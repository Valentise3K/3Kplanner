"""Voice transcription via OpenAI Whisper API."""

import io
import os
import tempfile

from openai import AsyncOpenAI

from config import logger, settings

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def transcribe_voice(file_bytes: bytes, filename: str = "voice.ogg", lang: str = "ru") -> str | None:
    """
    Transcribe a voice message (ogg/mp3/wav) to text.
    Returns the transcription string or None on failure.
    """
    whisper_lang = "ru" if lang == "ru" else "en"
    try:
        audio_file = io.BytesIO(file_bytes)
        audio_file.name = filename

        transcript = await _client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=whisper_lang,
        )
        return transcript.text.strip()
    except Exception as e:
        logger.warning("Voice transcription failed: %s", e)
        return None
