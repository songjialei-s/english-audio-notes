"""FastAPI 网站后端"""
import sys
import shutil
import uuid
import subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from web_sjl_database import add_history, get_history, delete_history, clear_history, get_settings, update_settings

app = FastAPI(title="Audio Notes Web")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_DIR = BASE_DIR.parent
STORAGE_DIR = BASE_DIR / "storage"
AUDIO_DIR = STORAGE_DIR / "audio"
RECORD_DIR = STORAGE_DIR / "records"
FRONTEND_DIR = BASE_DIR / "frontend"

for d in [STORAGE_DIR, AUDIO_DIR, RECORD_DIR]:
    d.mkdir(parents=True, exist_ok=True)

try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except:
    FFMPEG_PATH = "ffmpeg"

sys.path.insert(0, str(PROJECT_DIR))
from backend.tts import generate_audio, get_available_voices
from backend.stt import transcribe_audio, get_supported_languages
from backend.pdf_module import extract_text, get_pdf_page_count
from backend.pdf_parser import split_into_segments


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    voice_id: str = Form(None),
    rate: str = Form("100"),
    pages: str = Form("")
):
    try:
        rate = int(rate) if rate else 100
        file_id = str(uuid.uuid4())[:8]
        pdf_path = STORAGE_DIR / f"{file_id}.pdf"

        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        text = extract_text(str(pdf_path), pages_str=pages)
        segments = split_into_segments(text)

        audio_paths = []
        for i, seg in enumerate(segments):
            audio_file = f"{file_id}_{i}"
            generate_audio(seg, f"audio/{audio_file}", voice_id, rate)
            audio_paths.append({
                "index": i,
                "text": seg,
                "audio": f"/audio/{audio_file}.mp3"
            })

        add_history("pdf", file.name, text, audio_paths[0]["audio"] if audio_paths else None)

        return {"id": file_id, "segments": audio_paths}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form("auto")
):
    try:
        file_id = str(uuid.uuid4())[:8]
        ext = file.filename.split(".")[-1] if "." in file.filename else "mp3"
        audio_path = RECORD_DIR / f"{file_id}.{ext}"

        with open(audio_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        text = transcribe_audio(str(audio_path), language)

        add_history("transcribe", file.filename, text)

        return {"id": file_id, "text": text, "language": language}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/trim-silence")
async def trim_silence(
    file: UploadFile = File(...),
    silence_threshold: str = Form("-40"),
    min_silence_duration: str = Form("5")
):
    try:
        threshold_db = int(silence_threshold)
        min_duration = float(min_silence_duration)

        file_id = str(uuid.uuid4())[:8]
        ext = file.filename.split(".")[-1] if "." in file.filename else "mp3"
        input_path = str(RECORD_DIR / f"{file_id}_input.{ext}")
        output_path = str(RECORD_DIR / f"{file_id}_trimmed.mp3")

        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        original_duration = 0
        result = subprocess.run(
            [FFMPEG_PATH, "-i", input_path, "-f", "null", "-"],
            capture_output=True, text=True
        )
        for line in result.stderr.split("\n"):
            if "Duration:" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parts.split(":")
                original_duration = float(h) * 3600 + float(m) * 60 + float(s)
                break

        af = (
            f"silenceremove="
            f"start_periods=1:start_duration=0.1:start_threshold={threshold_db}dB:"
            f"stop_periods=-1:stop_duration={min_duration}:stop_threshold={threshold_db}dB,"
            f"apad=pad_dur=0.3"
        )

        subprocess.run(
            [FFMPEG_PATH, "-i", input_path, "-af", af, "-y", output_path],
            capture_output=True, timeout=300
        )

        if not Path(output_path).exists():
            return JSONResponse(status_code=500, content={"error": "裁剪失败"})

        trimmed_duration = 0
        result2 = subprocess.run(
            [FFMPEG_PATH, "-i", output_path, "-f", "null", "-"],
            capture_output=True, text=True
        )
        for line in result2.stderr.split("\n"):
            if "Duration:" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parts.split(":")
                trimmed_duration = float(h) * 3600 + float(m) * 60 + float(s)
                break

        Path(input_path).unlink()

        return {
            "id": file_id,
            "audio": f"/audio/{file_id}_trimmed.mp3",
            "original_duration": round(original_duration, 1),
            "trimmed_duration": round(trimmed_duration, 1),
            "saved_seconds": round(original_duration - trimmed_duration, 1)
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = AUDIO_DIR / filename
    if file_path.exists():
        return FileResponse(str(file_path), media_type="audio/mpeg")
    file_path = RECORD_DIR / filename
    if file_path.exists():
        return FileResponse(str(file_path), media_type="audio/mpeg")
    return JSONResponse(status_code=404, content={"error": "File not found"})


@app.get("/api/voices")
async def voices():
    return get_available_voices()


@app.get("/api/languages")
async def languages():
    return get_supported_languages()


@app.get("/api/history")
async def history():
    return get_history()


@app.delete("/api/history/{history_id}")
async def remove_history(history_id: int):
    delete_history(history_id)
    return {"status": "ok"}


@app.delete("/api/history")
async def clear_all_history():
    clear_history()
    return {"status": "ok"}


@app.get("/api/settings")
async def get_settings_api():
    return get_settings()


@app.post("/api/settings")
async def update_settings_api(voice_id: str = Form(None), rate: str = Form(None)):
    update_settings(voice_id, int(rate) if rate else None)
    return {"status": "ok"}


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
