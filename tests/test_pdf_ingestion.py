import hashlib
import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from ragscope.ingestion.pdf import PDFLoader


def test_pdf_extracts_text_and_preserves_blank_page(tmp_path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 20 200 Td (Revenue increased by 12 percent.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    writer.add_blank_page(width=300, height=300)
    path = tmp_path / 'arbitrary.pdf'
    writer.write(path)
    with pytest.warns(UserWarning, match='page 2'):
        result = PDFLoader().load(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert result.source.document_id == f'sha256:{digest}'
    assert result.source.sha256 == digest
    assert [unit.page_number for unit in result.units] == [1, 2]
    assert result.units[0].text == 'Revenue increased by 12 percent.'
    assert result.units[1].text == ''
    assert all(unit.document_name == path.name and unit.document_id == result.source.document_id for unit in result.units)
