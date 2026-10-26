import json
import sys
import pytest
from pydantic import TypeAdapter
from ragscope.cli import main
from ragscope.ingestion.models import IngestedDocument
from ragscope.golden.persistence import load_dataset, save_dataset


def test_import_review_export(tmp_path, document, case, monkeypatch, capsys):
    documents = tmp_path / 'documents.json'
    documents.write_bytes(TypeAdapter(list[IngestedDocument]).dump_json([document]))
    proposed = tmp_path / 'proposed.json'
    proposed.write_text(json.dumps([case.model_dump(mode='json')]))
    candidate = tmp_path / 'candidate_dataset.json'
    golden = tmp_path / 'golden_dataset.json'
    monkeypatch.setattr(sys, 'argv', ['ragscope', 'import-candidates', str(proposed), '--documents', str(documents), '--output', str(candidate)])
    main()
    responses = iter(['invalid', 'a', 'Checked page'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(responses))
    monkeypatch.setattr(sys, 'argv', ['ragscope', 'review', '--dataset', str(candidate), '--documents', str(documents), '--reviewer', 'human'])
    main()
    output = capsys.readouterr().out
    for value in [case.question, case.expected_answer, case.golden_evidence[0].text, 'page 1', 'finance']:
        assert value in output
    monkeypatch.setattr(sys, 'argv', ['ragscope', 'export', '--dataset', str(candidate), '--output', str(golden)])
    main()
    assert load_dataset(golden).cases[0].reviewer_notes == 'Checked page'


@pytest.mark.parametrize('action', ['s', 'q'])
def test_skip_and_quit_preserve_pending(tmp_path, dataset, document, monkeypatch, action):
    candidate = tmp_path / 'candidate.json'
    documents = tmp_path / 'documents.json'
    save_dataset(dataset, candidate)
    documents.write_bytes(TypeAdapter(list[IngestedDocument]).dump_json([document]))
    monkeypatch.setattr('builtins.input', lambda prompt: action)
    monkeypatch.setattr(sys, 'argv', ['ragscope', 'review', '--dataset', str(candidate), '--documents', str(documents), '--reviewer', 'human'])
    main()
    assert load_dataset(candidate) == dataset


def test_export_cannot_overwrite_candidate(tmp_path, dataset, monkeypatch):
    candidate = tmp_path / 'candidate.json'
    save_dataset(dataset, candidate)
    monkeypatch.setattr(sys, 'argv', ['ragscope', 'export', '--dataset', str(candidate), '--output', str(candidate)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    assert load_dataset(candidate) == dataset
