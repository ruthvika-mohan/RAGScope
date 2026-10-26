# RAGScope

RAGScope is a foundation for building human-approved ground truth for later RAG evaluation. This version ingests PDFs, validates proposed evidence, supports human review, and exports approved cases. It does not run a RAG pipeline or call an LLM.

## Setup

Requires Python 3.11+.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ragscope --help
```

## Workflow

### 1. Extract documents

```sh
ragscope ingest path/to/document.pdf path/to/another.pdf --output extracted_documents.json
```

Each page retains its document ID, original file name, one-based page number, and extracted text. IDs default to `sha256:<file hash>`. File hashes are also stored in the source manifest. Identical content cannot be ingested twice in one command. Empty pages are retained with warnings. Scanned PDFs need an external OCR step; this loader does not perform OCR. PDF reading order and text quality should be checked before proposing evidence.

### 2. Supply candidate cases

Create a JSON **array** in `proposed_cases.json`. Copy the document ID and a verbatim evidence excerpt from `extracted_documents.json`:

```json
[
  {
    "id": "case-001",
    "question": "How much did revenue increase?",
    "question_type": "factual",
    "expected_answer": "Revenue increased by 12 percent.",
    "golden_evidence": [
      {
        "document_id": "COPY_DOCUMENT_ID_FROM_EXTRACTION",
        "page_number": 1,
        "text": "Revenue increased by 12 percent."
      }
    ],
    "expected_metadata": {"category": "finance"},
    "review_status": "pending",
    "reviewer_notes": null
  }
]
```

This is an illustrative example, not a case generated from a bundled document.

```sh
ragscope import-candidates proposed_cases.json --documents extracted_documents.json
```

This creates `candidate_dataset.json`. Evidence must be a nonblank exact substring of its referenced extracted page. Unknown sources, missing pages, duplicate IDs, and mismatched excerpts are rejected. Provider-supplied review decisions and attribution are cleared; every imported candidate starts pending. Inputs must satisfy the typed schema before normalization. Existing ingestion/import output files require `--overwrite` to replace them.

### 3. Review

```sh
ragscope review --documents extracted_documents.json --reviewer your-name
```

The CLI checks evidence provenance, then displays each pending question, expected answer, question type, metadata, evidence, document name/ID, and page. Choose approve, reject, skip, or quit. Approvals and rejections accept optional notes and are saved immediately, with reviewer identity and a UTC timestamp. Skipped cases remain pending. Completed decisions survive quitting or restarting the command.

Reviewers determine whether the answer is correct, whether evidence supports it, and whether metadata expectations are appropriate. A matching excerpt alone does not establish correctness. Reject incorrect candidates and fix/reimport the original proposals as needed; reimport resets all review decisions. Use a separate candidate file if preserving prior decisions is necessary.

### 4. Export ground truth

```sh
ragscope export
```

This writes `golden_dataset.json` containing **only approved cases** and the source manifest. Export replaces an existing golden output; it does not modify the candidate file. An export with no approvals contains an empty case list. Alternate paths are available via `--dataset` and `--output`.

Dataset files contain `schema_version`, `sources`, and `cases`. Loading validates their schema and source references. Candidate evidence is verified against the saved extraction on import and review; ordinary dataset loading does not reopen original PDFs. Keep original PDFs and extraction JSON alongside datasets for reproducibility. These local files are trusted artifacts, not tamper-proof audit records. Review is single-user; concurrent writes are unsupported.

## Architecture

```text
src/ragscope/
  config.py          Default paths
  cli.py             argparse interface only
  ingestion/         Loader protocol, source/page models, PDF loader
  golden/            Case schema, candidate generation, provenance checks, JSON persistence
  review/            UI-independent review decisions
  chunking/          Future package
  embeddings/        Future package
  retrieval/         Future package
  generation/        Future answer-generation package
  evaluation/        Future package
  experiments/       Future package
  visualization/     Future package
```

`DocumentLoader` is a small protocol for additional loaders. A loader returns an `IngestedDocument` with source identity and extracted units.

`CandidateGenerator` is a provider-independent protocol. Future LLM adapters should live in separate modules with optional provider dependencies. Pass an adapter to `generate_candidates(generator, documents)`; the service validates evidence and resets review status. No model/provider SDK is required today. Externally generated cases can use the CLI import path above.

`review_case` returns an updated dataset without changing its input. Applications may approve/reject a case again to correct a decision; the latest reviewer attribution replaces the earlier decision. This is not an append-only audit history. The v0 CLI displays only pending cases.

`save_dataset` revalidates the dataset and atomically replaces its destination. `export_approved` filters approved cases without changing the source dataset. `question_type` is an open string, and `expected_metadata` accepts JSON values rather than a document-specific taxonomy.

### Golden evidence and retrieved chunks

`GoldenEvidence` describes proposed source excerpts until a human approves their containing case. Approved evidence is the ground truth for future retrieval and generation evaluation. It never represents chunks returned by an experiment. The schema rejects extra fields such as `retrieved_chunks`; future experiment outputs must use separate models referencing test-case IDs.

Future work can evaluate corpus/embeddings, retrieval quality (Recall@K, Precision@K, hit rate, MRR, coverage, filters), and generated answers (correctness, groundedness, citations) independently. None of those metrics, retrieval systems, embedding providers, or generation pipelines are implemented in this version.

## Tests

Tests cover actual PDF extraction including blank-page preservation, source identity, schema constraints, evidence verification, generator review resets, review decisions, persistence round trips, and approved-only exports. All fixtures use synthetic, document-independent content.
