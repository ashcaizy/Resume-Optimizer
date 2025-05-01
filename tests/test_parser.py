from src.parser import Resume

def test_tokenization_and_skills():
    doc = Resume("Python developer. C++ guru.")
    assert "python" in doc.tokens
    assert "developer" in doc.tokens
    assert any(s.lower().startswith("c++") for s in doc.skills)