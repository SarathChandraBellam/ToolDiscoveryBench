"""Multi-step workflow: one user request that needs 2-3 DIFFERENT tools in sequence.

The tasks are hand-written for this harness over the 31 real catalog tools (no test-split
question is used; none of them is a dataset question at all). Each request spells out the
order, and ``gold`` is that tool sequence. Unlike the single-turn gold labels they were NOT
produced by running Claude Code / Codex, so treat them as author-labelled.
"""

from __future__ import annotations

from typing import Any

_SVELTE_SNIPPET = "<script>let count = 0; $: doubled = count * 2</script><button on:click={() => count++}>{doubled}</button>"

_TASKS: list[tuple[str, list[str]]] = [
    (
        "Using Context7: first resolve the library id for Zod, then query its docs for how to "
        "write a discriminated union schema.",
        ["context7.resolve-library-id", "context7.query-docs"],
    ),
    (
        "First list the available Svelte documentation sections, then retrieve the full "
        "documentation for the section on the $derived rune.",
        ["svelte.list-sections", "svelte.get-documentation"],
    ),
    (
        f"Run the Svelte autofixer on this component, then generate a playground link for it: "
        f"{_SVELTE_SNIPPET}",
        ["svelte.svelte-autofixer", "svelte.playground-link"],
    ),
    (
        "For the GitHub repo vercel/next.js: first get the list of wiki documentation topics, "
        "then view the wiki documentation contents for the repo.",
        ["deepwiki.read_wiki_structure", "deepwiki.read_wiki_contents"],
    ),
    (
        "Search the AWS documentation for the skill that covers deploying an agent to Bedrock "
        "AgentCore, then retrieve that AWS skill's SKILL.md.",
        ["aws-knowledge.aws___search_documentation", "aws-knowledge.aws___retrieve_skill"],
    ),
    (
        "First list all AWS regions, then check whether Amazon Bedrock is available in "
        "eu-west-1, eu-central-1 and eu-north-1.",
        ["aws-knowledge.aws___list_regions", "aws-knowledge.aws___get_regional_availability"],
    ),
    (
        "Search the AWS docs for S3 lifecycle configuration rules, then fetch the full "
        "documentation page of the top result as markdown.",
        ["aws-knowledge.aws___search_documentation", "aws-knowledge.aws___read_documentation"],
    ),
    (
        "Search Microsoft Learn for Durable Functions orchestrations, then fetch the complete "
        "page of the best matching article.",
        ["microsoft-learn.microsoft_docs_search", "microsoft-learn.microsoft_docs_fetch"],
    ),
    (
        "First search the Microsoft docs for an overview of the Azure Blob Storage client "
        "library for Python, then search for an official code sample that uploads a blob.",
        ["microsoft-learn.microsoft_docs_search", "microsoft-learn.microsoft_code_sample_search"],
    ),
    (
        "Search the Hugging Face Hub for the most downloaded sentence-embedding models, then "
        "get the repo details of the top result.",
        ["huggingface.hub_repo_search", "huggingface.hub_repo_details"],
    ),
    (
        "Check which Hugging Face account I am logged in as, then search the Hub for datasets "
        "about code review.",
        ["huggingface.hf_whoami", "huggingface.hub_repo_search"],
    ),
    (
        "I only know the library name 'fastapi'. First map it to its GitHub owner/repo, then "
        "semantically search that repository's documentation for dependency injection.",
        ["gitmcp.match_common_libs_owner_repo_mapping", "gitmcp.search_generic_documentation"],
    ),
    (
        "For the library 'pydantic': first match the name to its GitHub owner/repo, then fetch "
        "the repository's documentation, then search its code for where model_validate is "
        "defined.",
        [
            "gitmcp.match_common_libs_owner_repo_mapping",
            "gitmcp.fetch_generic_documentation",
            "gitmcp.search_generic_code",
        ],
    ),
    (
        "I'm moving a Cloudflare Pages project to Workers. Read the Pages-to-Workers migration "
        "guide first, then search the Cloudflare documentation for how to bind a KV namespace "
        "in wrangler.",
        [
            "cloudflare-docs.migrate_pages_to_workers_guide",
            "cloudflare-docs.search_cloudflare_documentation",
        ],
    ),
    (
        "Search flights from Vienna to Lisbon on 2026-11-14 for one adult, then send feedback "
        "to the flight search tool's developers that results should show baggage fees.",
        ["kiwi.search-flight", "kiwi.feedback-to-devs"],
    ),
    (
        "Search the official Astro docs for how content collections are defined, then search "
        "the code of the GitHub repo withastro/astro for the defineCollection implementation.",
        ["astro-docs.search_astro_docs", "gitmcp.search_generic_code"],
    ),
    (
        "Ask the repository wiki Q&A how request routing works in fastapi/fastapi, then search "
        "that repository's code for the APIRouter class.",
        ["deepwiki.ask_wiki_question", "gitmcp.search_generic_code"],
    ),
    (
        "First list all AWS regions, then check Amazon Bedrock AgentCore availability in "
        "us-east-1 and us-west-2, then search the AWS documentation for its service quotas.",
        [
            "aws-knowledge.aws___list_regions",
            "aws-knowledge.aws___get_regional_availability",
            "aws-knowledge.aws___search_documentation",
        ],
    ),
]


def multistep_tasks() -> list[dict[str, Any]]:
    """The multi-step tasks as question rows: ``gold`` is the ordered tool sequence."""
    return [
        {"qid": f"ms-{i:02d}", "question": text, "gold": list(gold), "no_tool": False}
        for i, (text, gold) in enumerate(_TASKS, 1)
    ]
