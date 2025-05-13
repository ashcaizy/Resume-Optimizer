from fastapi import FastAPI, UploadFile, Form
from pathlib import Path
from src.data_loader import read_file
from src.similarity import DualSimilarity
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from PyPDF2 import PdfReader
from fastapi import HTTPException
from src.data_loader import read_file



from fastapi import FastAPI, UploadFile, HTTPException
from pathlib import Path
from src.data_loader import read_file
from src.similarity import DualSimilarity
from src.suggester import suggest_resume  # Import the suggester function
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

app = FastAPI()

# Load the trained model and tokenizer
model_path = "models/resume-fit"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)




@app.post("/analyze/")
async def analyze(resume: UploadFile, job: UploadFile):
    # Save uploaded files temporarily
    resume_path = Path(f"temp_{resume.filename}")
    job_path = Path(f"temp_{job.filename}")

    try:
        # Write the uploaded files to disk
        with open(resume_path, "wb") as f:
            f.write(await resume.read())
        with open(job_path, "wb") as f:
            f.write(await job.read())

        # Use read_file to parse the files
        resume_text = read_file(resume_path)
        job_text = read_file(job_path)

        # Debugging: Print extracted text
        print(f"Extracted Resume Text (first 500 chars): {resume_text[:500]}")
        print(f"Extracted Job Text (first 500 chars): {job_text[:500]}")

        # Predict fit score
        tf, sb = DualSimilarity(hf_model="sentence-transformers/all-MiniLM-L6-v2").score(resume_text, job_text)

        inputs = tokenizer(
            resume_text,
            job_text,
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors="pt",
        )
        with torch.no_grad():
            
            outputs = model(**inputs)
            logits = outputs.logits
            predicted_class = torch.argmax(logits, dim=1).item()

        # Generate suggestions using suggester.py
        markdown, keywords = suggest_resume(resume_text, job_text)

        # Map predicted_class to descriptive string
        if predicted_class == 0:
            fit_level = "Not a Fit"
        elif predicted_class == 1:
            fit_level = "Potential Fit"
        else:
            fit_level = "Good Fit"

        # Return the response
        return {
            "tf_idf_score": tf,
            "sbert_score": sb,
            "predicted_class": predicted_class,  # Numeric class
            "fit_level": fit_level,  # Descriptive string
            "suggestions_markdown": markdown,  # Include markdown in the response
            "missing_keywords": keywords,     # Include missing keywords
        }

    finally:
        # Clean up temporary files
        if resume_path.exists():
            resume_path.unlink()
        if job_path.exists():
            job_path.unlink()