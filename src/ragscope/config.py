"""Default output paths; callers can override these through the CLI."""
from pathlib import Path

CANDIDATE_PATH = Path("candidate_dataset.json")
GOLDEN_PATH = Path("golden_dataset.json")
