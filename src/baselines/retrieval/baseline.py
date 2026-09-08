"""THE RIVALS — Baseline 2: retrieval.

TF-IDF similarity retrieves the closest training example (by NL prompt) and reuses
its reference program. Purpose: can apparent neural-model competence be explained by
retrieval?

This is the simpler/no-learning baseline: it doesn't generate anything new, it just
finds a near-matching training prompt and returns that program.
"""
import os, json


class RetrievalBaseline:
    def __init__(self, train_tasks):
        """Store training tasks and build a TF-IDF index over their prompts."""
        self.tasks = train_tasks
        self.index = self._build_index([t["nl"]["prompt"] for t in train_tasks])

    def _build_index(self, texts):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self._cos = cosine_similarity
            self._vec = TfidfVectorizer().fit(texts)
            return self._vec
        except ImportError:
            self._cos = None
            return None

    def retrieve(self, prompt):
        """Return the reference program of the most-similar training task."""
        if self.index is None or self._cos is None:
            return None
        from sklearn.metrics.pairwise import cosine_similarity
        q = self.index.transform([prompt])
        train_mat = self.index.transform([t["nl"]["prompt"] for t in self.tasks])
        sim = cosine_similarity(q, train_mat)[0]
        best = int(sim.argmax())
        return self.tasks[best]["reference_code"]

    def baseline_generate(self, task):
        """Given a task, return the retrieved program."""
        return _maybe_adapt(self.retrieve(task["nl"]["prompt"]), task)


def _maybe_adapt(code, task):
    """Optionally adapt the retrieved program to the target function signature.
    For the pilot we return the retrieved code as-is (retrieval of a near-duplicate
    prompt usually yields the matching operation)."""
    return code
