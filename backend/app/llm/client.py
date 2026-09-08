"""
LLM client — hỗ trợ Gemini (Google AI Studio) và Anthropic. docx/06 §4–§5.

Chọn nhà cung cấp qua settings.llm_provider ("gemini" | "anthropic").
Chế độ offline (settings.llm_offline hoặc thiếu API key) → trả câu tĩnh,
để test pipeline / safety mà không tốn token.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

from app.config import settings

logger = logging.getLogger(__name__)

try:  # Gemini
    from google import genai
    from google.genai import types as genai_types
except Exception:  # pragma: no cover
    genai = None  # type: ignore
    genai_types = None  # type: ignore

try:  # Anthropic (tuỳ chọn)
    from anthropic import AsyncAnthropic
except Exception:  # pragma: no cover
    AsyncAnthropic = None  # type: ignore

_OFFLINE_SENTENCE = "Mình đang nghe bạn. Bạn kể thêm cho mình được không?"


def _backoff(attempt: int, exc: Exception) -> float:
    """Backoff luỹ thừa. 429/503 (rate limit / quá tải) chờ lâu hơn."""
    msg = str(exc)
    rate_limited = "429" in msg or "RESOURCE_EXHAUSTED" in msg or "503" in msg or "UNAVAILABLE" in msg
    base = 4.0 if rate_limited else 0.8
    return min(base * (2**attempt), 20.0)


class LLMClient:
    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self._sdk_ok = genai is not None if self.provider == "gemini" else AsyncAnthropic is not None
        self.offline = settings.llm_offline or not settings.has_api_key or not self._sdk_ok

        self._gemini = None
        self._anthropic = None
        if self.offline:
            return
        if self.provider == "gemini":
            self._gemini = genai.Client(api_key=settings.gemini_api_key)
        else:
            self._anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)

    # ------------------------------------------------------------------
    async def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool = False,
        retries: int = 2,
    ) -> str:
        if self.offline:
            return _OFFLINE_SENTENCE
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                if self.provider == "gemini":
                    return await self._gemini_complete(system, user, max_tokens, temperature, json_mode)
                return await self._anthropic_complete(system, user, max_tokens, temperature)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning("LLM complete lỗi (thử %d): %s", attempt + 1, exc)
                if attempt < retries:
                    await asyncio.sleep(_backoff(attempt, exc))
        raise RuntimeError(f"LLM complete thất bại: {last_exc}")

    async def stream(
        self, *, system: str, user: str, max_tokens: int, temperature: float, retries: int = 2
    ) -> AsyncIterator[str]:
        if self.offline:
            for chunk in _OFFLINE_SENTENCE.split(" "):
                yield chunk + " "
                await asyncio.sleep(0)
            return

        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                gen = (
                    self._gemini_stream(system, user, max_tokens, temperature)
                    if self.provider == "gemini"
                    else self._anthropic_stream(system, user, max_tokens, temperature)
                )
                async for piece in gen:
                    yield piece
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning("LLM stream lỗi (thử %d): %s", attempt + 1, exc)
                if attempt < retries:
                    await asyncio.sleep(_backoff(attempt, exc))
        raise RuntimeError(f"LLM stream thất bại: {last_exc}")

    # ---- Gemini ------------------------------------------------------
    @staticmethod
    def _gemini_text(resp) -> str:
        txt = getattr(resp, "text", None)
        if txt:
            return txt
        parts_text: list[str] = []
        for cand in getattr(resp, "candidates", None) or []:
            content = getattr(cand, "content", None)
            for part in getattr(content, "parts", None) or []:
                if getattr(part, "thought", False):
                    continue
                if getattr(part, "text", None):
                    parts_text.append(part.text)
        return "".join(parts_text)

    def _gemini_config(self, system: str, max_tokens: int, temperature: float, json_mode: bool):
        kwargs = dict(
            system_instruction=system,
            temperature=temperature,
            # chừa chỗ cho "thinking" — post-check tự cắt còn ≤ 5 câu
            max_output_tokens=max(max_tokens, 2048),
            automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(disable=True),
        )
        # 2.x cho phép tắt thinking → nhanh hơn. 3.x thì 400 nếu ép budget=0 nên bỏ qua.
        if settings.gemini_model.startswith(("gemini-2.", "gemini-1.")):
            kwargs["thinking_config"] = genai_types.ThinkingConfig(thinking_budget=0)
        if json_mode:
            kwargs["response_mime_type"] = "application/json"
        return genai_types.GenerateContentConfig(**kwargs)

    async def _gemini_complete(self, system, user, max_tokens, temperature, json_mode) -> str:
        resp = await self._gemini.aio.models.generate_content(
            model=settings.gemini_model,
            contents=user,
            config=self._gemini_config(system, max_tokens, temperature, json_mode),
        )
        return self._gemini_text(resp).strip()

    async def _gemini_stream(self, system, user, max_tokens, temperature) -> AsyncIterator[str]:
        stream = await self._gemini.aio.models.generate_content_stream(
            model=settings.gemini_model,
            contents=user,
            config=self._gemini_config(system, max_tokens, temperature, json_mode=False),
        )
        async for chunk in stream:
            for cand in getattr(chunk, "candidates", None) or []:
                for part in getattr(getattr(cand, "content", None), "parts", None) or []:
                    if getattr(part, "thought", False):
                        continue
                    if getattr(part, "text", None):
                        yield part.text

    # ---- Anthropic -------------------------------------------------
    async def _anthropic_complete(self, system, user, max_tokens, temperature) -> str:
        resp = await self._anthropic.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            b.text for b in resp.content if getattr(b, "type", "") == "text"
        ).strip()

    async def _anthropic_stream(self, system, user, max_tokens, temperature) -> AsyncIterator[str]:
        async with self._anthropic.messages.stream(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as s:
            async for text in s.text_stream:
                yield text


_client: LLMClient | None = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
