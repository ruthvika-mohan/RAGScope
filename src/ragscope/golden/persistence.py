"""Validated JSON persistence with atomic replacement."""
import os
import tempfile
from pathlib import Path
from .models import GoldenDataset, ReviewStatus

def load_dataset(path: Path) -> GoldenDataset:
    return GoldenDataset.model_validate_json(Path(path).read_text(encoding="utf-8"))

def save_dataset(dataset: GoldenDataset, path: Path) -> None:
    validated = GoldenDataset.model_validate(dataset.model_dump())
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(validated.model_dump_json(indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def export_approved(dataset: GoldenDataset, path: Path) -> GoldenDataset:
    approved = GoldenDataset(sources=dataset.sources, cases=[case for case in dataset.cases if case.review_status == ReviewStatus.APPROVED])
    save_dataset(approved, path)
    return approved
