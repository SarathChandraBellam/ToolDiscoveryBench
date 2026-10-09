"""``tdb``: ToolDiscoveryBench command line.

tdb pull      [--servers configs/servers.yaml] [--out data/catalog/public.json] [--only a,b]
tdb validate  [--config configs/bench.yaml]
tdb run       [--config configs/bench.yaml] [--routers a,b] [--limit N] [--out runs/x]
tdb report    RUN_DIR
tdb ask       "question" [--router NAME] [--size N|all]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Callable, Sequence

from tooldiscoverybench.core.config import load_dotenv, load_yaml


def _split(value: str | None) -> list[str] | None:
    return value.split(",") if value else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tdb", description="ToolDiscoveryBench")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pull = sub.add_parser("pull", help="snapshot tools/list from MCP servers")
    pull.add_argument("--servers", default="configs/servers.yaml")
    pull.add_argument("--out", default="data/catalog/public.json")
    pull.add_argument("--only", default=None, help="comma-separated server names")

    validate = sub.add_parser("validate", help="check golden labels exist in the catalog")
    validate.add_argument("--config", default="configs/bench.yaml")

    run = sub.add_parser("run", help="run the benchmark")
    run.add_argument("--config", default="configs/bench.yaml")
    run.add_argument("--routers", default=None, help="comma-separated router names")
    run.add_argument("--suites", default=None, help="comma-separated suite names")
    run.add_argument("--limit", type=int, default=None, help="first N questions per suite")
    run.add_argument("--out", default=None)

    report = sub.add_parser("report", help="re-render report.md for a run directory")
    report.add_argument("run_dir")
    report.add_argument(
        "--exclude-generators",
        default=None,
        help="comma-separated question authors to drop in the contamination table "
        "(default: the judges gpt-5.6-sol, claude-opus-5-5 and gpt-5.6-luna; '' for none)",
    )

    ask = sub.add_parser("ask", help="route one question and print the ranking")
    ask.add_argument("question")
    ask.add_argument("--router", default="bm25")
    ask.add_argument("--config", default="configs/bench.yaml")
    ask.add_argument("--size", default="all")
    return parser


def cmd_pull(args: argparse.Namespace) -> None:
    from tooldiscoverybench.catalog import pull_catalog, save_catalog

    catalog = pull_catalog(load_yaml(args.servers), only=_split(args.only))
    save_catalog(catalog, args.out)
    n_tools = sum(len(s["tools"]) for s in catalog["servers"].values())
    print(f"saved {n_tools} tools from {len(catalog['servers'])} servers -> {args.out}")


def cmd_validate(args: argparse.Namespace) -> None:
    from tooldiscoverybench.catalog import load_catalog
    from tooldiscoverybench.evaluation.runner import catalog_paths, suite_specs
    from tooldiscoverybench.golden import load_golden, validate_golden

    cfg = load_yaml(args.config)
    tools, _ = load_catalog(*catalog_paths(cfg))
    real_ids = {t.id for t in tools if not t.synthetic}
    failed = False
    for spec in suite_specs(cfg):
        items = load_golden(spec["golden"])
        used = {g for it in items for g in it.gold}
        no_tool = sum(it.expects_abstain for it in items)
        fixed = sum(it.candidates is not None for it in items)
        print(
            f"[{spec['name']}] {len(items)} questions ({no_tool} no-tool, {fixed} fixed-catalog); "
            f"gold covers {len(used & real_ids)}/{len(real_ids)} real tools"
        )
        uncovered = sorted(real_ids - used)
        if uncovered:
            print("  real tools with no question:", ", ".join(uncovered))
        problems = validate_golden(items, tools)
        if problems:
            failed = True
            print("  PROBLEMS:\n    " + "\n    ".join(problems[:30]))
    if failed:
        sys.exit(1)
    print("OK")


def cmd_run(args: argparse.Namespace) -> None:
    from tooldiscoverybench.evaluation.runner import run_bench

    out = asyncio.run(
        run_bench(
            load_yaml(args.config),
            args.out,
            only_routers=_split(args.routers),
            limit=args.limit,
            only_suites=_split(args.suites),
        )
    )
    print(f"\nreport: {out / 'report.md'}")


def cmd_report(args: argparse.Namespace) -> None:
    from tooldiscoverybench.evaluation.report import DEFAULT_EXCLUDE_GENERATORS, write_report

    exclude = (
        DEFAULT_EXCLUDE_GENERATORS
        if args.exclude_generators is None
        else tuple(g.strip() for g in args.exclude_generators.split(",") if g.strip())
    )
    print(write_report(args.run_dir, exclude))


async def _ask(args: argparse.Namespace) -> None:
    from tooldiscoverybench.catalog import CatalogSize, load_catalog, sample_catalog
    from tooldiscoverybench.core.models import GoldenItem
    from tooldiscoverybench.evaluation.runner import catalog_paths
    from tooldiscoverybench.routers import build_router

    cfg = load_yaml(args.config)
    tools, server_desc = load_catalog(*catalog_paths(cfg))
    router_cfg = next((r for r in cfg["routers"] if r["name"] == args.router), None)
    if router_cfg is None:
        sys.exit(f"no router named {args.router!r} in {args.config}")
    router = build_router(
        {
            k: v
            for k, v in router_cfg.items()
            if k not in ("concurrency", "usd_per_m_input", "abstain_threshold")
        }
    )
    reason = router.unavailable_reason()
    if reason:
        sys.exit(f"{router.name} unavailable: {reason}")
    await router.setup(tools, server_desc)
    size: CatalogSize = args.size if args.size == "all" else int(args.size)
    catalog = sample_catalog(tools, GoldenItem("ask", args.question, []), size)
    res = await router.route(args.question, catalog, server_desc)
    await router.aclose()
    print(
        json.dumps(
            {
                "router": router.name,
                "latency_ms": round(res.latency_ms, 1),
                "calls": res.calls,
                "input_tokens": res.input_tokens,
                "error": res.error,
                "abstained": res.abstained,
                "top5": [(tid, round(p, 4)) for tid, p in res.ranked[:5]],
            },
            indent=2,
        )
    )


def cmd_ask(args: argparse.Namespace) -> None:
    asyncio.run(_ask(args))


def main(argv: Sequence[str] | None = None) -> None:
    load_dotenv()
    args = build_parser().parse_args(argv)
    commands: dict[str, Callable[[argparse.Namespace], None]] = {
        "pull": cmd_pull,
        "validate": cmd_validate,
        "run": cmd_run,
        "report": cmd_report,
        "ask": cmd_ask,
    }
    commands[args.cmd](args)


if __name__ == "__main__":
    main()
