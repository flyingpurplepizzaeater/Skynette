"""
LM Studio Provider - Local LLM integration via OpenAI-compatible API.

Connects to LM Studio running locally on port 1234.
"""

from src.ai.gateway import AICapability
from src.ai.providers.openai import OpenAIProvider


class LMStudioProvider(OpenAIProvider):
    """
    LM Studio provider.

    Connects to local LM Studio instance via OpenAI-compatible API.
    Default URL: http://localhost:1234/v1
    """

    name = "lm_studio"
    display_name = "LM Studio (Local)"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.EMBEDDINGS,
        AICapability.CODE_GENERATION,
    }

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        api_key: str = "lm-studio",  # LM Studio doesn't strictly require a key
    ):
        super().__init__(api_key=api_key, base_url=base_url)
        self.model = "local-model"  # LM Studio usually uses the currently loaded model

    async def initialize(self) -> bool:
        """Initialize the LM Studio provider."""
        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            # Try to fetch models to verify availability
            await self.get_models()
            self._is_initialized = True
            self._is_available = True
            return True
        except Exception as e:
            print(f"Failed to initialize LM Studio provider: {e}")
            self._is_available = False
            return False

    async def get_models(self) -> list[dict]:
        """Get available models from LM Studio."""
        if not self._client:
            await self.initialize()
            if not self._client:
                return [
                    {"id": "local-model", "name": "Local Model (Not Connected)", "context": 32768}
                ]

        try:
            response = await self._client.models.list()
            models = []
            for model in response.data:
                models.append(
                    {
                        "id": model.id,
                        "name": model.id.split("/")[-1]
                        .replace("-", " ")
                        .title(),  # Clean up ID for display
                        "context": 32768,  # LM Studio doesn't always report context, assume high
                    }
                )
            return models
        except Exception as e:
            print(f"Failed to fetch models from LM Studio: {e}")
            return [{"id": "local-model", "name": "Currently Loaded Model", "context": 32768}]
