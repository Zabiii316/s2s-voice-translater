from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.services.translation_service import TranslationService
from app.services.pii_service import PIIService
from gtts import gTTS
from io import BytesIO

app = FastAPI(title="S2S Voice Translator Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

translator = TranslationService()
pii_service = PIIService()


@app.get("/")
def home():
    return {
        "message": "S2S Voice Translator Backend is running"
    }


@app.post("/translate")
def translate(payload: dict):
    try:
        text = payload.get("text", "")
        source_language = payload.get("source_language", "English")
        target_language = payload.get("target_language", "Urdu")
        arabic_dialect = payload.get("arabic_dialect", "MSA")

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        pii_result = pii_service.mask_text(text)

        translated_text = translator.translate(
            text=pii_result["masked_text"],
            source_language=source_language,
            target_language=target_language,
            arabic_dialect=arabic_dialect
        )

        return {
            "original_text": text,
            "masked_text": pii_result["masked_text"],
            "pii_found": pii_result["pii_found"],
            "detected_pii": pii_result["detected_pii"],
            "source_language": source_language,
            "target_language": target_language,
            "arabic_dialect": arabic_dialect,
            "translated_text": translated_text
        }

    except HTTPException:
        raise

    except Exception as e:
        print("TRANSLATION ERROR:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


@app.post("/tts")
def text_to_speech(payload: dict):
    try:
        text = payload.get("text", "")
        language = payload.get("language", "Urdu")

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        language_map = {
            "English": "en",
            "Urdu": "ur",
            "Arabic": "ar"
        }

        lang_code = language_map.get(language, "en")

        print("TTS REQUEST TEXT:", text)
        print("TTS LANGUAGE:", language)
        print("TTS LANGUAGE CODE:", lang_code)

        audio_buffer = BytesIO()

        tts = gTTS(
            text=text,
            lang=lang_code,
            slow=False
        )

        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=tts.mp3"
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        print("TTS ERROR:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"TTS failed: {str(e)}"
        )