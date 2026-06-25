import base64
import json
import os
import requests
from pathlib import Path

STEP_API_KEY = "6SvrHcNdNjjHIzgjHr3VB8qmcYe97eskHh39UKfFHgk9cIsG8AMt9JKvu1BW9QMw"
STEP_BASE_URL = "https://api.stepfun.com"

DEEPSEEK_API_KEY = "sk-6d156d535c3c467a8b1cb40859b0dfc5"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

CHUNK_DURATION = 30 * 60  # 30分钟分段


def _get_audio_format(audio_path: str) -> str:
    suffix = Path(audio_path).suffix.lower().lstrip(".")
    return suffix if suffix in ["wav", "mp3", "ogg", "pcm"] else "wav"


def _get_audio_duration(audio_path: str) -> float:
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0
    except:
        return 0


def _split_audio(audio_path: str, chunk_duration_ms: int) -> list:
    from pydub import AudioSegment
    audio = AudioSegment.from_file(audio_path)
    chunks = []
    total_len = len(audio)
    temp_dir = Path(__file__).parent.parent / "storage" / "temp_chunks"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for i in range(0, total_len, chunk_duration_ms):
        chunk = audio[i:i + chunk_duration_ms]
        chunk_path = temp_dir / f"chunk_{i}.wav"
        chunk.export(str(chunk_path), format="wav")
        chunks.append(str(chunk_path))

    return chunks


def _step_asr(audio_path: str, language: str = "auto") -> str:
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_format = _get_audio_format(audio_path)

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
            timeout=300,
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


def _cleanup_chunks(chunks: list):
    for chunk_path in chunks:
        try:
            os.remove(chunk_path)
        except:
            pass


def transcribe_audio(audio_path: str, language: str = "auto") -> str:
    duration = _get_audio_duration(audio_path)

    if duration > 0 and duration * 1000 > CHUNK_DURATION * 1.5:
        chunks = _split_audio(audio_path, CHUNK_DURATION * 1000)
        all_texts = []

        for i, chunk_path in enumerate(chunks):
            raw_text = _step_asr(chunk_path, language)
            if raw_text and not raw_text.startswith("["):
                all_texts.append(raw_text)

        _cleanup_chunks(chunks)

        if not all_texts:
            return "[ASR返回为空]"

        full_text = "\n".join(all_texts)
        corrected_text = _deepseek_correct(full_text)
        return corrected_text
    else:
        raw_text = _step_asr(audio_path, language)
        corrected_text = _deepseek_correct(raw_text)
        return corrected_text


def get_supported_languages() -> dict:
    return {
        "auto": "自动检测",
        "zh": "中文",
        "en": "英语",
    }
