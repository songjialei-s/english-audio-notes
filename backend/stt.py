import base64
import json
import os
import subprocess
import requests
from pathlib import Path

STEP_API_KEY = "6SvrHcNdNjjHIzgjHr3VB8qmcYe97eskHh39UKfFHgk9cIsG8AMt9JKvu1BW9QMw"
STEP_BASE_URL = "https://api.stepfun.com"

DEEPSEEK_API_KEY = "sk-6d156d535c3c467a8b1cb40859b0dfc5"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
CHUNK_DURATION = 10 * 60  # 10分钟分段

FFMPEG_PATH = None
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except:
    pass


def _get_audio_format(audio_path: str) -> str:
    suffix = Path(audio_path).suffix.lower().lstrip(".")
    format_map = {
        "wav": "wav", "mp3": "mp3", "ogg": "ogg", "pcm": "pcm",
        "m4a": "m4a", "aac": "aac", "flac": "flac",
    }
    return format_map.get(suffix, "mp3")


def _compress_audio(audio_path: str) -> str:
    if not FFMPEG_PATH:
        return audio_path

    file_size = os.path.getsize(audio_path)
    max_raw_size = MAX_FILE_SIZE * 0.75

    if file_size <= max_raw_size:
        return audio_path

    print(f"[Compress] Original: {file_size/1024/1024:.2f} MB, need < {max_raw_size/1024/1024:.2f} MB")
    compressed_path = audio_path + ".compressed.mp3"

    try:
        cmd = [
            FFMPEG_PATH,
            "-i", audio_path,
            "-ar", "16000",
            "-ac", "1",
            "-b:a", "32k",
            "-y",
            compressed_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)

        if os.path.exists(compressed_path):
            new_size = os.path.getsize(compressed_path)
            print(f"[Compress] Compressed: {new_size/1024/1024:.2f} MB")
            if new_size <= max_raw_size:
                return compressed_path
            os.remove(compressed_path)
    except Exception as e:
        print(f"[Compress] Error: {e}")

    return audio_path


def _step_asr(audio_path: str, language: str = "auto") -> str:
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_format = _get_audio_format(audio_path)

    if audio_path.endswith(".wav"):
        audio_format = "wav"

    print(f"[ASR] Size: {len(audio_bytes)/1024/1024:.2f} MB, Format: {audio_format}")

    headers = {
        "Authorization": f"Bearer {STEP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    lang = "zh" if language == "zh" else "en" if language == "en" else "zh"

    payload = {
        "audio": {
            "data": audio_b64,
            "input": {
                "transcription": {
                    "model": "stepaudio-2.5-asr",
                    "language": lang,
                    "enable_itn": True,
                },
                "format": {
                    "type": audio_format,
                },
            },
        }
    }

    try:
        resp = requests.post(
            f"{STEP_BASE_URL}/v1/audio/asr/sse",
            headers=headers,
            json=payload,
            timeout=600,
            stream=True,
        )
        resp.raise_for_status()

        final_text = ""
        for line in resp.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data:"):
                    data_str = line_str[5:].strip()
                    if data_str and data_str != "[DONE]":
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "transcript.text.done":
                                final_text = data.get("text", "")
                        except:
                            pass
        return final_text.strip() if final_text else "[ASR返回为空]"
    except Exception as e:
        return f"[StepFun ASR Error: {e}]"


def _deepseek_correct(raw_text: str) -> str:
    if not raw_text or raw_text.startswith("["):
        return raw_text

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = f"""你是会议记录纠错助手。语音识别了一段会议录音。

【核心规则】
1. 纠正明显的语音识别错误（同音词、近音词）
2. 根据上下文理解专业术语并纠正
3. 根据上下文补全标点符号
4. 保持原文语言，不要翻译
5. 适当整理格式，使其更易读

【语音识别内容】
{raw_text}

【纠正后输出】"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8192,
        "temperature": 0.1,
    }

    try:
        resp = requests.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return raw_text


def transcribe_audio(audio_path: str, language: str = "auto") -> str:
    target_path = _compress_audio(audio_path)
    raw_text = _step_asr(target_path, language)

    if target_path != audio_path and os.path.exists(target_path):
        os.remove(target_path)

    corrected_text = _deepseek_correct(raw_text)
    return corrected_text


def get_supported_languages() -> dict:
    return {
        "auto": "自动检测",
        "zh": "中文",
        "en": "英语",
    }
