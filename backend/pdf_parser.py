"""PDF 解析模块"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pdf模块 import extract_text
from backend.text_corrector import correct_ocr_text


def split_into_segments(text: str, max_len: int = 200) -> list[str]:
    """将文本按长度分段，用于 TTS"""
    # 先用 LLM 纠正文本
    corrected = correct_ocr_text(text)

    # 按行分割，去掉空行
    lines = [l.strip() for l in corrected.split("\n") if l.strip()]

    # 按 max_len 分段
    segments = []
    buf = ""
    for line in lines:
        if len(buf) + len(line) + 1 <= max_len:
            buf += line + "\n"
        else:
            if buf:
                segments.append(buf.strip())
            buf = line + "\n"
    if buf:
        segments.append(buf.strip())

    return segments
