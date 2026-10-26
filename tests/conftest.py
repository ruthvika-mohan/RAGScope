import pytest
from ragscope.ingestion.models import ExtractedUnit, IngestedDocument, SourceDocument
from ragscope.golden.models import GoldenEvidence, GoldenTestCase
from ragscope.golden.generation import prepare_candidates

@pytest.fixture
def document():
    source = SourceDocument(document_id='sha256:' + 'a' * 64, document_name='example.pdf', sha256='a' * 64)
    return IngestedDocument(source=source, units=[ExtractedUnit(document_id=source.document_id, document_name=source.document_name, page_number=1, text='Revenue increased by 12 percent. Costs remained stable.')])

@pytest.fixture
def case(document):
    return GoldenTestCase(id='case-1', question='How much did revenue increase?', question_type='factual', expected_answer='12 percent.', golden_evidence=[GoldenEvidence(document_id=document.source.document_id, page_number=1, text='Revenue increased by 12 percent.')], expected_metadata={'category': 'finance'})

@pytest.fixture
def dataset(case, document):
    return prepare_candidates([case], [document])
