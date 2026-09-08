"""Shortcut audit — dataset leakage.

Can a trivial classifier predict the target operation (or other semantic attributes)
from the natural-language specification alone? If yes, the dataset leaks the answer
through superficial wording. Also runs duplicate detection across splits.

See design/BOOK_DESIGN.md section 5 + spec section 11.
"""
import json
from collections import Counter

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    SKLEARN = True
except ImportError:
    SKLEARN = False


def load_tasks(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def text_of(t):
    return t["nl"]["prompt"]


def label_of(t, target="operation"):
    if target == "operation":
        return t["semantics"]["operation"]
    if target == "complexity":
        return str(t["semantics"].get("complexity"))
    if target == "output_type":
        return t["semantics"]["output_type"]
    return t["semantics"].get(target)


def classifier_leakage(tasks, target="operation"):
    """Train a TF-IDF + logistic-regression classifier to predict `target` from NL.
    Returns mean cross-val accuracy (0-1). High accuracy (>~0.9) => leakage warning.
    """
    if not SKLEARN:
        return None
    texts = [text_of(t) for t in tasks]
    labels = [label_of(t, target) for t in tasks]
    vec = TfidfVectorizer()
    X = vec.fit_transform(texts)
    clf = LogisticRegression(max_iter=1000)
    scores = cross_val_score(clf, X, labels, cv=5)
    return float(scores.mean())


def duplicate_checks(tasks):
    """Exact + normalized duplicate detection within and across splits."""
    from collections import Counter
    c = Counter(t["nl"]["prompt"].lower().strip() for t in tasks)
    dupes = [k for k, v in c.items() if v > 1]
    return len(dupes), dupes[:10]


def split_operation_distribution(tasks):
    by_split = {}
    for t in tasks:
        s = t.get("split", "?")
        by_split.setdefault(s, Counter())[t["semantics"]["operation"]] += 1
    return {s: dict(c) for s, c in by_split.items()}


def run_audit(dataset_path):
    tasks = load_tasks(dataset_path) if dataset_path.endswith(".jsonl") else []
    # For an audit across the whole pilot, load all split files.
    return tasks
