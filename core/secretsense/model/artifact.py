"""Explicit trust boundary for local pickle artifacts; hashes are not signatures."""

import hashlib
import hmac
import math
import os
import pickle
import re
import stat
import warnings
from pathlib import Path

from secretsense.features import FEATURE_NAMES, FEATURE_VERSION

MAX_ARTIFACT_BYTES = 32 * 1024 * 1024


def save_artifact(model, threshold: float, path: Path) -> str:
    """Persist a locally trained model. Record the returned digest in trusted metadata."""
    payload = {
        "feature_version": FEATURE_VERSION,
        "feature_names": FEATURE_NAMES,
        "threshold": threshold,
        "model": model,
    }
    data = pickle.dumps(payload, protocol=5)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def load_trusted_artifact(path: Path, *, expected_sha256: str) -> dict:
    """Load only with a digest obtained independently from a trusted training run.

    A digest supplied alongside an untrusted pickle does NOT make it safe.
    Validate the very bytes being deserialized, avoiding a second file read.
    """
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("A trusted SHA-256 digest is required.")
    try:
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("Model artifact must be a regular file.")
            data = stream.read(MAX_ARTIFACT_BYTES + 1)
    except OSError:
        raise ValueError("Unable to read model artifact.") from None
    if len(data) > MAX_ARTIFACT_BYTES:
        raise ValueError("Model artifact exceeds the size limit.")
    if not hmac.compare_digest(hashlib.sha256(data).hexdigest(), expected_sha256):
        raise ValueError("Model artifact checksum mismatch; loading refused.")
    try:
        # Reject incompatible dependency versions and suppress unsafe warning text.
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            payload = pickle.loads(data)
    except ImportError:
        raise ValueError(
            "Model dependencies missing; install the matching ML environment."
        ) from None
    except Exception:
        raise ValueError(
            "Unable to deserialize model; use the matching training environment."
        ) from None
    if (
        not isinstance(payload, dict)
        or payload.get("feature_version") != FEATURE_VERSION
        or not isinstance(payload.get("feature_names"), (list, tuple))
        or tuple(payload["feature_names"]) != FEATURE_NAMES
    ):
        raise ValueError("Model feature schema mismatch.")
    try:
        from sklearn.ensemble import RandomForestClassifier

        model = payload["model"]
        threshold = payload["threshold"]
        valid = (
            isinstance(model, RandomForestClassifier)
            and model.n_features_in_ == len(FEATURE_NAMES)
            and list(model.classes_) == [0, 1]
            and isinstance(threshold, (int, float))
            and not isinstance(threshold, bool)
            and math.isfinite(threshold)
            and 0 <= threshold <= 1
        )
    except Exception:
        valid = False
    if not valid:
        raise ValueError("Model prediction schema mismatch.")
    return payload
