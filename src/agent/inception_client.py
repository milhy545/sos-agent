"""Inception Labs Mercury API client for SOS Agent."""

import logging
import os
from typing import Any, AsyncIterator, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class InceptionClient:
    """
    Inception Labs Mercury API client for system rescue operations.

    Uses Inception Labs API with your subscription.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "mercury-coder", language: str = "en"):
        """
        Initialize Inception Labs client.

        Args:
            api_key: Inception API key (or from INCEPTION_API_KEY env var)
            model: Model name (default: mercury-coder)
            language: Response language ("en" or "cs")
        """
        self.api_key = api_key or os.getenv("INCEPTION_API_KEY")
        if not self.api_key:
            raise ValueError("INCEPTION_API_KEY not found in environment or constructor")

        self.model_name = model
        self.api_url = "https://api.inceptionlabs.ai/v1/chat/completions"
        self.logger = logging.getLogger(__name__)
        self.language = language

        self.logger.info(f"Inception Labs client initialized: {self.model_name}")

    async def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Query Inception Labs with a prompt.

        Args:
            prompt: Prompt text
            context: Additional context (ignored for now)
            stream: Whether to stream response

        Yields:
            Response chunks
        """
        self.logger.info(f"Querying Inception Labs: {prompt[:100]}...")

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are a helpful system administrator assistant. Provide clear, actionable advice for system diagnostics and rescue operations. Use plain text formatting without ASCII tables or excessive line breaks. Write in flowing paragraphs that terminals can wrap naturally. Avoid pre-formatted text blocks wider than 80 chars. {'Respond in Czech language (Čeština).' if self.language == 'cs' else 'Respond in English.'}",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 4096,
                    "stream": stream,
                }

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                }

                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    response.raise_for_status()

                    if stream:
                        # Stream response
                        async for line in response.content:
                            line_text = line.decode("utf-8").strip()
                            if line_text.startswith("data: "):
                                data_text = line_text[6:]  # Remove "data: " prefix
                                if data_text == "[DONE]":
                                    break
                                try:
                                    import json

                                    data = json.loads(data_text)
                                    if "choices" in data and data["choices"]:
                                        delta = data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
                    else:
                        # Non-streaming response
                        data = await response.json()
                        if "choices" in data and data["choices"]:
                            content = data["choices"][0]["message"]["content"]
                            yield content

        except Exception as e:
            self.logger.error(f"Inception Labs API error: {e}", exc_info=True)
            yield f"❌ Inception Labs API Error: {str(e)}\n\nℹ️  Check INCEPTION_API_KEY environment variable"
