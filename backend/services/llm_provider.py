from __future__ import annotations

import logging
import time
from typing import Any, Dict, AsyncGenerator

import google.generativeai as genai

from backend.config import get_settings

logger = logging.getLogger("backend.services.llm_provider")


class LLMProviderError(RuntimeError):
    """Raised when the LLM provider fails in a controlled way."""


class GeminiLLMProvider:
    """
    Google Gemini LLM provider wrapper using google-generativeai SDK.
    
    Works with free tier API keys.
    Supports both streaming and non-streaming generation.
    """

    def __init__(self) -> None:
        settings = get_settings()

        api_key = settings.gemini_api_key
        model_name = settings.gemini_model_name

        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Cannot initialize Gemini provider."
            )

        try:
            # Configure API key
            genai.configure(api_key=api_key)
            
            # Initialize model
            self._model = genai.GenerativeModel(model_name)
            self._model_name = model_name

            logger.info(
                "Gemini provider initialized successfully",
                extra={"model": model_name},
            )

        except Exception:
            logger.exception("Failed to initialize Gemini provider")
            raise

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """
        Generate response from Gemini (non-streaming).

        Returns provider-neutral dict:
        {
            text,
            latency_ms,
            provider,
            model
        }
        """
        start = time.perf_counter()

        try:
            logger.info(
                "Gemini generation started",
                extra={
                    "prompt_length": len(prompt),
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
            )

            # Generate content
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
            )

            latency_ms = int((time.perf_counter() - start) * 1000)

            # Extract text from response
            text = response.text if response and hasattr(response, 'text') else ""

            logger.info(
                "Gemini generation completed",
                extra={
                    "latency_ms": latency_ms,
                    "output_length": len(text),
                },
            )

            return {
                "text": text,
                "latency_ms": latency_ms,
                "provider": "gemini",
                "model": self._model_name,
            }

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.exception(
                "Gemini API error",
                extra={"latency_ms": latency_ms, "error": str(e)},
            )
            raise LLMProviderError(f"Gemini API error: {str(e)}") from e

    async def generate_stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """
        Generate response from Gemini with streaming.

        Yields chunks of text as they are generated.
        """
        try:
            logger.info(
                "Gemini streaming generation started",
                extra={
                    "prompt_length": len(prompt),
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
            )

            # Generate content with streaming
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
                stream=True,
            )

            # Yield chunks as they arrive
            for chunk in response:
                if chunk.text:
                    yield chunk.text

            logger.info("Gemini streaming generation completed")

        except Exception as e:
            logger.exception(
                "Gemini streaming API error",
                extra={"error": str(e)},
            )
            raise LLMProviderError(f"Gemini streaming API error: {str(e)}") from e
