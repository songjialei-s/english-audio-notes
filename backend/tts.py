import re
import asyncio
import edge_tts
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

STORAGE_DIR = Path(__file__).parent.parent / "storage"
_executor = ThreadPoolExecutor(max_workers=2)


def _clean_text_for_tts(text: str) -> str:
    text = text.replace('/', ' and ')
    text = re.sub(r'\.{2,}', ' ', text)
    text = re.sub(r'[,，。！？、；：""''【】（）《》…—]', ' ', text)
    text = re.sub(r'[.!?:;"\[\]()<>]', ' ', text)
    text = re.sub(r'([a-zA-Z])([^\sa-zA-Z])', r'\1 \2', text)
    text = re.sub(r'([^\sa-zA-Z])([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


VOICES = {
    "zh-female": "zh-CN-XiaoxiaoNeural",
    "zh-male": "zh-CN-YunxiNeural",
    "en-us-female": "en-US-JennyNeural",
    "en-us-male": "en-US-GuyNeural",
    "en-gb-female": "en-GB-SoniaNeural",
    "en-gb-male": "en-GB-RyanNeural",
}


async def _generate_async(text: str, output_path: str, voice: str, rate: str):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=120)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def generate_audio(text: str, filename: str, voice: str = None, rate: int = 0) -> str:
    output_path = STORAGE_DIR / f"{filename}.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clean_text = _clean_text_for_tts(text)

    if voice and voice in VOICES:
        voice_name = VOICES[voice]
    elif voice and voice.startswith("zh"):
        voice_name = "zh-CN-XiaoxiaoNeural"
    elif voice and voice.startswith("en"):
        voice_name = "en-US-JennyNeural"
    else:
        voice_name = "zh-CN-XiaoxiaoNeural"

    if rate >= 200:
        rate_str = "+100%"
    elif rate >= 150:
        rate_str = "+50%"
    elif rate >= 100:
        rate_str = "+0%"
    elif rate >= 50:
        rate_str = "-25%"
    else:
        rate_str = "-50%"
    
    print(f"[TTS] rate={rate} -> rate_str={rate_str}")

    _run_async(_generate_async(clean_text, str(output_path), voice_name, rate_str))

    return str(output_path)


def get_available_voices() -> list:
    result = []
    for key, voice_id in VOICES.items():
        lang = "zh" if "zh" in key else "en"
        gender = "女" if "female" in key else "男"
        region = ""
        if "gb" in key:
            region = "英式"
        elif "us" in key:
            region = "美式"
        elif "zh" in key:
            region = "中文"

        result.append({
            "id": key,
            "name": f"{region}{gender}声",
            "lang": lang,
            "region": region,
            "voice_id": voice_id
        })
    return result
