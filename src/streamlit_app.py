import streamlit as st
from pathlib import Path
from src.data_loader import read_file
from src.similarity import DualSimilarity
from src.suggester import suggest_edits
from src.config import HF_MODEL_EMBED
from src.job_scraper import fetch as fetch_job

st.set_page_config(page_title="Resume Optimizer", layout="wide")
st.title("📄 Resume Optimizer")

col1, col2 = st.columns(2)
with col1:
    res_f = st.file_uploader("Upload Resume", type=["pdf","docx","txt"])
with col2:
    job_f = st.file_uploader("Upload Job Description", type=["pdf","docx","txt"])
    url  = st.text_input("…or paste job URL")

if res_f and (job_f or url):
    res_text = read_file(res_f)
    job_text = fetch_job(url) if url else read_file(job_f)

    tf, sb = DualSimilarity(HF_MODEL_EMBED).score(res_text, job_text)
    st.success(f"**TF-IDF:** {tf:.3f}   **SBERT:** {sb:.3f}")

    if st.button("Suggest Improvements"):
        with st.spinner("Generating…"):
            out = suggest_edits(res_text, job_text)
        st.download_button("Download .md", out, file_name="improved_resume.md")
        st.markdown(out)