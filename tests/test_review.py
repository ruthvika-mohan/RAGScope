import pytest
from ragscope.review.service import review_case
from ragscope.golden.models import ReviewStatus


@pytest.mark.parametrize('decision', [ReviewStatus.APPROVED, ReviewStatus.REJECTED])
def test_review_records_attribution_without_mutating_input(dataset, decision):
    reviewed = review_case(dataset, 'case-1', decision, 'human', 'Checked source')
    assert dataset.cases[0].review_status == ReviewStatus.PENDING
    case = reviewed.cases[0]
    assert case.review_status == decision
    assert case.reviewer_id == 'human'
    assert case.reviewer_notes == 'Checked source'
    assert case.reviewed_at.utcoffset() is not None
    assert case.golden_evidence == dataset.cases[0].golden_evidence


def test_invalid_review(dataset):
    with pytest.raises(ValueError):
        review_case(dataset, 'case-1', ReviewStatus.PENDING, 'human')
    with pytest.raises(ValueError):
        review_case(dataset, 'case-1', ReviewStatus.APPROVED, ' ')
    with pytest.raises(KeyError):
        review_case(dataset, 'missing', ReviewStatus.APPROVED, 'human')
