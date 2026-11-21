import asyncio
import re

import openai

from app.config import Settings

SYSTEM_INSTRUCTIONS = """You are Kaayal (കായൽ), a friendly voice assistant answering phone callers in Kerala.
Reply in the same language the caller used (Malayalam or English).
Keep replies under 60 words: plain speakable text, no markdown, no lists, no emojis.
Never invent prices, operators, availability, bookings, payments or confirmations.
If the caller asks for something unsupported (booking, payment, callback), politely say it is not available yet.
If the question is unclear, ask one short clarifying question."""


class OpenAIAdapterError(Exception):
    """Upstream OpenAI call failed or produced no usable text."""


def _sanitize_reply(text: str, max_chars: int) -> str:
    # Collapse whitespace/newlines so Sarvam TTS gets clean speakable text.
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def make_responder(settings: Settings):
    client: openai.AsyncOpenAI | None = None

    def get_client() -> openai.AsyncOpenAI:
        nonlocal client
        if client is None:
            if not settings.openai_api_key:
                raise OpenAIAdapterError("openai api key not configured")
            client = openai.AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=settings.openai_timeout_seconds,
                max_retries=0,
            )
        return client

    async def respond(utterance: str, language: str | None) -> str:
        instructions = SYSTEM_INSTRUCTIONS
        if language:
            instructions += f"\nThe caller's language hint is: {language}."

        try:
            response = await get_client().responses.create(
                model=settings.openai_model,
                instructions=instructions,
                input=utterance,
                max_output_tokens=settings.openai_max_output_tokens,
                store=False,
            )
        except (openai.APITimeoutError, asyncio.TimeoutError) as exc:
            raise OpenAIAdapterError("openai timeout") from exc
        except openai.APIError as exc:
            raise OpenAIAdapterError(f"openai api error: {type(exc).__name__}") from exc

        text = _sanitize_reply(getattr(response, "output_text", "") or "", settings.reply_max_chars)
        if not text:
            raise OpenAIAdapterError("openai returned empty output")
        return text

    return respond
