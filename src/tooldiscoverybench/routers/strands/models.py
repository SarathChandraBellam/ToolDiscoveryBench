"""Build a Strands model for a provider, importing only the SDK that provider needs.

Providers: ``bedrock`` (default), ``anthropic``, ``openai``, ``huggingface``, ``litellm``.

``huggingface`` uses Hugging Face Inference Providers through its OpenAI-compatible router
(``https://router.huggingface.co/v1``) with an ``HF_TOKEN``, so any chat model served there
(Qwen, Llama, DeepSeek, gpt-oss, ...) can drive the Strands agent. Pin a specific inference
provider with a ``:provider`` suffix, e.g. ``Qwen/Qwen3-32B:cerebras``.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_MODEL_IDS = {
    "bedrock": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "anthropic": "claude-haiku-4-5",
    "openai": "gpt-4.1-mini",
    "huggingface": "Qwen/Qwen3-32B",
}

HF_ROUTER_URL = "https://router.huggingface.co/v1"


def build_model(cfg: dict[str, Any]) -> Any:
    provider = cfg.get("provider", "bedrock")
    model_id = str(cfg.get("model_id") or DEFAULT_MODEL_IDS.get(provider, ""))
    params: dict[str, Any] = {"max_tokens": int(cfg.get("max_tokens", 512))}
    if cfg.get("temperature") is not None:
        params["temperature"] = float(cfg["temperature"])

    if provider == "bedrock":
        from strands.models.bedrock import BedrockModel

        region = cfg.get("region") or os.environ.get("AWS_REGION", "us-east-1")
        return BedrockModel(model_id=model_id, region_name=region, **params)
    if provider == "anthropic":
        from strands.models.anthropic import AnthropicModel

        return AnthropicModel(
            client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY")},
            model_id=model_id,
            **params,
        )
    if provider == "openai":
        from strands.models.openai import OpenAIModel

        client_args: dict[str, Any] = {"api_key": os.environ.get("OPENAI_API_KEY")}
        if cfg.get("base_url"):
            client_args["base_url"] = cfg["base_url"]
        return OpenAIModel(client_args=client_args, model_id=model_id, params=params)
    if provider == "huggingface":
        from strands.models.openai import OpenAIModel

        hf_args = {
            "api_key": os.environ.get(cfg.get("api_key_env", "HF_TOKEN")),
            "base_url": cfg.get("base_url") or HF_ROUTER_URL,
        }
        return OpenAIModel(client_args=hf_args, model_id=model_id, params=params)
    if provider == "litellm":
        from strands.models.litellm import LiteLLMModel

        return LiteLLMModel(model_id=model_id, params=params)
    raise ValueError(f"unknown strands provider {provider!r}")


def provider_unavailable_reason(cfg: dict[str, Any]) -> str | None:
    """Cheap credential check so the runner can skip instead of failing every question."""
    provider = cfg.get("provider", "bedrock")
    if provider == "bedrock":
        try:
            import boto3
        except ImportError:
            return "boto3 not installed (uv sync --extra strands)"
        # off EC2 the instance-metadata probe can hang; cap it
        os.environ.setdefault("AWS_METADATA_SERVICE_TIMEOUT", "1")
        os.environ.setdefault("AWS_METADATA_SERVICE_NUM_ATTEMPTS", "1")
        if boto3.Session().get_credentials() is None:
            return "no AWS credentials for Bedrock"
        return None
    env_for = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "huggingface": cfg.get("api_key_env", "HF_TOKEN"),
    }
    key = env_for.get(provider)
    if key and not os.environ.get(key):
        return f"{key} not set"
    if provider in ("openai", "huggingface"):
        try:
            import openai  # noqa: F401
        except ImportError:
            return "openai SDK not installed (uv sync --extra huggingface)"
    return None
