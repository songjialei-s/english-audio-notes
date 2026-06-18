import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pdf模块 import extract_text


def split_into_segments(text: str, max_len: int = 500) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    segments = []
    for para in paragraphs:
        if len(para) <= max_len:
            segments.append(para)
        else:
            sentences = para.replace("。", ".").replace("？", "?").replace("！", "!").split(".")
            buf = ""
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if len(buf) + len(sent) < max_len:
                    buf += sent + ". "
                else:
                    if buf:
                        segments.append(buf.strip())
                    buf = sent + ". "
            if buf:
                segments.append(buf.strip())
    return segments
