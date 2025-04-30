import streamlit as st

st.set_page_config(
    page_title="Jobscan",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- Top bar ----
logo, spacer, premium = st.columns([1, 8, 1])
with logo:
    st.image("https://raw.githubusercontent.com/your‐repo/logo.png", width=120)  # replace with your logo URL or local file

# ---- Sidebar navigation ----
st.sidebar.markdown("## Jobscan")
page = st.sidebar.radio(
    "",
    ["Dashboard", "LinkedIn Scan", "Job Tracker", "Find Jobs",
     "Resume Builder", "Resume Manager", "Scan History", "New Scan"],
    index=7
)

# ---- Page content ----
if page == "New Scan":
    st.header("New scan")
    col_resume, col_jd = st.columns(2, gap="large")

    with col_resume:
        st.subheader("Resume")
        resume_text = st.text_area(
            "Paste resume text…", 
            height=300, 
            placeholder="Paste resume text here…"
        )
        uploaded = st.file_uploader(
            "Drag & Drop or Upload", 
            type=["pdf", "docx", "txt"]
        )

    with col_jd:
        st.subheader("Job Description")
        jd_text = st.text_area(
            "Copy and paste job description here", 
            height=300, 
            placeholder="Paste job description here…"
        )

    scan_btn = st.button("Scan", use_container_width=True)
    if scan_btn:
        st.info("🔍 Scanning… (this is just the frontend scaffold)")
else:
    st.header(page)
    st.write(f"This is the **{page}** view. Build out each page as needed!")

