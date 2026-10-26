"""Local CLI for ingestion, candidate import, review, and golden export."""
import argparse
import json
from pathlib import Path
from pydantic import TypeAdapter
from ragscope.config import CANDIDATE_PATH, GOLDEN_PATH
from ragscope.ingestion.models import IngestedDocument
from ragscope.ingestion.pdf import PDFLoader
from ragscope.golden.generation import prepare_candidates, validate_evidence
from ragscope.golden.models import GoldenTestCase, ReviewStatus
from ragscope.golden.persistence import export_approved, load_dataset, save_dataset
from ragscope.review.service import review_case


def _documents(path: Path) -> list[IngestedDocument]:
    return TypeAdapter(list[IngestedDocument]).validate_json(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="Extract PDF pages to JSON")
    ingest.add_argument("pdfs", nargs="+", type=Path)
    ingest.add_argument("--output", type=Path, default=Path("extracted_documents.json"))
    ingest.add_argument("--overwrite", action="store_true")
    candidates = commands.add_parser("import-candidates", help="Validate a JSON array of candidate cases")
    candidates.add_argument("input", type=Path)
    candidates.add_argument("--documents", type=Path, required=True)
    candidates.add_argument("--output", type=Path, default=CANDIDATE_PATH)
    candidates.add_argument("--overwrite", action="store_true")
    review = commands.add_parser("review", help="Interactively inspect and decide cases")
    review.add_argument("--dataset", type=Path, default=CANDIDATE_PATH)
    review.add_argument("--documents", type=Path, required=True)
    review.add_argument("--reviewer", required=True)
    export = commands.add_parser("export", help="Export approved ground truth")
    export.add_argument("--dataset", type=Path, default=CANDIDATE_PATH)
    export.add_argument("--output", type=Path, default=GOLDEN_PATH)
    args = parser.parse_args()
    try:
        if args.command in ("ingest", "import-candidates") and args.output.exists() and not args.overwrite:
            parser.error("Output exists; use --overwrite to replace it")
        if args.command == "ingest":
            documents = [PDFLoader().load(path) for path in args.pdfs]
            if len({doc.source.document_id for doc in documents}) != len(documents):
                raise ValueError("Duplicate document content supplied")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(TypeAdapter(list[IngestedDocument]).dump_json(documents, indent=2).decode() + "\n", encoding="utf-8")
            print(f"Extracted {sum(len(doc.units) for doc in documents)} pages to {args.output}")
        elif args.command == "import-candidates":
            cases = TypeAdapter(list[GoldenTestCase]).validate_json(args.input.read_text(encoding="utf-8"))
            dataset = prepare_candidates(cases, _documents(args.documents))
            save_dataset(dataset, args.output)
            print(f"Saved {len(dataset.cases)} pending cases to {args.output}")
        elif args.command == "review":
            if not args.reviewer.strip():
                raise ValueError("Reviewer ID must not be blank")
            dataset = load_dataset(args.dataset)
            validate_evidence(dataset, _documents(args.documents))
            names = {source.document_id: source.document_name for source in dataset.sources}
            for case in dataset.cases:
                if case.review_status != ReviewStatus.PENDING:
                    continue
                print(f"\nCase: {case.id}\nType: {case.question_type}\nQuestion: {case.question}\nExpected answer: {case.expected_answer}")
                print("Expected metadata:", json.dumps(case.expected_metadata, indent=2, ensure_ascii=False))
                for evidence in case.golden_evidence:
                    print(f"Evidence — {names[evidence.document_id]}, page {evidence.page_number}\nDocument ID: {evidence.document_id}\n{evidence.text}")
                while True:
                    action = input("[a]pprove / [r]eject / [s]kip / [q]uit: ").strip().lower()
                    if action in {"a", "r", "s", "q"}:
                        break
                    print("Enter a, r, s, or q.")
                if action == "q":
                    break
                if action == "s":
                    continue
                notes = input("Reviewer notes (optional): ").strip() or None
                decision = ReviewStatus.APPROVED if action == "a" else ReviewStatus.REJECTED
                dataset = review_case(dataset, case.id, decision, args.reviewer, notes)
                save_dataset(dataset, args.dataset)
                print(f"Saved decision: {decision.value}")
        else:
            if args.dataset.resolve() == args.output.resolve():
                raise ValueError("Golden export must use a different path from the candidate dataset")
            approved = export_approved(load_dataset(args.dataset), args.output)
            print(f"Exported {len(approved.cases)} approved cases to {args.output}")
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Error: {error}\n")
    except (EOFError, KeyboardInterrupt):
        print("\nReview stopped; completed decisions have been saved.")


if __name__ == "__main__":
    main()
