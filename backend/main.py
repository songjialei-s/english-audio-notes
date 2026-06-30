from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import uuid

from backend.pdf_parser import extract_text, split_into_segments
from backend.tts import generate_audio, get_available_voices
from backend.stt import transcribe_audio, get_supported_languages

app = FastAPI(title="Document Audio Tool")
STORAGE_DIR = Path(__file__).parent.parent / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = STORAGE_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
RECORD_DIR = STORAGE_DIR / "records"
RECORD_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    voice_id: str = Form(None),
    rate: int = Form(150)
):
    file_id = str(uuid.uuid4())[:8]
    pdf_path = UPLOAD_DIR / f"{file_id}.pdf"
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = extract_text(str(pdf_path))
    segments = split_into_segments(text)

    audio_paths = []
    for i, seg in enumerate(segments):
        audio_file = f"{file_id}_{i}"
        path = generate_audio(seg, f"audio/{audio_file}", voice_id, rate)
        audio_paths.append({"index": i, "text": seg, "audio": f"/audio/{audio_file}.mp3"})

    return {"id": file_id, "segments": audio_paths}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = Form("auto")):
    file_id = str(uuid.uuid4())[:8]
    ext = file.filename.split(".")[-1] if "." in file.filename else "wav"
    audio_path = RECORD_DIR / f"{file_id}.{ext}"
    with open(audio_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = audio_path.stat().st_size
    print(f"[Transcribe] File: {file.filename}, Size: {file_size} bytes ({file_size/1024/1024:.2f} MB), Ext: {ext}")

    text = transcribe_audio(str(audio_path), language)
    print(f"[Transcribe] Result: {text[:100] if text else 'empty'}...")
    return {"id": file_id, "text": text, "language": language}


@app.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    language: str = Form("zh-CN"),
    voice_id: str = Form(None),
    rate: int = Form(150)
):
    file_id = str(uuid.uuid4())[:8]
    audio_file = f"audio/tts_{file_id}"
    generate_audio(text, audio_file, voice_id, rate)
    return {"id": file_id, "audio": f"/audio/{audio_file}.mp3"}


@app.get("/voices")
async def voices():
    return get_available_voices()


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = AUDIO_DIR / filename
    if file_path.exists():
        return FileResponse(str(file_path), media_type="audio/mpeg")
    return {"error": "File not found"}


@app.get("/languages")
async def languages():
    return get_supported_languages()


@app.get("/")
async def root():
    return {"message": "Document Audio Tool API is running"}
