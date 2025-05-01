from functools import cached_property
import spacy, re

# load SpaCy model (disable unnecessary pipes for speed)
nlp = spacy.load("en_core_web_sm", disable=["ner"])
SKILL_PATTERN = re.compile(r"\b([A-Za-z\+]+)\b")

class Resume:
    def __init__(self, raw_text: str):
        self.doc = nlp(raw_text)

    @cached_property
    def tokens(self):
        """List of normalized lemmas (lowercase) excluding stopwords and punctuation."""
        return [t.lemma_.lower() for t in self.doc if not t.is_stop and not t.is_punct]

    @cached_property
    def skills(self):
        """Unique skill tokens matched by SKILL_PATTERN."""
        return sorted({m.group(1) for m in SKILL_PATTERN.finditer(self.doc.text)})

class JobPost(Resume):
    """Inherits token/skill extraction from Resume for job postings."""
    pass