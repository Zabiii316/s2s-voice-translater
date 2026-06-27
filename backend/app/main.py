from __future__ import annotations

import logging
import time
from io import BytesIO
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from gtts import gTTS
from pydantic import BaseModel, Field

load_dotenv()

from app.services.pii_service import PIIService
from app.services.translation_service import TranslationService


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger("s2s-backend")


app = FastAPI(
    title="S2S Voice Translator Backend",
    version="1.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],
    allow_headers=["*"],
)


translator = TranslationService()
pii_service = PIIService()


class TranslateRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=6000,
    )

    source_language: str = "English"
    target_language: str = "Urdu"
    arabic_dialect: str = "MSA"
    speaker_role: Optional[str] = "Auto"
    pathway: Optional[str] = "A"


class TTSRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=6000,
    )

    language: str = "English"


@app.get("/")
async def home() -> dict:
    return {
        "message": (
            "S2S Voice Translator Backend "
            "is running"
        ),
        "version": "1.1.0",
        "ai_translation_enabled": (
            translator.ai_enabled
        ),
    }


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "ai_translation_enabled": (
            translator.ai_enabled
        ),
    }


@app.post("/translate")
async def translate(
    payload: TranslateRequest,
) -> dict:

    started = time.perf_counter()

    try:
        original_text = payload.text.strip()

        pii_result = pii_service.mask_text(
            original_text
        )

        masked_text = pii_result.get(
            "masked_text",
            original_text,
        )

        result = await translator.translate_async(
            text=masked_text,
            source_language=payload.source_language,
            target_language=payload.target_language,
            arabic_dialect=payload.arabic_dialect,
        )

        elapsed_ms = round(
            (
                time.perf_counter()
                - started
            )
            * 1000
        )

        return {
            "original_text": original_text,
            "masked_text": masked_text,
            "pii_found": bool(
                pii_result.get(
                    "pii_found",
                    False,
                )
            ),
            "detected_pii": pii_result.get(
                "detected_pii",
                [],
            ),
            "source_language": (
                translator.normalize_language(
                    payload.source_language
                )
            ),
            "target_language": (
                translator.normalize_language(
                    payload.target_language
                )
            ),
            "arabic_dialect": (
                translator.normalize_dialect(
                    payload.arabic_dialect
                )
            ),
            "translated_text": (
                result.translated_text
            ),
            "provider": result.provider,
            "segments": result.segments,
            "translation_latency_ms": (
                elapsed_ms
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Translation endpoint failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Translation failed",
        ) from exc


def generate_tts_audio(
    text: str,
    language_code: str,
) -> BytesIO:

    buffer = BytesIO()

    gTTS(
        text=text,
        lang=language_code,
        slow=False,
    ).write_to_fp(buffer)

    buffer.seek(0)

    return buffer


@app.post("/tts")
async def text_to_speech(
    payload: TTSRequest,
) -> StreamingResponse:

    language_map = {
        "English": "en",
        "Urdu": "ur",
        "Arabic": "ar",
    }

    language = payload.language.strip().title()

    language_code = language_map.get(
        language
    )

    if not language_code:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported TTS language: "
                f"{payload.language}"
            ),
        )

    text = payload.text.strip()

    if "[Offline phrase not found" in text:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot speak an untranslated "
                "offline fallback message"
            ),
        )

    try:
        audio_buffer = await run_in_threadpool(
            generate_tts_audio,
            text,
            language_code,
        )

        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": (
                    "inline; "
                    "filename=translation.mp3"
                ),
                "Cache-Control": "no-store",
            },
        )

    except Exception as exc:
        logger.exception(
            "TTS generation failed"
        )

        raise HTTPException(
            status_code=500,
            detail="TTS generation failed",
        ) from exc