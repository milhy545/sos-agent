"""Gemini API client for SOS Agent."""

import logging
import os
from typing import Any, AsyncIterator, Dict, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Gemini API client for system rescue operations.

    Uses Google's Gemini API with your subscription.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key (or from GEMINI_API_KEY env var)
            model: Model name (default: gemini-2.0-flash-exp)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or constructor")

        self.model_name = model
        self.logger = logging.getLogger(__name__)

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            ),
        )

        self.logger.info(f"Gemini client initialized: {self.model_name}")

    async def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Query Gemini with a prompt.

        Args:
            prompt: Prompt text
            context: Additional context (ignored for now)
            stream: Whether to stream response

        Yields:
            Response chunks
        """
        self.logger.info(f"Querying Gemini: {prompt[:100]}...")

        try:
            if stream:
                # Stream response
                response = self.model.generate_content(prompt, stream=True)

                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            else:
                # Non-streaming response
                response = self.model.generate_content(prompt)
                yield response.text

        except Exception as e:
            self.logger.error(f"Gemini API error: {e}", exc_info=True)
            yield f"❌ Gemini API Error: {str(e)}\n\nℹ️  Check GEMINI_API_KEY environment variable"
