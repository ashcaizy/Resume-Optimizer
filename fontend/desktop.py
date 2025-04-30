import streamlit as st
import os

st.set_page_config(
    page_title="Resume Optimizer – New Scan",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---- Top bar with local logo.png ----
logo_col, _, premium_col = st.columns([2, 6, 1])
with logo_col:
    # assumes logo.png is in the same folder where you run streamlit
    logo_path = os.path.join(os.getcwd(), "logo.png")
    st.image(logo_path, width=400)
with premium_col:
    st.button("Contact Us")

st.markdown("---")

# ---- New Scan UI ----
st.header("New Improvement")
col_resume, col_jd = st.columns(2, gap="large")

with col_resume:
    st.subheader("Resume")
    resume_text = st.text_area(
        label="Paste resume text…",
        height=300,
        placeholder="Paste resume text here…"
    )
    st.file_uploader(
        label="Drag & Drop or Upload",
        type=["pdf", "docx", "txt"]
    )

with col_jd:
    st.subheader("Job Description")
    jd_text = st.text_area(
        label="Copy and paste job description here",
        height=300,
        placeholder="Paste job description here…"
    )

# ---- Scan button ----
if st.button("Scan", use_container_width=True):
    st.info("🔍 Scanning… (frontend only)")
