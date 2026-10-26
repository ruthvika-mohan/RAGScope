from datetime import datetime, timezone
import pytest
from ragscope.golden.generation import generate_candidates, prepare_candidates, validate_evidence
from ragscope.golden.models import GoldenTestCase, ReviewStatus


def test_generator_cannot_auto_approve(case, document):
    data = case.model_dump()
    data.update(review_status='approved', reviewer_id='provider', reviewed_at=datetime.now(timezone.utc), reviewer_notes='Auto-approved')
    class FakeGenerator:
        def generate(self, documents):
            assert documents == [document]
            return [GoldenTestCase.model_validate(data)]
    result = generate_candidates(FakeGenerator(), [document])
    generated = result.cases[0]
    assert generated.review_status == ReviewStatus.PENDING
    assert generated.reviewer_id is generated.reviewed_at is generated.reviewer_notes is None


@pytest.mark.parametrize('changes', [{'text': 'Invented evidence'}, {'page_number': 2}, {'document_id': 'other'}])
def test_rejects_untraceable_evidence(case, document, changes):
    data = case.model_dump()
    data['golden_evidence'][0].update(changes)
    with pytest.raises(ValueError):
        prepare_candidates([GoldenTestCase.model_validate(data)], [document])


def test_manifest_must_match(dataset, document):
    other = document.model_copy(update={'source': document.source.model_copy(update={'sha256': 'b' * 64})})
    with pytest.raises(ValueError, match='manifest'):
        validate_evidence(dataset, [other])
