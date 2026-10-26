import pytest
from ragscope.golden.models import GoldenDataset, GoldenTestCase, ReviewStatus
from ragscope.golden.persistence import export_approved, load_dataset, save_dataset
from ragscope.review.service import review_case


def test_round_trip(dataset, tmp_path):
    path = tmp_path / 'nested' / 'candidate_dataset.json'
    save_dataset(dataset, path)
    assert load_dataset(path) == dataset
    assert list(path.parent.iterdir()) == [path]


def test_only_approved_exported(dataset, tmp_path):
    cases = []
    for name in ['approved', 'rejected', 'pending']:
        data = dataset.cases[0].model_dump()
        data['id'] = name
        cases.append(GoldenTestCase.model_validate(data))
    mixed = GoldenDataset(sources=dataset.sources, cases=cases)
    mixed = review_case(mixed, 'approved', ReviewStatus.APPROVED, 'human')
    mixed = review_case(mixed, 'rejected', ReviewStatus.REJECTED, 'human')
    path = tmp_path / 'golden_dataset.json'
    exported = export_approved(mixed, path)
    assert [case.id for case in exported.cases] == ['approved']
    assert load_dataset(path) == exported
    assert len(mixed.cases) == 3
    assert exported.sources == mixed.sources


def test_empty_approved_export(dataset, tmp_path):
    assert export_approved(dataset, tmp_path / 'golden_dataset.json').cases == []


def test_malformed_json_rejected(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text('{broken')
    with pytest.raises(ValueError):
        load_dataset(path)
