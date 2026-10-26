"""Source documents and extracted page units."""
from pydantic import BaseModel, ConfigDict, Field, model_validator

class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_id: str = Field(min_length=1)
    document_name: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

class ExtractedUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_id: str = Field(min_length=1)
    document_name: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    text: str

class IngestedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: SourceDocument
    units: list[ExtractedUnit]

    @model_validator(mode="after")
    def valid_units(self) -> "IngestedDocument":
        pages = [unit.page_number for unit in self.units]
        if len(pages) != len(set(pages)):
            raise ValueError("Extracted page numbers must be unique within a document")
        for unit in self.units:
            if unit.document_id != self.source.document_id or unit.document_name != self.source.document_name:
                raise ValueError("Extracted unit identity must match the source manifest")
        return self
