import spacy, re
from functools import cached_property

nlp = spacy.load("en_core_web_sm", disable=["ner"])
SKILL_PATTERN = re.compile(r"\b([A-Za-z\+]+)\b")

class Resume:
    def __init__(self, raw_text: str):
        self.doc = nlp(raw_text)

    @cached_property
    def tokens(self):
        return [t.lemma_.lower() for t in self.doc if not t.is_stop and not t.is_punct]

    @cached_property
    def skills(self):
        return sorted({m.group(1) for m in SKILL_PATTERN.finditer(self.doc.text)})

class JobPost(Resume):
    pass