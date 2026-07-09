"""PDF 文本提取模块"""
import fitz
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR
from backend.volcano_llm import correct_with_llm

# OCR 引擎
ocr_engine = RapidOCR()


def _parse_page_range(pages_str: str, total_pages: int) -> list:
    """解析页码范围字符串，如 '1-5,8,10-12'"""
    if not pages_str or pages_str.strip() == '':
        return list(range(total_pages))

    result = set()
    parts = pages_str.replace('，', ',').split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            # 处理范围：1-5
            start, end = part.split('-', 1)
            start = max(1, int(start.strip()))
            end = min(total_pages, int(end.strip()))
            result.update(range(start - 1, end))
        else:
            # 处理单页：3
            page = int(part.strip())
            if 1 <= page <= total_pages:
                result.add(page - 1)
    return sorted(result)


def extract_text_pymupdf(pdf_path: str, pages: list = None) -> str:
    """用 PyMuPDF 提取文本（适用于文字版 PDF）"""
    doc = fitz.open(pdf_path)
    if pages is None:
        pages = list(range(len(doc)))
    text = "\n".join([doc[i].get_text() for i in pages if i < len(doc)])
    doc.close()
    return text.strip()


def ocr_pdf(pdf_path: str, max_pages: int = 10, pages: list = None) -> str:
    """用 RapidOCR 识别图片版 PDF"""
    doc = fitz.open(pdf_path)
    all_text = []
    if pages is None:
        pages = list(range(min(len(doc), max_pages)))
    for i in pages:
        if i >= len(doc):
            continue
        page = doc[i]
        # 渲染页面为图片
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        # OCR 识别
        result, _ = ocr_engine(img_bytes)
        if result:
            page_text = "\n".join([item[1] for item in result])
            all_text.append(page_text)
    doc.close()
    return "\n".join(all_text)


def extract_text(pdf_path: str, use_llm: bool = True, pages_str: str = '') -> str:
    """提取 PDF 文本（优先文字版，失败用 OCR）"""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # 获取总页数
    doc = fitz.open(str(path))
    total_pages = len(doc)
    doc.close()

    # 解析页码范围
    pages = _parse_page_range(pages_str, total_pages)

    # 优先尝试 PyMuPDF 提取
    text = extract_text_pymupdf(str(path), pages)
    if text:
        return text

    # 文字版失败，用 OCR
    raw_ocr = ocr_pdf(str(path), pages=pages)

    # 用 LLM 纠正 OCR 结果
    if use_llm and raw_ocr:
        corrected = correct_with_llm(raw_ocr)
        if corrected and not corrected.startswith("[LLM Error"):
            return corrected

    return raw_ocr


def get_pdf_page_count(pdf_path: str) -> int:
    """获取 PDF 页数"""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m backend.pdf_module <path_to_pdf>")
        sys.exit(1)
    text = extract_text(sys.argv[1])
    print(text[:500])
    print(f"\n--- Total chars: {len(text)} ---")
