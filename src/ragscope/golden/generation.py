"""Provider-independent candidate generation and source validation."""
from typing import Protocol, Sequence
from ragscope.ingestion.models import IngestedDocument
from .models import GoldenDataset, GoldenTestCase

class CandidateGenerator(Protocol):
    def generate(self, documents: Sequence[IngestedDocument]) -> Sequence[GoldenTestCase]: ...

def validate_evidence(dataset: GoldenDataset, documents: Sequence[IngestedDocument]) -> None:
    """Verify source identity and verbatim page evidence against loaded documents."""
    sources = {doc.source.document_id: doc.source for doc in documents}
    pages = {(unit.document_id, unit.page_number): unit.text for doc in documents for unit in doc.units}
    for source in dataset.sources:
        if sources.get(source.document_id) != source:
            raise ValueError(f"Source manifest does not match ingested document: {source.document_id}")
    for case in dataset.cases:
        for evidence in case.golden_evidence:
            page = pages.get((evidence.document_id, evidence.page_number))
            if page is None or evidence.text not in page:
                raise ValueError(f"Evidence for case {case.id} does not match its source page")

def prepare_candidates(cases: Sequence[GoldenTestCase], documents: Sequence[IngestedDocument]) -> GoldenDataset:
    """Reset all provider-supplied review decisions before accepting candidates."""
    pending = []
    for case in cases:
        data = case.model_dump()
        data.update(review_status="pending", reviewer_notes=None, reviewer_id=None, reviewed_at=None)
        pending.append(GoldenTestCase.model_validate(data))
    dataset = GoldenDataset(sources=[doc.source for doc in documents], cases=pending)
    validate_evidence(dataset, documents)
    return dataset

def generate_candidates(generator: CandidateGenerator, documents: Sequence[IngestedDocument]) -> GoldenDataset:
    return prepare_candidates(generator.generate(documents), documents)
