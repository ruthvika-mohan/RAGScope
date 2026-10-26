import pytest
from pydantic import ValidationError
from ragscope.golden.models import GoldenDataset, GoldenTestCase


def test_rejects_duplicate_ids(dataset):
    with pytest.raises(ValidationError, match='unique'):
        GoldenDataset(sources=dataset.sources, cases=dataset.cases * 2)


def test_rejects_unknown_source(case):
    with pytest.raises(ValidationError, match='Unknown evidence document'):
        GoldenDataset(cases=[case])


@pytest.mark.parametrize('field,value', [('question', ' '), ('golden_evidence', []), ('review_status', 'golden'), ('review_status', 'approved')])
def test_rejects_invalid_cases(case, field, value):
    data = case.model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        GoldenTestCase.model_validate(data)


def test_retrieved_chunks_are_not_case_fields(case):
    data = case.model_dump()
    data['retrieved_chunks'] = []
    with pytest.raises(ValidationError, match='Extra inputs'):
        GoldenTestCase.model_validate(data)


def test_extraction_rejects_inconsistent_identity(document):
    from ragscope.ingestion.models import IngestedDocument
    data = document.model_dump()
    data['units'][0]['document_id'] = 'wrong'
    with pytest.raises(ValidationError, match='identity'):
        IngestedDocument.model_validate(data)


def test_extraction_rejects_duplicate_pages(document):
    from ragscope.ingestion.models import IngestedDocument
    data = document.model_dump()
    data['units'] *= 2
    with pytest.raises(ValidationError, match='unique'):
        IngestedDocument.model_validate(data)
