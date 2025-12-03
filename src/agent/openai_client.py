"""OpenAI API client for SOS Agent."""

import logging
import os
from typing import Any, AsyncIterator, Dict, Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    OpenAI API client for system rescue operations.

    Uses OpenAI API with your subscription.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env var)
            model: Model name (default: gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or constructor")

        self.model_name = model
        self.logger = logging.getLogger(__name__)

        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)

        self.logger.info(f"OpenAI client initialized: {self.model_name}")

    async def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Query OpenAI with a prompt.

        Args:
            prompt: Prompt text
            context: Additional context (ignored for now)
            stream: Whether to stream response

        Yields:
            Response chunks
        """
        self.logger.info(f"Querying OpenAI: {prompt[:100]}...")

        try:
            if stream:
                # Stream response
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful system administrator assistant. Provide clear, actionable advice for system diagnostics and rescue operations.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    stream=True,
                    temperature=0.7,
                    max_tokens=4096,
                )

                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                # Non-streaming response
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful system administrator assistant.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                )

                yield response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}", exc_info=True)
            yield f"❌ OpenAI API Error: {str(e)}\n\nℹ️  Check OPENAI_API_KEY environment variable"
