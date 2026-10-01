"""Feature and model contracts; all credential-shaped strings are built at runtime."""

import hashlib
import math
import pickle

import pytest

from secretsense.features import FEATURE_NAMES, extract_features
from secretsense.model.artifact import load_trusted_artifact, save_artifact
from secretsense.model.train import metrics, select_model
from secretsense.scanner.candidates import extract_candidates
from secretsense.scanner.engine import scan_text


def test_features_numeric_context_and_private_inputs():
    value = "ghp_" + "Ab3x" * 9
    vector = extract_features(value, f'github_token = "{value}"')
    assert len(vector) == len(FEATURE_NAMES)
    assert all(math.isfinite(item) for item in vector)
    mapped = dict(zip(FEATURE_NAMES, vector, strict=True))
    assert mapped["length"] == 40
    assert mapped["format_match"] == mapped["secret_name"] == 1
    assert mapped["placeholder_marker"] == 0
    benign_context = extract_features(value, f'build_id = "{value}"')
    assert benign_context[FEATURE_NAMES.index("secret_name")] == 0
    for invalid in ("", "absent"):
        with pytest.raises(ValueError) as error:
            extract_features(invalid, value)
        assert value not in str(error.value)
    assert extract_features("dummy_" + "x" * 16, "dummy_" + "x" * 16)[-2] == 1
    assert extract_features("${NAME}", "token = ${NAME}")[-1] == 1


def test_candidates_keep_offsets_only_and_match_findings():
    value = "ghp_" + "Ab3x" * 9
    content = f'first = "{value}"\napi_token = "{value}"'
    candidates = extract_candidates(content)
    findings = scan_text(content)
    assert len(candidates) == len(findings) == 2
    assert all(content[item.start : item.end] == value for item in candidates)
    assert value not in repr(candidates) + repr(findings)
    assert [item.rule_id for item in candidates] == [item.rule_id for item in findings]


def test_selection_metrics_and_trusted_roundtrip(tmp_path):
    x = [[0.0] * len(FEATURE_NAMES), [1.0] * len(FEATURE_NAMES)] * 10
    y = [0, 1] * 10
    model, audit = select_model(x, y, x, y, seed=12)
    assert len(audit["trials"]) == 15
    assert audit["selected"]["metrics"]["recall"] == 1
    assert audit["selected"]["threshold"] == 0.5
    path = tmp_path / "model.pkl"
    digest = save_artifact(model, 0.5, path)
    restored = load_trusted_artifact(path, expected_sha256=digest)
    assert (restored["model"].predict_proba(x) == model.predict_proba(x)).all()
    assert restored["threshold"] == 0.5
    assert metrics([0, 0, 1, 1], [0, 1, 0, 1])["confusion_matrix"] == [[1, 1], [1, 1]]
    with pytest.raises(ValueError, match="both labels"):
        select_model(x, [1] * len(x), x, y)


def test_artifact_rejected_before_deserialization(tmp_path, monkeypatch):
    from secretsense.model import artifact

    path = tmp_path / "untrusted.pkl"
    path.write_bytes(b"untrusted artifact")

    def forbidden(data):
        pytest.fail("Unverified pickle was deserialized")

    monkeypatch.setattr(artifact.pickle, "loads", forbidden)
    with pytest.raises(ValueError, match="trusted SHA-256"):
        load_trusted_artifact(path, expected_sha256="invalid")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_trusted_artifact(path, expected_sha256="0" * 64)
    monkeypatch.setattr(artifact, "MAX_ARTIFACT_BYTES", 4)
    with pytest.raises(ValueError, match="size limit"):
        load_trusted_artifact(path, expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def test_artifact_schema_rejection(tmp_path):
    path = tmp_path / "old.pkl"
    data = pickle.dumps({"feature_version": -1, "feature_names": ()})
    path.write_bytes(data)
    with pytest.raises(ValueError, match="schema mismatch"):
        load_trusted_artifact(path, expected_sha256=hashlib.sha256(data).hexdigest())
