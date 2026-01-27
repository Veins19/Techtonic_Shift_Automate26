from __future__ import annotations

import logging
import time
from typing import Any, Dict

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

from backend.config import get_settings

logger = logging.getLogger("backend.services.llm_provider")


class LLMProviderError(RuntimeError):
    """Raised when the LLM provider fails in a controlled way."""


class GeminiLLMProvider:
    """
    Google Gemini LLM provider wrapper.

    Design goals:
    - Runtime correctness
    - Clean logging & latency measurement
    - Provider-agnostic response shape
    - Zero Pylance false positives
    """

    def __init__(self) -> None:
        settings = get_settings()

        # ✅ Correct key from config.py
        api_key = settings.gemini_api_key
        model_name = settings.gemini_model_name

        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Cannot initialize Gemini provider."
            )

        try:
            # Gemini SDK has incomplete type stubs → use getattr safely
            configure_fn = getattr(genai, "configure", None)
            model_cls = getattr(genai, "GenerativeModel", None)

            if not configure_fn or not model_cls:
                raise RuntimeError(
                    "Gemini SDK is missing required attributes. "
                    "Check google-generativeai installation."
                )

            # Configure API key
            configure_fn(api_key=api_key)

            # Initialize model
            self._model = model_cls(model_name=model_name)

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
        Generate response from Gemini.

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

            response = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
            )

            latency_ms = int((time.perf_counter() - start) * 1000)
            text = response.text if response and response.text else ""

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
                "model": self._model.model_name,
            }

        except GoogleAPIError as e:
            latency_ms = int((time.perf_counter() - start) * 1000)

            logger.exception(
                "Gemini API error",
                extra={"latency_ms": latency_ms},
            )
            raise LLMProviderError("Gemini API error") from e

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)

            logger.exception(
                "Unexpected Gemini failure",
                extra={"latency_ms": latency_ms},
            )
            raise LLMProviderError("Unexpected Gemini failure") from e
