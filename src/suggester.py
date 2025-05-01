import functools, itertools, torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, TextStreamer
from .parser import Resume, JobPost
from .config import HF_MODEL_GENERATION, TOP_N_GAPS, MAX_NEW_TOKENS

device = "cuda" if torch.cuda.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(HF_MODEL_GENERATION)
model = AutoModelForSeq2SeqLM.from_pretrained(HF_MODEL_GENERATION)
model = model.to(device).eval()

def keyword_gap(resume: Resume, job: JobPost, top_n: int = TOP_N_GAPS):
    missing = (set(job.tokens) - set(resume.tokens)) - set(resume.skills)
    return list(itertools.islice(missing, top_n))

@functools.cache
def _make_streamer():
    return TextStreamer(tok, skip_prompt=True, skip_special_tokens=True)

def suggest_edits(resume_text: str, job_text: str) -> str:
    res, job = Resume(resume_text), JobPost(job_text)
    missing = ", ".join(keyword_gap(res, job)) or "NONE"

    prompt = f"""
You are a resume-optimizing assistant.
Add the MISSING_KEYWORDS **without deleting or paraphrasing any existing bullet**.
Preserve all line breaks exactly. Append new bullets where sensible.

RESUME:
{resume_text}

MISSING_KEYWORDS: {missing}

### UPDATED RESUME
"""
    inputs = tok(prompt, return_tensors="pt", truncation=True).to(device)
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=0.3,
            top_p=0.9,
        )
    text = tok.decode(outputs[0], skip_special_tokens=True)
    return text.split("### UPDATED RESUME")[-1].strip()
