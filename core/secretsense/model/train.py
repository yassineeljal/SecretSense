"""Fit on training data and select parameters/threshold using validation only."""

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, fbeta_score, precision_recall_fscore_support

# Fixed before test evaluation. Prefer recall using F2, then recall, then precision.
CONFIGURATIONS = (
    {"max_depth": 6, "min_samples_leaf": 2},
    {"max_depth": 12, "min_samples_leaf": 2},
    {"max_depth": None, "min_samples_leaf": 1},
)
THRESHOLDS = (0.25, 0.4, 0.5, 0.6, 0.75)


def metrics(labels, predictions) -> dict:
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    return {
        "rows": len(labels),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "f2": float(fbeta_score(labels, predictions, beta=2, zero_division=0)),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
    }


def select_model(train_x, train_y, validation_x, validation_y, *, seed: int = 20260930):
    """Never receives test data. Return the selected fitted model and selection audit."""
    if set(train_y) != {0, 1} or set(validation_y) != {0, 1}:
        raise ValueError("Training and validation must each contain both labels.")
    trials = []
    best = None
    for parameters in CONFIGURATIONS:
        model = RandomForestClassifier(
            n_estimators=100, random_state=seed, n_jobs=1, class_weight="balanced", **parameters
        ).fit(train_x, train_y)
        scores = model.predict_proba(validation_x)[:, 1]
        for threshold in THRESHOLDS:
            result = metrics(validation_y, scores >= threshold)
            trial = {"parameters": parameters, "threshold": threshold, "metrics": result}
            trials.append(trial)
            rank = (result["f2"], result["recall"], result["precision"], -abs(threshold - 0.5))
            if best is None or rank > best[0]:
                best = (rank, model, trial)
    return best[1], {"selected": best[2], "trials": trials, "seed": seed}
