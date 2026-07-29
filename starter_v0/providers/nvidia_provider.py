from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class NvidiaProvider(OpenAIProvider):
    """NVIDIA uses an OpenAI-compatible Chat Completions surface."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="NVIDIA_API_KEY",
            base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            default_model="meta/llama-3.1-8b-instruct",
        )
