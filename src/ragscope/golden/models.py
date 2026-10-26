"""Human-reviewed evidence is independent of any retrieval experiment."""
from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator
from ragscope.ingestion.models import SourceDocument

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class GoldenEvidence(BaseModel):
    """Proposed source evidence until its containing case is approved."""
    model_config = ConfigDict(extra="forbid")
    document_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    text: str = Field(min_length=1)

    @field_validator("document_id", "text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank")
        return value

class GoldenTestCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    question_type: str = Field(min_length=1)
    expected_answer: str = Field(min_length=1)
    golden_evidence: list[GoldenEvidence] = Field(min_length=1)
    expected_metadata: dict[str, JsonValue] = Field(default_factory=dict)
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewer_notes: str | None = None
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None

    @field_validator("id", "question", "question_type", "expected_answer")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank")
        return value

    @model_validator(mode="after")
    def valid_review(self) -> "GoldenTestCase":
        if self.review_status == ReviewStatus.PENDING:
            if self.reviewer_id is not None or self.reviewed_at is not None:
                raise ValueError("Pending cases cannot have review attribution")
        elif not self.reviewer_id or not self.reviewer_id.strip() or self.reviewed_at is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("Reviewed cases require reviewer_id and a timezone-aware reviewed_at")
        return self

class GoldenDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"
    sources: list[SourceDocument] = Field(default_factory=list)
    cases: list[GoldenTestCase] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_references(self) -> "GoldenDataset":
        source_ids = [source.document_id for source in self.sources]
        case_ids = [case.id for case in self.cases]
        if len(set(source_ids)) != len(source_ids) or len(set(case_ids)) != len(case_ids):
            raise ValueError("Document and case IDs must be unique")
        for case in self.cases:
            for evidence in case.golden_evidence:
                if evidence.document_id not in source_ids:
                    raise ValueError(f"Unknown evidence document: {evidence.document_id}")
        return self
