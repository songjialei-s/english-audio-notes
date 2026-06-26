import re
import pyttsx3
from pathlib import Path

STORAGE_DIR = Path(__file__).parent.parent / "storage"


def _clean_text_for_tts(text: str) -> str:
    text = re.sub(r'[，。！？、；：""''【】（）《》…—\-]', ' ', text)
    text = re.sub(r'[,.!?;:""\[\]()<>]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def generate_audio(text: str, filename: str, voice: str = None, rate: int = 150) -> str:
    output_path = STORAGE_DIR / f"{filename}.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clean_text = _clean_text_for_tts(text)

    engine = pyttsx3.init()
    if voice:
        engine.setProperty('voice', voice)
    engine.setProperty('rate', rate)
    engine.save_to_file(clean_text, str(output_path))
    engine.runAndWait()
    return str(output_path)


def get_available_voices() -> list:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    result = []
    for v in voices:
        lang = "zh" if "ZH" in v.id.upper() else "en"
        region = "US" if "US" in v.id.upper() else "UK" if "UK" in v.id.upper() else ""
        result.append({
            "id": v.id,
            "name": v.name,
            "lang": lang,
            "region": region
        })
    return result
