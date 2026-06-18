import fitz
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR

ocr_engine = RapidOCR()


def extract_text_pymupdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    doc.close()
    return text.strip()


def ocr_pdf(pdf_path: str, max_pages: int = 1) -> str:
    doc = fitz.open(pdf_path)
    all_text = []
    total = min(len(doc), max_pages)
    for i in range(total):
        page = doc[i]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        result, _ = ocr_engine(img_bytes)
        if result:
            page_text = "\n".join([item[1] for item in result])
            all_text.append(page_text)
    doc.close()
    return "\n".join(all_text)


def extract_text(pdf_path: str) -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    text = extract_text_pymupdf(str(path))
    if text:
        return text

    return ocr_pdf(str(path))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf模块.py <path_to_pdf>")
        sys.exit(1)
    text = extract_text(sys.argv[1])
    print(text[:500])
    print(f"\n--- Total chars: {len(text)} ---")
