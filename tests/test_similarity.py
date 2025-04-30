from src.similarity import DualSimilarity

def test_similarity_range():
    sim = DualSimilarity("sentence-transformers/all-MiniLM-L6-v2")
    a, b = sim.score("data science","data engineering")
    assert 0.0 <= a <= 1.0
    assert 0.0 <= b <= 1.0