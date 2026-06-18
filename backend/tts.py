import pyttsx3
from pathlib import Path

STORAGE_DIR = Path(__file__).parent.parent / "storage"


def generate_audio(text: str, filename: str, voice: str = None) -> str:
    output_path = STORAGE_DIR / f"{filename}.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    engine = pyttsx3.init()
    if voice:
        engine.setProperty('voice', voice)
    engine.setProperty('rate', 150)
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    return str(output_path)
