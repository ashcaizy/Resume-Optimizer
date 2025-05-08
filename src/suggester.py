import functools, itertools, torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, TextStreamer
from .parser import Resume, JobPost
from .config import HF_MODEL_GENERATION, TOP_N_GAPS, MAX_NEW_TOKENS

device = "cuda" if torch.cuda.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(HF_MODEL_GENERATION)
model = AutoModelForSeq2SeqLM.from_pretrained(HF_MODEL_GENERATION)
model = model.to(device).eval()

print(f"✅ Tokenizer can handle up to {tok.model_max_length} tokens")

def keyword_gap(resume: Resume, job: JobPost, top_n: int = TOP_N_GAPS):
    missing = (set(job.tokens) - set(resume.tokens)) - set(resume.skills)
    return list(itertools.islice(missing, top_n))

@functools.cache
def _make_streamer():
    return TextStreamer(tok, skip_prompt=True, skip_special_tokens=True)

def suggest_edits(resume_text: str, job_text: str) -> str:
    res, job = Resume(resume_text), JobPost(job_text)

    # 1) Get the raw list of missing keywords
    missing_list = keyword_gap(res, job, top_n=TOP_N_GAPS)
    # 2) Print (or log) it
    print("Missing keywords:", missing_list)

    missing = ", ".join(keyword_gap(res, job)) or "NONE"


    # change the prompt to be more specific -- give it one example, make it more free for 
    # it to edit the resume text (less restrictive)

    prompt = f"""
You are a resume assistant. Rewrite bullets to include missing keywords.
Resume:
{resume_text}
Keywords: {missing}
### UPDATED RESUME
"""
    inputs = tok(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=tok.model_max_length,    # explicitly 512
    ).to(device)

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=0.3,
            top_p=0.9,
        )
        generated = tok.decode(outputs[0], skip_special_tokens=True)
        print("📝 RAW GENERATED:\n", generated)
    text = tok.decode(outputs[0], skip_special_tokens=True)
    return text.split("### UPDATED RESUME")[-1].strip()
