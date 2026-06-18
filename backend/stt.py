import speech_recognition as sr
from pathlib import Path


def transcribe_audio(audio_path: str, language: str = "zh-CN") -> str:
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(audio_path)

    with audio_file as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data, language=language)
        return text
    except sr.UnknownValueError:
        return "[无法识别音频内容]"
    except sr.RequestError as e:
        return f"[语音识别服务错误: {e}]"


def get_supported_languages() -> dict:
    return {
        "zh-CN": "中文",
        "en-US": "英语",
        "ja-JP": "日语",
        "ko-KR": "韩语",
        "fr-FR": "法语",
        "de-DE": "德语",
        "es-ES": "西班牙语",
    }
