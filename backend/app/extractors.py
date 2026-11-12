import io
import fitz  # PyMuPDF
from docx import Document


def extract_text(filename: str, data: bytes) -> str:
    ext = filename.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        with fitz.open(stream=data, filetype='pdf') as doc:
            text = '\n'.join(page.get_text() for page in doc)
    elif ext == 'docx':
        d = Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs]
        for table in d.tables:
            for row in table.rows:
                parts.append(' | '.join(c.text for c in row.cells))
        text = '\n'.join(parts)
    else:
        raise ValueError('Only PDF and DOCX files are supported')
    text = text.strip()
    if not text:
        raise ValueError('No text found. The file may be a scanned image (OCR is not supported)')
    return text