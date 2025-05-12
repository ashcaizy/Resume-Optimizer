import streamlit as st
import requests
import os
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Optimizer – New Scan",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Session state ────────────────────────────────────────────────────────────
if "scan_done" not in st.session_state:
    st.session_state.scan_done = False

# ── Scan callback: save inputs to disk ─────────────────────────────────────────
def start_scan(resume_text, uploaded_file, jd_text):
    # Ensure the uploads directory exists
    os.makedirs("uploads", exist_ok=True)

    # Save pasted resume text
    if resume_text:
        st.write("Saving resume text to file...")
        with open(os.path.join("uploads", "resume_text.txt"), "w", encoding="utf-8") as f:
            f.write(resume_text)

    # Save uploaded resume file
    resume_path = None
    if uploaded_file is not None:
        st.write("Saving uploaded resume file...")
        resume_path = os.path.join("uploads", uploaded_file.name)  # Save with original name
        with open(resume_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    # Save job description text
    if jd_text:
        st.write("Saving job description to file...")
        job_path = os.path.join("uploads", "job_description.txt")
        with open(job_path, "w", encoding="utf-8") as f:
            f.write(jd_text)
    else:
        st.error("Please provide a job description.")
        return

    # Send the resume and job description to the backend API
    if resume_path:
        st.write("Sending files to backend API...")
        with open(resume_path, "rb") as resume_file, open(job_path, "rb") as job_file:
            response = requests.post(
                "http://127.0.0.1:8000/analyze/",
                files={"resume": resume_file, "job": job_file},
            )

        # Parse the response
        if response.status_code == 200:
            result = response.json()
            st.session_state.result = result  # Store the result in session state
            st.session_state.scan_done = True  # Set scan_done to True
            st.write("### Analysis Results")
            st.write(f"**TF-IDF Score:** {result['tf_idf_score']:.3f}")
            st.write(f"**SBERT Score:** {result['sbert_score']:.3f}")
            st.write(f"**Predicted Compatibility Class:** {result['predicted_class']}")
        else:
            st.error("Error: Could not process the request.")
    else:
        st.error("Please upload a resume file.")
   

# ── Top bar ───────────────────────────────────────────────────────────────────
logo_col, _, premium_col = st.columns([2, 6, 1])
with logo_col:
    logo_path = os.path.join(os.getcwd(), "logo.png")
    st.image(logo_path, width=400)
with premium_col:
    st.button("Contact Us")

st.markdown("---")

# ── Gauge helper ──────────────────────────────────────────────────────────────
def make_gauge(value: float):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": "%", "font": {"size": 36}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#40c057"},
                "steps": [
                    {"range": [0, 50],  "color": "#ff922b"},
                    {"range": [50, 75], "color": "#40c057"},
                    {"range": [75, 100],"color": "#228be6"},
                ],
                "threshold": {
                    "line": {"color": "gray", "width": 4},
                    "thickness": 0.75,
                    "value": value,
                },
            },
        )
    )
    fig.update_layout(margin={"t":0,"b":0,"l":0,"r":0}, height=250)
    return fig

# ── New Improvement form ──────────────────────────────────────────────────────
if not st.session_state.scan_done:
    st.header("New Improvement")
    col_resume, col_jd = st.columns(2, gap="large")

    with col_resume:
        st.subheader("Resume")
        resume_text = st.text_area(
            label="Paste resume text OR Upload File below", 
            height=300,
            placeholder="Paste resume text here…",
        )
        uploaded_file = st.file_uploader(
            label="Drag & Drop or Upload",
            type=["pdf", "docx", "txt"],
        )

    with col_jd:
         st.subheader("Job Description")
         jd_text = st.text_area(
            "Copy and paste job description or URL link here",
            height=300,
            placeholder="Paste job description here…",
        )

    st.button(
        "Start Scanning",
        on_click=start_scan,
        args=(resume_text, uploaded_file, jd_text),
        use_container_width=True
    )

# ── Results page ──────────────────────────────────────────────────────────────
else:
    hdr, actions = st.columns([8,2])
    with hdr:
        st.markdown("## Resume Scan Results")
        job_title = st.text_input("", "Please Input Job Title", label_visibility="collapsed")
    with actions:
        st.button("Track", use_container_width=True)
        st.button("Print", use_container_width=True)

    st.markdown("---")

    left, right = st.columns([2,5], gap="large")

    # — Left panel
    with left:
        st.plotly_chart(make_gauge(46), use_container_width=True)
        st.button("⚡ Power Edit", use_container_width=True)

        def cat(name, pct, issues):
            st.markdown(f"**{name}** — {issues} issues to fix")
            st.progress(pct / 100)

        cat("Experiences Match", 75, 2)
        cat("Education Match", 20, 14)
        cat("Skills Match", 30, 5)

    # — Right panel
    with right:
        st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab"] {
        font-size: 20px !important; /* Force the font size */
        font-weight: bold !important; /* Force bold text */
    }
    </style>
    """,
    unsafe_allow_html=True
)
        tabs = st.tabs(["    Resume Job Match    ", "    Suggested Improvements"])

        with tabs[0]:

            st.markdown(
                "### AI Model Match"
                "<span style='background:#495057;color:white;"
                "padding:4px 8px;border-radius:4px;font-size:0.8rem;'>IMPORTANT</span>",
                unsafe_allow_html=True
            )
            st.markdown(
                "This section shows how well your previous experiences fit in this new role using our trianed AI model."
            )

            c1, c2 = st.columns([2,8])
            with c1:
                st.markdown("**Match Class**")
                st.markdown("**Project Match**")
            with c2:
                # Display the Predicted Compatibility Class
                if "result" in st.session_state:
                    predicted_class = st.session_state.result["predicted_class"]
                    st.markdown(f"**Predicted Compatibility Class:** {predicted_class}")
                else:
                    st.markdown("No results available yet.")

                st.markdown("✅ You mentioned verb like led, spearheaded.")
                st.markdown("❌ You did not mention related project to product development.")


            c1, c2 = st.columns([2,8])
            with c1:
                st.markdown("**Summary**")
            with c2:
                st.markdown(
                    "⚠️ You provided good experience in terms of action but not related projects. We suggest you add more information"
                )

            st.markdown("---")

            st.markdown(
                "### Similarity Match"
                "<span style='background:#495057;color:white;"
                "padding:4px 8px;border-radius:4px;font-size:0.8rem;'>IMPORTANT</span>",
                unsafe_allow_html=True
            )
            st.markdown(
                "This section shows how well your current/ previous Education fit in this new role."
            )
            c3, c4 = st.columns([2,8])

            with c3:
                st.markdown("**Degree Level Match**")
                st.markdown("**Major Match**")
                
            with c4:
                st.markdown("✅ Your education matches the preferred (BS, MS, BA, BS) education listed in the job description.")
                st.markdown("✅ Your Major matches the preferred (Computer Science, Math, Engineering) area of studies listed in the job description.")

            st.markdown("---")

            st.markdown(
                "### BSERT Score Match"
                "<span style='background:#495057;color:white;"
                "padding:4px 8px;border-radius:4px;font-size:0.8rem;'>IMPORTANT</span>",
                unsafe_allow_html=True
            )
            st.markdown(
                "This section shows how well your hard and soft skills fit in this new role. Tip: Match the skills in your resume to the exact spelling in the job description. Prioritize skills that appear most frequently in the job description."
            )
            c5, c6 = st.columns([2,8])

            with c5:
                st.markdown("**Hard Skills Match**")
                st.markdown(
                    "✅ Product Management<br>"
                    "✅ Good<br>"
                    "❌ Python<br>"
                    "❌ Excel<br>"
                    "✅ CSS",
                    unsafe_allow_html=True
                )

            with c6:
                st.markdown("**Soft Skills Match**")
                st.markdown(
                    "✅ Communication<br>"
                    "✅ Teamwork<br>"
                    "❌ Leadership<br>"
                    "❌ Problem-Solving<br>"
                    "✅ Adaptability",
                    unsafe_allow_html=True
    )

        with tabs[1]:
            
            st.markdown(
                "<h2 style='font-size:26px; font-weight:bold; margin-bottom:0;'>How to Improve your Resume </h2>",
                unsafe_allow_html=True
            )
            st.markdown(
                "_(Here you could highlight keywords from the job description and compare them to your resume.)_"
            )
            st.markdown("### Suggested Improvements")
            st.markdown(st.session_state.result["suggestions_markdown"], unsafe_allow_html=True)
