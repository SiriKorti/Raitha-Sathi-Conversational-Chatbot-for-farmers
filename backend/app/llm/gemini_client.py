"""
gemini_client.py — Google Gemini API Fallback Client

WHAT IT DOES:
Provides access to Google's Gemini models via their official cloud API.
It is used as a high-accuracy fallback when local Ollama is unavailable.

WHY IT EXISTS:
Ensures the assistant stays functional even if the local Ollama server
is down or the user's hardware is too slow for a large model.

CONNECTIONS:
- Used as a fallback by 'response_generator.py'.
- Requires GEMINI_API_KEY to be set in .env.

UPDATED: Now uses the new google.genai SDK (google-generativeai is deprecated).

ANTI-HALLUCINATION SETTINGS:
- temperature: 0.3 (low for factual responses)
- max_output_tokens: 600
- top_p: 0.85
"""

import asyncio
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import (
    LLMConnectionError, LLMResponseError, ConfigurationError
)


class GeminiClient:
    """
    Google Gemini API client using the new google.genai SDK.

    Used as a fallback when the local Ollama model is unavailable.
    Requires GEMINI_API_KEY to be set in .env.
    """

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ConfigurationError(
                "GEMINI_API_KEY is not set in .env. "
                "Get a free key at https://aistudio.google.com/app/apikey"
            )

        try:
            from google import genai
            from google.genai import types
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self._types = types
            self._model = settings.GEMINI_MODEL or "gemini-flash-lite-latest"
            self._candidate_models = ["gemini-flash-lite-latest"]
            logger.info(
                "Gemini client initialised | primary_model={m}",
                m=self._model
            )
        except ImportError:
            raise ConfigurationError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )

    def _make_config(self, max_tokens: int = 2048):
        """Build a GenerateContentConfig object for comprehensive agricultural advice."""
        return self._types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=max_tokens,
            top_p=0.8,
        )

    async def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        """
        Generate a response using the Gemini API with automatic model failover and retries.
        """
        logger.debug("Sending prompt to Gemini | prompt_len={n}", n=len(prompt))
        loop = asyncio.get_running_loop()
        last_exception = None

        for model_name in self._candidate_models:
            for attempt in range(2):
                try:
                    response = await loop.run_in_executor(
                        None,
                        lambda m=model_name: self._client.models.generate_content(
                            model=m,
                            contents=prompt,
                            config=self._make_config(max_tokens=max_tokens),
                        )
                    )

                    if not response:
                        continue

                    if not response.candidates:
                        logger.warning("Gemini response was blocked by safety filters | model={m}", m=model_name)
                        return "ಕ್ಷಮಿಸಿ, ಈ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರ ನೀಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ."

                    text = ""
                    if response.candidates:
                        first_cand = response.candidates[0]
                        if hasattr(first_cand, "content") and first_cand.content and hasattr(first_cand.content, "parts"):
                            text = "".join(p.text for p in first_cand.content.parts if hasattr(p, "text") and p.text).strip()
                    if not text and hasattr(response, "text"):
                        try:
                            text = response.text.strip()
                        except Exception:
                            pass

                    if text:
                        logger.debug("Gemini response successful | model={m} | chars={n}", m=model_name, n=len(text))
                        return text
                except Exception as e:
                    last_exception = e
                    logger.warning("Gemini generate attempt failed | model={m} | attempt={a} | error={e}", m=model_name, a=attempt, e=e)
                    await asyncio.sleep(0.5)

        logger.error("All Gemini model attempts exhausted | last_error={e}", e=last_exception)
        raise LLMConnectionError(f"Gemini API call failed across all models: {last_exception}")

    async def generate_stream(self, prompt: str, max_tokens: int = 2048):
        """
        Stream response tokens from the Gemini API with automatic fallback.
        """
        logger.debug("Streaming from Gemini")
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        SENTINEL = object()

        def _run_stream():
            """Runs the Gemini stream with model fallback."""
            stream_succeeded = False
            for model_name in self._candidate_models:
                if stream_succeeded:
                    break
                try:
                    for chunk in self._client.models.generate_content_stream(
                        model=model_name,
                        contents=prompt,
                        config=self._make_config(max_tokens=max_tokens),
                    ):
                        chunk_text = ""
                        try:
                            chunk_text = chunk.text or ""
                        except Exception:
                            pass
                        
                        if not chunk_text and hasattr(chunk, 'candidates') and chunk.candidates:
                            for cand in chunk.candidates:
                                if hasattr(cand, 'content') and cand.content and hasattr(cand.content, 'parts'):
                                    for p in cand.content.parts:
                                        if hasattr(p, 'text') and p.text:
                                            chunk_text += p.text

                        if chunk_text:
                            stream_succeeded = True
                            loop.call_soon_threadsafe(queue.put_nowait, chunk_text)
                    if stream_succeeded:
                        break
                except Exception as e:
                    logger.warning("Gemini stream failed for model={m} | err={e}", m=model_name, e=e)
                    continue

            loop.call_soon_threadsafe(queue.put_nowait, SENTINEL)

        loop.run_in_executor(None, _run_stream)

        while True:
            item = await queue.get()
            if item is SENTINEL:
                break
            yield item

    async def is_available(self) -> bool:
        """Check if Gemini API is accessible with a lightweight test call."""
        try:
            loop = asyncio.get_running_loop()
            for model_name in self._candidate_models:
                try:
                    await loop.run_in_executor(
                        None,
                        lambda m=model_name: self._client.models.generate_content(
                            model=m,
                            contents="Reply with just 'ok'",
                            config=self._types.GenerateContentConfig(max_output_tokens=5),
                        )
                    )
                    return True
                except Exception:
                    continue
            return False
        except Exception:
            return False
