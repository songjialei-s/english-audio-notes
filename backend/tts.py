"""语音合成模块 - edge-tts"""
import re
import asyncio
import edge_tts
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from backend.config import STORAGE_DIR, VOICES

# 线程池执行器
_executor = ThreadPoolExecutor(max_workers=2)


def _clean_text_for_tts(text: str) -> str:
    """清理文本，去掉特殊符号，TTS 读起来更自然"""
    # 斜杠替换为 and（同义词连接符）
    text = text.replace('/', ' and ')
    # 去掉省略号
    text = re.sub(r'\.{2,}', ' ', text)
    # 去掉中文标点
    text = re.sub(r'[,，。！？、；：""''【】（）《》…—]', ' ', text)
    # 去掉英文标点
    text = re.sub(r'[.!?:;"\[\]()<>]', ' ', text)
    # 英文和非英文之间加空格
    text = re.sub(r'([a-zA-Z])([^\sa-zA-Z])', r'\1 \2', text)
    text = re.sub(r'([^\sa-zA-Z])([a-zA-Z])', r'\1 \2', text)
    # 合并多个空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text


async def _generate_async(text: str, output_path: str, voice: str, rate: str):
    """异步生成语音"""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


def _run_async(coro):
    """运行异步协程"""
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
    """生成语音文件"""
    output_path = STORAGE_DIR / f"{filename}.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 清理文本
    clean_text = _clean_text_for_tts(text)

    # 选择声音
    if voice and voice in VOICES:
        voice_name = VOICES[voice]
    elif voice and voice.startswith("zh"):
        voice_name = "zh-CN-XiaoxiaoNeural"
    elif voice and voice.startswith("en"):
        voice_name = "en-US-JennyNeural"
    else:
        voice_name = "zh-CN-XiaoxiaoNeural"

    # 语速映射：rate 值 -> edge-tts 格式
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

    # 生成语音
    _run_async(_generate_async(clean_text, str(output_path), voice_name, rate_str))

    return str(output_path)


def get_available_voices() -> list:
    """获取可用声音列表"""
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
