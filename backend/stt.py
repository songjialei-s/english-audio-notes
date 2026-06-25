from faster_whisper import WhisperModel
from pathlib import Path

DEEPSEEK_API_KEY = "sk-6d156d535c3c467a8b1cb40859b0dfc5"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

_model = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def _whisper_asr(audio_path: str, language: str = "auto") -> str:
    model = _get_model()
    lang = None if language == "auto" else language
    segments, info = model.transcribe(audio_path, language=lang, beam_size=5)
    text = " ".join([seg.text for seg in segments])
    return text.strip()


def _deepseek_correct(raw_text: str) -> str:
    if not raw_text or raw_text.startswith("["):
        return raw_text

    import requests

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
    raw_text = _whisper_asr(audio_path, language)
    corrected_text = _deepseek_correct(raw_text)
    return corrected_text


def get_supported_languages() -> dict:
    return {
        "auto": "自动检测",
        "zh": "中文",
        "en": "英语",
    }
