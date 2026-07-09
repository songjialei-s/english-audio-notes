"""文本纠错模块"""
import re
from backend.volcano_llm import correct_with_llm


def correct_ocr_text(text: str, use_llm: bool = True) -> str:
    """纠正 OCR 识别结果"""
    # 优先用 LLM 纠正
    if use_llm and text.strip():
        corrected = correct_with_llm(text)
        if corrected and not corrected.startswith("[LLM Error"):
            return corrected

    # LLM 失败时，简单过滤空行
    lines = text.split("\n")
    result = []
    for line in lines:
        line = line.strip()
        if line and re.search(r'[a-zA-Z]', line):
            result.append(line)
    return "\n".join(result)
