
import re
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

import streamlit as st
import matplotlib.pyplot as plt
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="ResumeIQ | Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- CUSTOM THEME --------------------

st.markdown("""
<style>
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #17243a !important;
    border: 1.5px solid #c5d5eb !important;
    border-radius: 14px !important;
    padding: 14px !important;
}

.stTextArea label {
    color: #163a5f !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)


# -------------------- SKILLS DATABASE --------------------
SKILLS = [
    "python", "java", "sql", "html", "css", "javascript",
    "machine learning", "deep learning", "data analysis",
    "pandas", "numpy", "scikit-learn", "streamlit", "git",
    "github", "excel", "power bi", "communication",
    "problem solving", "teamwork", "data structures",
    "algorithms", "oop", "rest api", "flask", "django",
    "mongodb", "mysql", "postgresql", "aws", "azure",
    "linux", "docker", "tensorflow", "pytorch",
    "statistics", "tableau", "visualization"
]


# -------------------- SKILL EXTRACTION --------------------
def extract_skills(text):
    text = text.lower()
    found = set()

    for skill in SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            found.add(skill)

    return found


# -------------------- SUGGESTIONS --------------------
def build_suggestions(resume_text, job_text, matched, missing, score):
    suggestions = []
    resume_lower = resume_text.lower()
    job_lower = job_text.lower()

    if missing:
        suggestions.append(
            "Skill gaps: The following job skills were not detected in "
            "your resume: " + ", ".join(sorted(missing)) +
            ". If you genuinely have these skills, include relevant "
            "projects or experience that demonstrate them."
        )
    else:
        suggestions.append(
            "Your resume contains all detected job-description skills "
            "from this application's predefined skill list."
        )

    if score < 40:
        suggestions.append(
            "Job alignment: Review the job requirements and highlight "
            "relevant coursework, projects, internships, and skills."
        )
    elif score < 75:
        suggestions.append(
            "Job alignment: Connect your experience to the role with "
            "specific examples of how you used relevant skills."
        )
    else:
        suggestions.append(
            "Job alignment: Your keyword overlap is strong. Emphasize "
            "relevant achievements and provide evidence of your skills."
        )

    if not re.search(r"\bprojects?\b", resume_lower):
        suggestions.append(
            "Projects: Add a Projects section describing the objective, "
            "technologies used, your contribution, and the result."
        )

    action_verbs = (
        r"\b(built|developed|created|designed|implemented|improved|"
        r"tested|analyzed|analysed|automated|managed|optimized|"
        r"optimised|deployed|maintained)\b"
    )
    if not re.search(action_verbs, resume_lower):
        suggestions.append(
            "Impact: Use accurate action verbs such as developed, "
            "tested, implemented, or automated to describe your work."
        )

    if not re.search(r"\b\d+(?:\.\d+)?\s*%", resume_lower):
        suggestions.append(
            "Achievements: Include measurable results when you have "
            "real evidence. Never invent numbers or achievements."
        )

    if len(resume_text.split()) < 80:
        suggestions.append(
            "Content: Very little resume text was detected. Check PDF "
            "extraction and include education, skills, projects, and "
            "experience where relevant."
        )

    if not re.search(
        r"\b(skills|technical skills|technical expertise)\b",
        resume_lower
    ):
        suggestions.append(
            "Structure: Consider adding a clearly labeled Technical "
            "Skills section."
        )

    if "experience" in job_lower and "experience" not in resume_lower:
        suggestions.append(
            "Experience: Highlight relevant internships, academic "
            "projects, training, or genuine hands-on work."
        )

    return suggestions


# -------------------- PDF REPORT --------------------
def create_pdf_report(
    resume_name, score, matched, missing, job_skills, suggestions
):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="ResumeIQ Analysis Report",
        author="ResumeIQ",
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ResumeIQTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#163A5F"),
        fontSize=20,
        leading=25,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="ResumeIQHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#2256A5"),
        fontSize=12,
        leading=15,
        spaceBefore=12,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="ResumeIQBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=5,
    ))

    story = [
        Paragraph("ResumeIQ Analysis Report", styles["ResumeIQTitle"]),
        Paragraph(
            "Resume Analyzer &amp; Job Matcher",
            ParagraphStyle(
                "ResumeIQSubtitle",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                textColor=colors.HexColor("#61718A"),
                fontSize=10,
                spaceAfter=12,
            ),
        ),
        HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor("#D7E2EC")
        ),
        Spacer(1, 10),
        Paragraph(
            f"<b>Resume:</b> {escape(resume_name)}",
            styles["ResumeIQBody"]
        ),
        Paragraph(
            f"<b>Generated:</b> {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
            styles["ResumeIQBody"]
        ),
        Spacer(1, 8),
    ]

    table_data = [
        ["Metric", "Result"],
        ["Keyword match", f"{score}%"],
        ["Matched skills", str(len(matched))],
        ["Missing skills", str(len(missing))],
        ["Detected job skills", str(len(job_skills))],
    ]

    table = Table(table_data, colWidths=[75 * mm, 75 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7E2EC")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F5F8FB")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(table)

    story.append(Paragraph("Matched Skills", styles["ResumeIQHeading"]))
    story.append(Paragraph(
        escape(", ".join(sorted(matched)) if matched else "No matches found."),
        styles["ResumeIQBody"]
    ))

    story.append(Paragraph("Missing Skills", styles["ResumeIQHeading"]))
    story.append(Paragraph(
        escape(", ".join(sorted(missing)) if missing else "No missing skills."),
        styles["ResumeIQBody"]
    ))

    story.append(Paragraph(
        "Improvement Suggestions", styles["ResumeIQHeading"]
    ))
    for suggestion in suggestions:
        story.append(Paragraph(
            "• " + escape(suggestion), styles["ResumeIQBody"]
        ))

    story.append(Paragraph("Important Note", styles["ResumeIQHeading"]))
    story.append(Paragraph(
        "This application uses predefined keyword matching and "
        "rule-based suggestions. The percentage is not an official ATS "
        "score and does not measure skill proficiency. Add only skills "
        "and achievements that accurately reflect your abilities.",
        styles["ResumeIQBody"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("## 📄 ResumeIQ")
    st.caption("Resume Analyzer & Job Matcher")
    st.markdown("---")
    st.markdown("### 📌 How to use")
    st.markdown(
        "1. Upload a PDF resume or paste resume text.\n\n"
        "2. Paste the target job description.\n\n"
        "3. Click Analyze Resume.\n\n"
        "4. Review the dashboard and suggestions.\n\n"
        "5. Download your PDF report."
    )
    st.markdown("---")
    st.caption("Demo version • Keyword-based analysis")
    st.caption("Use a text-based PDF for best results.")


# -------------------- HEADER --------------------
st.markdown("""
<div class="hero">
    <h1>📄 ResumeIQ</h1>
    <p>Analyze your resume, discover skill gaps, and prepare for your
    target job with confidence.</p>
</div>
""", unsafe_allow_html=True)


# -------------------- INPUT AREA --------------------
left, right = st.columns(2, gap="large")

with left:
    st.subheader("📎 Your Resume")
    uploaded_file = st.file_uploader(
        "Upload your PDF resume",
        type=["pdf"],
        key="resume_pdf",
        help="Text-based PDFs work best. Scanned PDFs may need OCR.",
    )

with right:
    st.subheader("🎯 Target Role")
    st.markdown(
        '<p class="small-muted">Paste the job description to compare '
        'your skills with the role.</p>',
        unsafe_allow_html=True,
    )

extracted_text = ""

if uploaded_file is not None:
    try:
        reader = PdfReader(uploaded_file)
        extracted_text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

        if extracted_text.strip():
            st.success("✅ PDF text extracted successfully.")
        else:
            st.warning(
                "No selectable text found. This may be a scanned PDF; "
                "OCR may be needed."
            )
    except Exception as error:
        st.error(f"Unable to read PDF: {error}")

if "resume_box" not in st.session_state:
    st.session_state.resume_box = ""

if uploaded_file is not None and extracted_text.strip():
    upload_id = f"{uploaded_file.name}:{uploaded_file.size}"

    if st.session_state.get("last_uploaded_file") != upload_id:
        st.session_state.resume_box = extracted_text
        st.session_state.last_uploaded_file = upload_id

resume_text = st.text_area(
    "Resume text (you can edit it)",
    height=230,
    key="resume_box",
    placeholder="Upload a PDF above or paste your resume text here...",
)

job_text = st.text_area(
    "Job description",
    height=230,
    key="job_description",
    placeholder="Paste the job title, required skills, and responsibilities...",
)

analyze_col, clear_col = st.columns([2, 1])

with analyze_col:
    analyze_clicked = st.button(
        "✨ Analyze Resume",
        type="primary",
        use_container_width=True,
    )

with clear_col:
    clear_clicked = st.button(
        "🧹 Clear Analysis",
        use_container_width=True,
    )

if clear_clicked:
    st.session_state.pop("analysis", None)
    st.session_state.resume_box = ""
    st.session_state.job_description = ""
    st.session_state.pop("last_uploaded_file", None)
    st.rerun()


# -------------------- ANALYSIS LOGIC --------------------
if analyze_clicked:
    if not resume_text.strip() or not job_text.strip():
        st.error("Please provide both resume text and job description.")
    else:
        resume_skills = extract_skills(resume_text)
        job_skills = extract_skills(job_text)

        matched = resume_skills & job_skills
        missing = job_skills - resume_skills

        score = (
            round(len(matched) / len(job_skills) * 100)
            if job_skills else 0
        )

        suggestions = build_suggestions(
            resume_text, job_text, matched, missing, score
        )

        st.session_state.analysis = {
            "score": score,
            "matched": sorted(matched),
            "missing": sorted(missing),
            "job_skills": sorted(job_skills),
            "suggestions": suggestions,
            "resume_name": (
                uploaded_file.name
                if uploaded_file is not None
                else "Pasted resume text"
            ),
        }

        if not job_skills:
            st.warning(
                "No skills from the predefined skill list were detected "
                "in the job description. Try including specific technical "
                "skills in the description."
            )


# -------------------- RESULTS DASHBOARD --------------------
if "analysis" in st.session_state:
    analysis = st.session_state.analysis

    score = analysis["score"]
    matched = set(analysis["matched"])
    missing = set(analysis["missing"])
    job_skills = set(analysis["job_skills"])
    suggestions = analysis["suggestions"]

    st.markdown("---")
    st.header("📊 Analysis Dashboard")
    st.caption(
        "This dashboard compares detected keywords. Review the details "
        "rather than relying on the percentage alone."
    )

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("🎯 Keyword Match", f"{score}%")
    metric2.metric("✅ Matched Skills", len(matched))
    metric3.metric("📌 Missing Skills", len(missing))

    st.progress(
        score / 100,
        text=f"{score}% of detected job skill keywords matched"
    )

    chart_col1, chart_col2 = st.columns(2, gap="large")

    with chart_col1:
        st.subheader("📈 Skill Match Overview")

        fig, ax = plt.subplots(figsize=(5, 3.5))
        labels = ["Matched", "Missing"]
        values = [len(matched), len(missing)]

        bars = ax.bar(
            labels,
            values,
            color=["#2E8B75", "#E49A45"],
            width=0.55,
        )

        ax.set_ylabel("Number of skills")
        ax.set_title("Detected job skills")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.25)
        ax.set_axisbelow(True)

        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                str(value),
                ha="center",
                va="bottom",
                fontsize=10,
            )

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with chart_col2:
        st.subheader("📊 Keyword Match Percentage")

        fig2, ax2 = plt.subplots(figsize=(5, 3.5))
        ax2.barh(
            ["Match"], [score],
            color="#3269B1", height=0.42
        )
        ax2.barh(
            ["Match"], [100 - score],
            left=[score], color="#E5EBF4", height=0.42
        )

        ax2.set_xlim(0, 100)
        ax2.set_xlabel("Percent")
        ax2.set_title("Keyword overlap")
        ax2.text(
            min(max(score, 5), 92),
            0,
            f"{score}%",
            va="center",
            ha="center",
            color="white" if score >= 15 else "#17243A",
            fontweight="bold",
        )

        ax2.set_yticks([])
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        ax2.spines["left"].set_visible(False)
        ax2.grid(axis="x", linestyle="--", alpha=0.2)
        ax2.set_axisbelow(True)

        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    # -------------------- SKILL LISTS --------------------
    skill_col1, skill_col2 = st.columns(2, gap="large")

    with skill_col1:
        st.subheader("✅ Matched Skills")
        if matched:
            for skill in sorted(matched):
                st.markdown(f"- `{skill}`")
        else:
            st.info("No matching skill keywords detected.")

    with skill_col2:
        st.subheader("🎯 Missing Skills")
        if missing:
            for skill in sorted(missing):
                st.markdown(f"- `{skill}`")
        else:
            st.success("No missing skills detected from this skill list.")

    # -------------------- SUGGESTIONS --------------------
    st.markdown("---")
    st.header("💡 Resume Improvement Suggestions")

    for index, suggestion in enumerate(suggestions, start=1):
        st.markdown(f"**{index}.** {suggestion}")

    st.warning(
        "Only add skills and achievements that are true for you. "
        "This tool uses a predefined keyword list; it is not an official "
        "ATS score."
    )

    # -------------------- DOWNLOAD REPORT --------------------
    report_data = create_pdf_report(
        analysis["resume_name"],
        score,
        matched,
        missing,
        job_skills,
        suggestions,
    )

    st.download_button(
        label="📥 Download PDF Analysis Report",
        data=report_data,
        file_name="resume_analysis_report.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

else:
    st.markdown("""
    <div class="section-card">
        <h3>✨ Ready to analyze?</h3>
        <p class="small-muted">
            Add your resume and target job description, then click
            <b>Analyze Resume</b> to see your skill match, charts,
            improvement suggestions, and downloadable PDF report.
        </p>
    </div>
    """, unsafe_allow_html=True)

# -------------------- FOOTER --------------------
st.markdown("---")
st.markdown(
    '<p class="small-muted" style="text-align:center;">'
    'ResumeIQ • Resume Analyzer & Job Matcher • Demo Project'
    '</p>',
    unsafe_allow_html=True,
)



