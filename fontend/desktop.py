import streamlit as st
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

def start_scan():
    st.session_state.scan_done = True

# ── Top bar ──────────────────────────────────────────────────────────────────
logo_col, _, premium_col = st.columns([2, 6, 1])
with logo_col:
    logo_path = os.path.join(os.getcwd(), "logo.png")
    st.image(logo_path, width=400)
with premium_col:
    st.button("Contact Us")

st.markdown("---")

# ── Gauge helper ───────────────────────────────────────────────────────────────
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

# ── New Improvement form ─────────────────────────────────────────────────────
if not st.session_state.scan_done:
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

    st.button(
        "Start Scanning",
        on_click=start_scan,
        use_container_width=True
    )

# ── Results page ─────────────────────────────────────────────────────────────
else:
    # — Header + actions
    hdr, actions = st.columns([8,2])
    with hdr:
        st.markdown("##### Resume scan results")
        job_title = st.text_input("", "Tiktok - Product Manager")
    with actions:
        st.button("Track", use_container_width=True)
        st.button("Print", use_container_width=True)

    st.markdown("---")

    left, right = st.columns([2,5], gap="large")

    # — Left panel
    with left:
        st.plotly_chart(make_gauge(46), use_container_width=True)
        # (no rescan implementation needed)
        st.button("⚡ Power Edit", use_container_width=True)

        def cat(name, pct, issues):
            st.markdown(f"**{name}** — {issues} issues to fix")
            st.progress(pct / 100)

        cat("Searchability", 75, 2)
        cat("Hard Skills", 20, 14)
        cat("Soft Skills", 30, 5)
        cat("Recruiter Tips", 60, 2)

    # — Right panel
    with right:
        tabs = st.tabs(["Resume", "Job Description"])

        with tabs[0]:
            st.markdown(
                "## Searchability  "
                "<span style='background:#495057;color:white;"
                "padding:4px 8px;border-radius:4px;font-size:0.8rem;'>IMPORTANT</span>",
                unsafe_allow_html=True
            )
            st.markdown(
                "An ATS (Applicant Tracking System) is software used by 90% of companies and recruiters…  "
                "**Tip:** Fix the red Xs to ensure your resume is easily searchable by recruiters and parsed correctly by the ATS."
            )

            c1, c2 = st.columns([2,8])
            with c1:
                st.markdown("**Contact Information**")
            with c2:
                st.markdown("✔ You provided your physical address.")
                st.markdown("✔ You provided your email.")
                st.markdown("✔ You provided your phone number.")
            st.markdown("---")

            c1, c2 = st.columns([2,8])
            with c1:
                st.markdown("**Summary**")
            with c2:
                st.markdown(
                    "⚠️ We did not find a summary section on your resume. "
                    "A summary helps recruiters grasp your qualifications quickly."
                )

        with tabs[1]:
            st.markdown(
                "_(Here you could highlight keywords from the job description and compare them to your resume.)_"
            )
