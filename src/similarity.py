from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

class DualSimilarity:
    def __init__(self, hf_model: str):
        self.sbert = SentenceTransformer(hf_model)
        self.tfidf = TfidfVectorizer(stop_words="english")

    def _tfidf_score(self, a: str, b: str) -> float:
        mat = self.tfidf.fit_transform([a, b])
        return cosine_similarity(mat[0], mat[1])[0, 0]

    def _sbert_score(self, a: str, b: str) -> float:
        emb = self.sbert.encode([a, b], normalize_embeddings=True)
        return float(np.dot(emb[0], emb[1]))

    def score(self, resume_text: str, job_text: str) -> tuple[float, float]:
        return self._tfidf_score(resume_text, job_text), self._sbert_score(resume_text, job_text)