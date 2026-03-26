from __future__ import annotations

import json
import logging
import time

from groq import Groq

from config import CHUNK_SIZE, GROQ_API_KEY, MAX_RETRIES, MAX_TOKENS, MODEL
from core.api import extract_json, merge_chunk_results, paper_chunk_prompts
from interfaces.llm import LLMInterface

logger = logging.getLogger(__name__)


class GroqLLM(LLMInterface):
    def __init__(
        self,
        api_key: str | None = GROQ_API_KEY,
        model: str = MODEL,
        max_tokens: int = MAX_TOKENS,
        max_retries: int = MAX_RETRIES,
        chunk_size: int = CHUNK_SIZE,
    ) -> None:
        self._client = Groq(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens
        self._max_retries = max_retries
        self._chunk_size = chunk_size

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        allow_chunking: bool = False,
    ) -> dict:
        prompts = paper_chunk_prompts(user_prompt, self._chunk_size) if allow_chunking else [user_prompt]
        results = [self._run_prompt(system_prompt, prompt) for prompt in prompts]
        return merge_chunk_results(results) if allow_chunking else results[0]

    def _run_prompt(self, system_prompt: str, user_prompt: str) -> dict:
        result = None
        last_error = None

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info("Prompt attempt %s", attempt)
                raw = self._call(system_prompt, user_prompt)
                logger.debug("Raw output:\n%s", raw[:500])
                result = extract_json(raw)
                break
            except (ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                logger.warning("Attempt %s failed: %s", attempt, exc)
                if attempt < self._max_retries:
                    time.sleep(2**attempt)
            except Exception:
                raise

        if result is None:
            raise ValueError(f"All {self._max_retries} attempts failed. Last error: {last_error}")

        return result

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()
