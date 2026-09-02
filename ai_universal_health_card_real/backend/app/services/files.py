from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from PIL import Image
import io

ALLOWED = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

def validate_upload(file: UploadFile, max_bytes: int):
    if file.content_type not in ALLOWED:
        raise HTTPException(400, "Only PDF, JPG and PNG files are supported")
    if not file.filename:
        raise HTTPException(400, "Filename is required")

async def save_upload(file: UploadFile, directory: str, max_bytes: int):
    validate_upload(file, max_bytes)
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > max_bytes:
        raise HTTPException(413, "File exceeds configured upload limit")

    # Basic structural validation for PDF/image files.
    if file.content_type == "application/pdf":
        try:
            PdfReader(io.BytesIO(data))
        except Exception:
            raise HTTPException(400, "Invalid PDF")
    else:
        try:
            Image.open(io.BytesIO(data)).verify()
        except Exception:
            raise HTTPException(400, "Invalid image")

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}{ALLOWED[file.content_type]}"
    path = directory / stored
    path.write_bytes(data)
    return stored, path, len(data)

def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

def extract_text(path: Path, mime_type: str) -> str:
    if mime_type == "application/pdf":
        return extract_pdf_text(path)
    # OCR is deliberately optional. No fabricated OCR text is generated.
    try:
        import pytesseract
        image = Image.open(path)
        return pytesseract.image_to_string(image).strip()
    except Exception:
        return ""
