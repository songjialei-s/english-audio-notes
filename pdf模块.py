import fitz
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR
from backend.volcano_llm import correct_with_llm

ocr_engine = RapidOCR()


def _parse_page_range(pages_str: str, total_pages: int) -> list:
    if not pages_str or pages_str.strip() == '':
        return list(range(total_pages))
    
    result = set()
    parts = pages_str.replace('，', ',').split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            start = max(1, int(start.strip()))
            end = min(total_pages, int(end.strip()))
            result.update(range(start - 1, end))
        else:
            page = int(part.strip())
            if 1 <= page <= total_pages:
                result.add(page - 1)
    return sorted(result)


def extract_text_pymupdf(pdf_path: str, pages: list = None) -> str:
    doc = fitz.open(pdf_path)
    if pages is None:
        pages = list(range(len(doc)))
    text = "\n".join([doc[i].get_text() for i in pages if i < len(doc)])
    doc.close()
    return text.strip()


def ocr_pdf(pdf_path: str, max_pages: int = 10, pages: list = None) -> str:
    doc = fitz.open(pdf_path)
    all_text = []
    if pages is None:
        pages = list(range(min(len(doc), max_pages)))
    for i in pages:
        if i >= len(doc):
            continue
        page = doc[i]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        result, _ = ocr_engine(img_bytes)
        if result:
            page_text = "\n".join([item[1] for item in result])
            all_text.append(page_text)
    doc.close()
    return "\n".join(all_text)


def extract_text(pdf_path: str, use_llm: bool = True, pages_str: str = '') -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(path))
    total_pages = len(doc)
    doc.close()

    pages = _parse_page_range(pages_str, total_pages)

    text = extract_text_pymupdf(str(path), pages)
    if text:
        return text

    raw_ocr = ocr_pdf(str(path), pages=pages)

    if use_llm and raw_ocr:
        corrected = correct_with_llm(raw_ocr)
        if corrected and not corrected.startswith("[LLM Error"):
            return corrected

    return raw_ocr


def get_pdf_page_count(pdf_path: str) -> int:
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf模块.py <path_to_pdf>")
        sys.exit(1)
    text = extract_text(sys.argv[1])
    print(text[:500])
    print(f"\n--- Total chars: {len(text)} ---")
