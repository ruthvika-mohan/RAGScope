"""Review decisions independent of any CLI or UI."""
from datetime import datetime, timezone
from ragscope.golden.models import GoldenDataset, GoldenTestCase, ReviewStatus

def review_case(dataset: GoldenDataset, case_id: str, decision: ReviewStatus, reviewer_id: str, notes: str | None = None) -> GoldenDataset:
    decision = ReviewStatus(decision)
    if decision == ReviewStatus.PENDING:
        raise ValueError("Review decision must be approved or rejected")
    if not reviewer_id.strip():
        raise ValueError("Reviewer ID must not be blank")
    if not any(case.id == case_id for case in dataset.cases):
        raise KeyError(f"Unknown case: {case_id}")
    cases = []
    for case in dataset.cases:
        if case.id == case_id:
            data = case.model_dump()
            data.update(review_status=decision, reviewer_id=reviewer_id, reviewer_notes=notes, reviewed_at=datetime.now(timezone.utc))
            case = GoldenTestCase.model_validate(data)
        cases.append(case)
    return GoldenDataset(sources=dataset.sources, cases=cases)
