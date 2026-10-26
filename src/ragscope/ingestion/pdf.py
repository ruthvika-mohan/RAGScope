"""PDF text extraction; OCR is deliberately outside this loader."""
import hashlib
import io
import warnings
from pathlib import Path
from pypdf import PdfReader
from .models import ExtractedUnit, IngestedDocument, SourceDocument

class PDFLoader:
    def load(self, path: Path) -> IngestedDocument:
        data = Path(path).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        source = SourceDocument(document_id=f"sha256:{digest}", document_name=Path(path).name, sha256=digest)
        reader = PdfReader(io.BytesIO(data))
        units = []
        for number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                warnings.warn(f"No extractable text: {source.document_name}, page {number}", UserWarning)
            units.append(ExtractedUnit(document_id=source.document_id, document_name=source.document_name, page_number=number, text=text))
        return IngestedDocument(source=source, units=units)
