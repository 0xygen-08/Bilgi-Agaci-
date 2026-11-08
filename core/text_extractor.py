"""
OCR (Image-to-Text) and PDF Text Extraction Engine for Knowledge Tree.

Supports:
1. PDF text extraction via `pypdf` (with fallback to `pdftotext` CLI and OCR on scanned PDF images).
2. Image OCR (Optical Character Recognition) via:
   - Bundled `assets/tessdata` (`tur+eng`) with `tesseract` CLI / `pytesseract`
   - System `tesseract` language models (`tur`, `eng`, or any available Latin script)
   - `rapidocr_onnxruntime` if installed
"""

import os
import shutil
import subprocess
import sys
import tempfile


def _resolve_bundled_tessdata() -> str | None:
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate = os.path.join(base, "assets", "tessdata")
    if os.path.isdir(candidate) and (
        os.path.exists(os.path.join(candidate, "tur.traineddata"))
        or os.path.exists(os.path.join(candidate, "eng.traineddata"))
    ):
        return candidate
    return None


def _get_system_tesseract_langs() -> list[str]:
    if not shutil.which("tesseract"):
        return []
    try:
        proc = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
        return [ln for ln in lines if not ln.lower().startswith("list of available") and ln != "osd"]
    except Exception:
        return []


def extract_text_from_image(image_path: str) -> str:
    """Extract readable text (Turkish + English) from an image file."""
    if not image_path or not os.path.exists(image_path):
        return ""

    if shutil.which("tesseract"):
        bundled_dir = _resolve_bundled_tessdata()
        if bundled_dir:
            has_tur = os.path.exists(os.path.join(bundled_dir, "tur.traineddata"))
            has_eng = os.path.exists(os.path.join(bundled_dir, "eng.traineddata"))
            lang_arg = "tur+eng" if (has_tur and has_eng) else ("tur" if has_tur else "eng")
            try:
                proc = subprocess.run(
                    [
                        "tesseract",
                        image_path,
                        "stdout",
                        "--tessdata-dir",
                        bundled_dir,
                        "-l",
                        lang_arg,
                        "--oem",
                        "1",
                        "--psm",
                        "3",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=25,
                    check=False,
                )
                if proc.returncode == 0 and proc.stdout and proc.stdout.strip():
                    return proc.stdout.strip()
            except Exception:
                pass

        # Fallback to system tessdata languages
        sys_langs = _get_system_tesseract_langs()
        candidates = []
        if "tur" in sys_langs and "eng" in sys_langs:
            candidates.append("tur+eng")
        if "tur" in sys_langs:
            candidates.append("tur")
        if "eng" in sys_langs:
            candidates.append("eng")
        for extra in sys_langs:
            if extra not in candidates:
                candidates.append(extra)

        for lang in candidates:
            try:
                proc = subprocess.run(
                    ["tesseract", image_path, "stdout", "-l", lang, "--oem", "1", "--psm", "3"],
                    capture_output=True,
                    text=True,
                    timeout=25,
                    check=False,
                )
                if proc.returncode == 0 and proc.stdout and proc.stdout.strip():
                    return proc.stdout.strip()
            except Exception:
                continue

    return ""


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all readable text from a PDF file (including scanned image pages via OCR)."""
    if not pdf_path or not os.path.exists(pdf_path):
        return ""

    extracted_pages = []
    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_txt = ""
            try:
                page_txt = (page.extract_text() or "").strip()
            except Exception:
                page_txt = ""

            if page_txt:
                extracted_pages.append(page_txt)
            else:
                # Scanned PDF page fallback: run OCR on embedded page images
                try:
                    for image_file_object in getattr(page, "images", []):
                        ext = os.path.splitext(image_file_object.name)[1].lower() or ".png"
                        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_img:
                            tmp_img.write(image_file_object.data)
                            tmp_img_path = tmp_img.name
                        try:
                            ocr_txt = extract_text_from_image(tmp_img_path)
                            if ocr_txt:
                                extracted_pages.append(ocr_txt)
                        finally:
                            if os.path.exists(tmp_img_path):
                                os.remove(tmp_img_path)
                except Exception:
                    pass
    except Exception:
        pass

    if not extracted_pages and shutil.which("pdftotext"):
        try:
            proc = subprocess.run(
                ["pdftotext", "-enc", "UTF-8", pdf_path, "-"],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            if proc.stdout and proc.stdout.strip():
                extracted_pages.append(proc.stdout.strip())
        except Exception:
            pass

    return "\n\n".join(extracted_pages).strip()


def extract_pdf_pages_structured(pdf_path: str) -> list[dict]:
    """
    Extract structured pages from a PDF file.
    Returns: list of dicts: [{'page_num': 1, 'text': '...', 'preview': '...'}]
    """
    if not pdf_path or not os.path.exists(pdf_path):
        return []

    structured_pages = []
    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            page_num = i + 1
            page_txt = ""
            try:
                page_txt = (page.extract_text() or "").strip()
            except Exception:
                page_txt = ""

            if not page_txt:
                # OCR fallback on scanned page images
                try:
                    for image_file_object in getattr(page, "images", []):
                        ext = os.path.splitext(image_file_object.name)[1].lower() or ".png"
                        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_img:
                            tmp_img.write(image_file_object.data)
                            tmp_img_path = tmp_img.name
                        try:
                            ocr_txt = extract_text_from_image(tmp_img_path)
                            if ocr_txt:
                                page_txt = (page_txt + "\n" + ocr_txt).strip()
                        finally:
                            if os.path.exists(tmp_img_path):
                                os.remove(tmp_img_path)
                except Exception:
                    pass

            structured_pages.append({
                "page_num": page_num,
                "text": page_txt,
            })
    except Exception:
        pass

    return structured_pages


def extract_text_from_file(file_path: str) -> str:
    """Unified dispatcher for extracting text from either an image or a PDF."""
    if not file_path or not os.path.exists(file_path):
        return ""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
        return extract_text_from_image(file_path)
    return ""
