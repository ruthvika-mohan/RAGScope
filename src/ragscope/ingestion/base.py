"""Minimal extension point for additional document loaders."""
from pathlib import Path
from typing import Protocol
from .models import IngestedDocument

class DocumentLoader(Protocol):
    def load(self, path: Path) -> IngestedDocument: ...
