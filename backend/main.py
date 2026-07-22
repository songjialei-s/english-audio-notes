"""FastAPI 主入口 - 路由定义"""
import shutil
import uuid
import subprocess
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from backend.config import UPLOAD_DIR, AUDIO_DIR, RECORD_DIR, TEMP_DIR
from backend.pdf_parser import extract_text, split_into_segments
from backend.tts import generate_audio, get_available_voices
from backend.stt import transcribe_audio, get_supported_languages
from backend.pdf_module import get_pdf_page_count

# 获取 FFmpeg 路径
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except:
    FFMPEG_PATH = "ffmpeg"

app = FastAPI(title="Document Audio Tool")


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    voice_id: str = Form(None),
    rate: str = Form("100"),
    pages: str = Form('')
):
    """上传 PDF 并生成语音"""
    try:
        rate = int(rate) if rate else 100
        print(f"[UPLOAD] voice_id={voice_id}, rate={rate}, pages={pages}")

        # 保存上传的 PDF
        file_id = str(uuid.uuid4())[:8]
        pdf_path = UPLOAD_DIR / f"{file_id}.pdf"
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 提取文本并分段
        text = extract_text(str(pdf_path), pages_str=pages)
        segments = split_into_segments(text)

        # 为每段生成语音
        audio_paths = []
        for i, seg in enumerate(segments):
            audio_file = f"{file_id}_{i}"
            generate_audio(seg, f"audio/{audio_file}", voice_id, rate)
            audio_paths.append({
                "index": i,
                "text": seg,
                "audio": f"/audio/{audio_file}.mp3"
            })

        return {"id": file_id, "segments": audio_paths}

    except Exception as e:
        print(f"[UPLOAD] Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form("auto")
):
    """语音/视频转文字"""
    try:
        file_id = str(uuid.uuid4())[:8]
        ext = file.filename.split(".")[-1] if "." in file.filename else "wav"
        audio_path = RECORD_DIR / f"{file_id}.{ext}"

        # 保存上传的文件
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 打印文件信息
        file_size = audio_path.stat().st_size
        print(f"[Transcribe] File: {file.filename}, Size: {file_size/1024/1024:.2f} MB")

        # 转写
        text = transcribe_audio(str(audio_path), language)
        print(f"[Transcribe] Result: {text[:100] if text else 'empty'}...")

        return {"id": file_id, "text": text, "language": language}

    except Exception as e:
        print(f"[Transcribe] Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    language: str = Form("zh-CN"),
    voice_id: str = Form(None),
    rate: str = Form("100")
):
    """文本转语音"""
    try:
        rate = int(rate) if rate else 100
        file_id = str(uuid.uuid4())[:8]
        audio_file = f"tts_{file_id}"
        generate_audio(text, f"audio/{audio_file}", voice_id, rate)
        return {"id": file_id, "audio": f"/audio/{audio_file}.mp3"}

    except Exception as e:
        print(f"[TTS] Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/voices")
async def voices():
    """获取可用声音列表"""
    return get_available_voices()


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """获取音频文件"""
    file_path = AUDIO_DIR / filename
    if file_path.exists():
        return FileResponse(str(file_path), media_type="audio/mpeg")
    return JSONResponse(status_code=404, content={"error": "File not found"})


@app.get("/languages")
async def languages():
    """获取支持的语言列表"""
    return get_supported_languages()


@app.get("/pdf-info")
async def pdf_info(filename: str):
    """获取 PDF 页数"""
    pdf_path = UPLOAD_DIR / filename
    if not pdf_path.exists():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    count = get_pdf_page_count(str(pdf_path))
    return {"pages": count}


@app.get("/")
async def root():
    """健康检查"""
    return {"message": "Document Audio Tool API is running"}


@app.get("/health")
async def health():
    """服务健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/trim-silence")
async def trim_silence(
    file: UploadFile = File(...),
    silence_threshold: str = Form("-40"),
    min_silence_duration: str = Form("5")
):
    """裁剪音频中的静默片段"""
    try:
        threshold_db = int(silence_threshold)
        min_duration = float(min_silence_duration)

        file_id = str(uuid.uuid4())[:8]
        ext = file.filename.split(".")[-1] if "." in file.filename else "mp3"
        input_path = str(RECORD_DIR / f"{file_id}_input.{ext}")
        output_path = str(RECORD_DIR / f"{file_id}_trimmed.mp3")

        # 保存上传文件
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        original_size = RECORD_DIR / f"{file_id}_input.{ext}"
        original_duration_cmd = [
            FFMPEG_PATH, "-i", input_path,
            "-f", "null", "-"
        ]
        result = subprocess.run(original_duration_cmd, capture_output=True, text=True)
        # 从 stderr 解析时长
        original_duration = 0
        for line in result.stderr.split("\n"):
            if "Duration:" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parts.split(":")
                original_duration = float(h) * 3600 + float(m) * 60 + float(s)
                break

        # FFmpeg silenceremove 滤镜
        # 移除超过指定时长的静默片段，替换为0.3秒短停顿
        af = (
            f"silenceremove="
            f"start_periods=1:"
            f"start_duration=0.1:"
            f"start_threshold={threshold_db}dB:"
            f"stop_periods=-1:"
            f"stop_duration={min_duration}:"
            f"stop_threshold={threshold_db}dB,"
            f"apad=pad_dur=0.3"
        )

        cmd = [
            FFMPEG_PATH, "-i", input_path,
            "-af", af,
            "-y", output_path
        ]

        print(f"[TrimSilence] threshold={threshold_db}dB, min_duration={min_duration}s")
        subprocess.run(cmd, capture_output=True, timeout=300)

        if not __import__("os").path.exists(output_path):
            return JSONResponse(status_code=500, content={"error": "裁剪失败"})

        # 获取裁剪后时长
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

        # 清理输入文件
        __import__("os").remove(input_path)

        saved = original_duration - trimmed_duration
        print(f"[TrimSilence] Original: {original_duration:.1f}s, Trimmed: {trimmed_duration:.1f}s, Saved: {saved:.1f}s")

        return {
            "id": file_id,
            "audio": f"/audio/{file_id}_trimmed.mp3",
            "original_duration": round(original_duration, 1),
            "trimmed_duration": round(trimmed_duration, 1),
            "saved_seconds": round(saved, 1)
        }

    except Exception as e:
        print(f"[TrimSilence] Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
