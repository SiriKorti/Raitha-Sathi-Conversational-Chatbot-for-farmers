"""
voice.py — FastAPI Routes for Voice Interactions

Provides HTTP endpoints for converting Speech-to-Text (STT) 
and Text-to-Speech (TTS).
"""

import os
import tempfile
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from app.utils.speech import transcribe_speech, sanitize_for_speech
from app.utils.logger import logger

# We only import edge-tts and gTTS locally when needed
try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import edge_tts
except ImportError:
    edge_tts = None
    logger.warning("edge-tts is not installed. Falling back to gTTS.")

router = APIRouter()

class SynthesizeRequest(BaseModel):
    text: str

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error(f"Failed to remove temp file {path}: {e}")

@router.post("/transcribe")
async def api_transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Endpoint to transcribe an uploaded audio file using Gemini with language support.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Create a temporary file to save the uploaded audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_path = temp_audio.name
        content = await file.read()
        temp_audio.write(content)
        
    try:
        # Transcribe using Gemini with explicit language enforcement
        transcription = await transcribe_speech(temp_path, language=language)
        return {"text": transcription}
    except Exception as e:
        logger.error(f"Transcription API failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        remove_file(temp_path)

@router.post("/synthesize")
async def api_synthesize(request: SynthesizeRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to synthesize text into speech and return an MP3 file using SapnaNeural.
    """
    import re
    if not gTTS and not edge_tts:
        raise HTTPException(status_code=500, detail="No TTS engines installed on the server.")
        
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
        
    # Remove source references and URLs if present
    text = re.sub(r'(?i)\*\*📚\s*Source:.*', '', text)
    text = re.sub(r'(?i)📚\s*Source:.*', '', text)
    text = re.sub(r'(?i)ಮೂಲ:.*', '', text)
    
    cleaned_text = sanitize_for_speech(text)
    
    if not cleaned_text:
         raise HTTPException(status_code=400, detail="Text resulted in empty string after sanitization")

    # Ensure full complete speech delivery for the farmer without premature cutoff.
    # Set a generous safety cap (5000 characters) to prevent abuse while allowing full detailed answers.
    if len(cleaned_text) > 5000:
        truncated = cleaned_text[:5000]
        last_punct = max(truncated.rfind('.'), truncated.rfind('?'), truncated.rfind('!'), truncated.rfind('।'))
        if last_punct > 2000:
            cleaned_text = truncated[:last_punct + 1]
        else:
            cleaned_text = truncated

    # Auto-detect language mostly based on Kannada characters
    kannada_chars = sum(1 for c in cleaned_text if 0x0C80 <= ord(c) <= 0x0CFF)
    lang = "kn" if kannada_chars > 3 else "en"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_path = temp_audio.name
        
    try:
        if edge_tts is not None:
            if lang == "en":
                voice = "en-IN-NeerjaNeural"
                communicate = edge_tts.Communicate(cleaned_text, voice, rate="+10%", pitch="+0Hz")
            else:
                voice = "kn-IN-SapnaNeural"
                communicate = edge_tts.Communicate(cleaned_text, voice, rate="+5%", pitch="-2Hz")
                
            await communicate.save(temp_path)
        else:
            # Fallback to gTTS
            loop = asyncio.get_event_loop()
            def _generate():
                tts = gTTS(text=cleaned_text, lang=lang)
                tts.save(temp_path)
            await loop.run_in_executor(None, _generate)
        
        # We need to return the file, and then delete it afterwards
        background_tasks.add_task(remove_file, temp_path)
        return FileResponse(temp_path, media_type="audio/mpeg", filename="response.mp3")
        
    except Exception as e:
        logger.error(f"Synthesis API failed: {e}")
        remove_file(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

