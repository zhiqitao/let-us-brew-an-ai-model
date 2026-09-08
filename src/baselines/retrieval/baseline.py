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
        self._cos = None
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self._cos = cosine_similarity
            texts = [t["nl"]["prompt"] for t in train_tasks]
            self._vec = TfidfVectorizer().fit(texts)
            self._train_mat = self._vec.transform(texts)  # precompute ONCE
            self.index = self._vec
        except ImportError:
            self.index = None
            self._train_mat = None

    def retrieve(self, prompt):
        """Return the reference program of the most-similar training task."""
        if self._train_mat is None or self._cos is None:
            return None
        q = self._vec.transform([prompt])
        sim = self._cos(q, self._train_mat)[0]
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
