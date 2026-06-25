import base64
import requests
from pathlib import Path

MIMO_API_KEY = "sk-c04enis3enaeuvc0eiz3psz4vwc5ggzmztotuesagbyfr22a"
MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"

DEEPSEEK_API_KEY = "sk-6d156d535c3c467a8b1cb40859b0dfc5"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def _get_mime_type(audio_path: str) -> str:
    suffix = Path(audio_path).suffix.lower()
    mime_map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".webm": "audio/webm",
    }
    return mime_map.get(suffix, "audio/wav")


def _mimo_asr(audio_path: str, language: str = "auto") -> str:
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    mime_type = _get_mime_type(audio_path)
    data_url = f"data:{mime_type};base64,{audio_b64}"

    headers = {
        "api-key": MIMO_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "model": "mimo-v2.5-asr",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": data_url,
                        },
                    }
                ],
            }
        ],
        "asr_options": {
            "language": language,
        },
    }

    try:
        resp = requests.post(
            f"{MIMO_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[MiMo ASR Error: {e}]"


def _deepseek_correct(raw_text: str) -> str:
    if not raw_text or raw_text.startswith("["):
        return raw_text

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = f"""你是英语录音纠错助手。语音识别了一段英语录音。

【核心规则】
1. 纠正明显的语音识别错误（同音词、近音词）
2. 词组必须完整保留，包括with/sth/to等搭配词：
   - correlate with sth 与...相互关联
   - spur to sth 对...的激励
   - amount to sth 等同于
3. sth = something, sb = somebody, 保留不翻译
4. 根据上下文补全标点符号
5. 如果是英语学习内容，保持原文不翻译

【语音识别内容】
{raw_text}

【纠正后输出】"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.1,
    }

    try:
        resp = requests.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return raw_text


def transcribe_audio(audio_path: str, language: str = "auto") -> str:
    raw_text = _mimo_asr(audio_path, language)
    corrected_text = _deepseek_correct(raw_text)
    return corrected_text


def get_supported_languages() -> dict:
    return {
        "auto": "自动检测",
        "zh": "中文",
        "en": "英语",
    }
