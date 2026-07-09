"""语音识别模块 - StepFun ASR + DeepSeek 纠错"""
import base64
import json
import os
import subprocess
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from backend.config import (
    STEP_API_KEY, STEP_BASE_URL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    MAX_BASE64_SIZE, CHUNK_SECONDS,
    VIDEO_EXTENSIONS, TEMP_DIR
)

# 获取 ffmpeg 路径
FFMPEG_PATH = None
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except:
    pass


def _get_audio_format(audio_path: str) -> str:
    """获取音频格式"""
    suffix = Path(audio_path).suffix.lower().lstrip(".")
    format_map = {
        "wav": "wav", "mp3": "mp3", "ogg": "ogg", "pcm": "pcm",
        "m4a": "m4a", "aac": "aac", "flac": "flac",
    }
    return format_map.get(suffix, "mp3")


def _is_video_file(file_path: str) -> bool:
    """判断是否是视频文件"""
    suffix = Path(file_path).suffix.lower()
    return suffix in VIDEO_EXTENSIONS


def _extract_audio_from_video(video_path: str) -> str:
    """从视频中提取音频"""
    if not FFMPEG_PATH:
        return video_path

    audio_path = str(Path(video_path).with_suffix('.mp3'))

    # 用 ffmpeg 提取音频，采样率 16000，单声道，64kbps
    cmd = [
        FFMPEG_PATH, "-i", video_path,
        "-vn", "-acodec", "libmp3lame",
        "-ar", "16000", "-ac", "1",
        "-b:a", "64k",
        "-y", audio_path
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=300)
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            return audio_path
    except Exception as e:
        print(f"[VideoExtract] Error: {e}")

    return video_path


def _get_duration(audio_path: str) -> float:
    """获取音频时长（秒）"""
    if not FFMPEG_PATH:
        return 0
    try:
        cmd = [FFMPEG_PATH, "-i", audio_path, "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        stderr = result.stderr.decode("utf-8", errors="ignore")
        for line in stderr.split("\n"):
            if "Duration:" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parts.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
    except:
        pass
    return 0


def _split_and_compress(audio_path: str) -> list:
    """大文件分片处理"""
    if not FFMPEG_PATH:
        return [audio_path]

    duration = _get_duration(audio_path)
    file_size = os.path.getsize(audio_path)

    # 计算 base64 编码后的大小限制
    max_raw = MAX_BASE64_SIZE * 0.7 / 1.33

    # 文件小于限制，不分片
    if file_size <= max_raw:
        return [audio_path]

    print(f"[Split] Duration: {duration:.0f}s, Size: {file_size/1024/1024:.2f} MB")

    # 按 CHUNK_SECONDS 分片
    chunks = []
    total_ms = int(duration * 1000)
    chunk_ms = CHUNK_SECONDS * 1000

    for i in range(0, total_ms, chunk_ms):
        chunk_path = str(TEMP_DIR / f"chunk_{i}.mp3")
        cmd = [
            FFMPEG_PATH, "-i", audio_path,
            "-ss", str(i / 1000),
            "-t", str(CHUNK_SECONDS),
            "-ar", "16000", "-ac", "1",
            "-b:a", "32k",
            "-y", chunk_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)

        if os.path.exists(chunk_path):
            chunk_size = os.path.getsize(chunk_path)
            print(f"[Split] Chunk {len(chunks)+1}: {chunk_size/1024/1024:.2f} MB")
            if chunk_size > 0:
                chunks.append(chunk_path)

    return chunks if chunks else [audio_path]


def _cleanup(chunks: list, original: str):
    """清理临时分片文件"""
    for c in chunks:
        if c != original and os.path.exists(c):
            try:
                os.remove(c)
            except:
                pass


def _step_asr(audio_path: str, language: str = "auto") -> str:
    """调用 StepFun ASR 接口"""
    # 读取音频文件并 base64 编码
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_format = "mp3" if audio_path.endswith(".mp3") else _get_audio_format(audio_path)

    print(f"[ASR] Size: {len(audio_bytes)/1024/1024:.2f} MB, Format: {audio_format}")

    headers = {
        "Authorization": f"Bearer {STEP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    # 语言选择：zh 或 en，其他默认中文
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
        # SSE 流式响应
        resp = requests.post(
            f"{STEP_BASE_URL}/v1/audio/asr/sse",
            headers=headers,
            json=payload,
            timeout=600,
            stream=True,
        )
        resp.raise_for_status()

        # 解析 SSE 数据
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
    """用 DeepSeek 纠正语音识别结果"""
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


def _process_chunk(args):
    """处理单个分片（用于多线程）"""
    i, chunk, language = args
    print(f"[Transcribe] Chunk {i+1}")
    raw_text = _step_asr(chunk, language)
    return i, raw_text


def transcribe_audio(audio_path: str, language: str = "auto") -> str:
    """语音转文字主函数"""
    work_path = audio_path

    # 如果是视频，先提取音频
    if _is_video_file(audio_path):
        print(f"[Transcribe] Video detected, extracting audio...")
        work_path = _extract_audio_from_video(audio_path)
        if work_path == audio_path:
            return "[视频音频提取失败]"

    # 分片处理
    chunks = _split_and_compress(work_path)

    # 单片直接处理
    if len(chunks) == 1:
        raw_text = _step_asr(chunks[0], language)
        _cleanup(chunks, work_path)
        if work_path != audio_path and os.path.exists(work_path):
            os.remove(work_path)
        if not raw_text or raw_text.startswith("["):
            return raw_text if raw_text else "[ASR返回为空]"
        return _deepseek_correct(raw_text)

    # 多片并行处理
    args = [(i, chunk, language) for i, chunk in enumerate(chunks)]
    results = []

    with ThreadPoolExecutor(max_workers=min(len(chunks), 6)) as pool:
        results = list(pool.map(_process_chunk, args))

    # 清理临时文件
    _cleanup(chunks, work_path)
    if work_path != audio_path and os.path.exists(work_path):
        os.remove(work_path)

    # 合并结果
    results.sort(key=lambda x: x[0])
    all_texts = [text for _, text in results if text and not text.startswith("[")]

    if not all_texts:
        return "[ASR返回为空]"

    full_text = "\n".join(all_texts)
    return _deepseek_correct(full_text)


def get_supported_languages() -> dict:
    """获取支持的语言列表"""
    return {
        "auto": "自动检测",
        "zh": "中文",
        "en": "英语",
    }
