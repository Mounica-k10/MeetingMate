import os
import sqlite3
import json
import tempfile
import hashlib
import secrets
import io
from pathlib import Path
from datetime import date, time

import streamlit as st
from dotenv import load_dotenv
from google import genai


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="MeetingMate | AI Meeting Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = "gemini-3.1-flash-lite"
DB_NAME = "meetingmate.db"

if not API_KEY:
    st.error("Gemini API key not found. Please check your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)


# ==================================================
# 2. PROFESSIONAL CSS DESIGN
# ==================================================

st.markdown("""
<style>

/* Main application */
.stApp {
    background: linear-gradient(135deg, #0b1020 0%, #11182d 55%, #15152b 100%);
    color: #f4f5ff;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* Main content spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

/* Headings */
h1 {
    color: #ffffff !important;
    font-size: 2.25rem !important;
    font-weight: 800 !important;
    letter-spacing: -1px;
}

h2, h3, h4 {
    color: #f1f0ff !important;
    font-weight: 700 !important;
}

/* Paragraphs and labels */
p, label, .stMarkdown {
    color: #d5d9eb;
}

small {
    color: #aab2ca !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #101629;
    border-right: 1px solid rgba(148, 163, 184, 0.16);
}

section[data-testid="stSidebar"] > div {
    padding: 1.4rem 1rem;
}

/* Sidebar text */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    font-size: 17px !important;
    font-weight: 600 !important;
}

/* Sidebar radio navigation */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 9px;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: #18223a;
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 11px;
    padding: 12px 13px;
    transition: all 0.2s ease;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: #263451;
    border-color: #8b5cf6;
}

/* Buttons */
.stButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(110deg, #7657ed, #a855f7);
    color: white !important;
    border: none;
    border-radius: 10px;
    min-height: 43px;
    font-weight: 700;
    transition: all 0.2s ease;
    box-shadow: 0 5px 18px rgba(124, 87, 237, 0.17);
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: linear-gradient(110deg, #8b6cf5, #bd6cff);
    border: none;
    transform: translateY(-2px);
}

/* Inputs */
.stTextInput input,
.stTextArea textarea,
.stDateInput input,
.stTimeInput input,
.stSelectbox div[data-baseweb="select"] {
    background: #18223a !important;
    color: white !important;
    border: 1px solid #35415e !important;
    border-radius: 9px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #9b75ff !important;
    box-shadow: 0 0 0 1px #9b75ff !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #18223a;
    border: 1px dashed #8065df;
    border-radius: 13px;
    padding: 15px;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1c2945, #20203e);
    border: 1px solid rgba(167, 139, 250, 0.22);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

/* Metric text */
[data-testid="stMetricLabel"] {
    color: #b8c0d8 !important;
    font-size: 15px !important;
}

[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 30px !important;
    font-weight: 800 !important;
}

/* Containers and expanders */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(28, 39, 65, 0.75);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 14px;
}

details {
    background: #18223a;
    border: 1px solid #35415e;
    border-radius: 11px;
    padding: 5px 10px;
}

/* Tabs */
button[data-baseweb="tab"] {
    color: #c8cce0 !important;
    font-size: 15px !important;
}

/* Dividers */
hr {
    border-color: rgba(148, 163, 184, 0.2) !important;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Chat */
[data-testid="stChatMessage"] {
    background: #1a2540;
    border: 1px solid rgba(148, 163, 184, 0.13);
    border-radius: 13px;
    padding: 12px;
}

/* Login card */
.auth-card {
    background: linear-gradient(145deg, #182440, #211d3c);
    border: 1px solid rgba(167, 139, 250, 0.25);
    border-radius: 20px;
    padding: 30px;
    box-shadow: 0 15px 50px rgba(0,0,0,0.25);
}

/* Brand */
.brand-title {
    font-size: 30px;
    font-weight: 850;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #bba8ff, #e1b8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.brand-subtitle {
    color: #aeb8d0;
    font-size: 14px;
    line-height: 1.6;
}

/* Welcome banner */
.hero {
    background: linear-gradient(115deg, #28245a, #40266a, #273b68);
    border: 1px solid rgba(190, 160, 255, 0.3);
    border-radius: 18px;
    padding: 28px;
    margin-bottom: 25px;
}

.hero h2 {
    font-size: 27px;
    margin-bottom: 8px;
}

.hero p {
    color: #d8d5f5;
    margin-bottom: 0;
}

/* =========================================
   PREMIUM UI ENHANCEMENTS
========================================= */

/* Smooth page entrance */
.main .block-container {
    animation: fadeIn 0.6s ease-in-out;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(14px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Wider, more attractive welcome banner */
.hero {
    background:
        radial-gradient(circle at top right,
        rgba(168, 85, 247, 0.25), transparent 45%),
        linear-gradient(120deg, #29245c, #45266d, #273c70);
    border: 1px solid rgba(190, 160, 255, 0.4);
    border-radius: 20px;
    padding: 38px;
    margin-bottom: 30px;
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.22);
    transition: all 0.3s ease;
}

.hero:hover {
    transform: translateY(-3px);
    box-shadow: 0 18px 40px rgba(124, 87, 237, 0.2);
}

.hero h2 {
    font-size: 30px !important;
    font-weight: 800 !important;
    margin-bottom: 14px;
}

.hero p {
    font-size: 16px;
    line-height: 1.8;
}

/* Wider and cleaner authentication form */
div[data-testid="stForm"] {
    background: rgba(25, 35, 59, 0.78);
    border: 1px solid rgba(167, 139, 250, 0.3);
    border-radius: 17px;
    padding: 26px;
    box-shadow: 0 14px 35px rgba(0, 0, 0, 0.2);
}

/* Authentication headings */
.main h2,
.main h3 {
    letter-spacing: -0.5px;
}

/* Larger input fields */
.stTextInput input {
    min-height: 49px;
    font-size: 15px !important;
    padding: 12px 14px !important;
}

/* Input focus glow */
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.18) !important;
}

/* More polished buttons */
.stButton > button,
.stFormSubmitButton > button {
    min-height: 49px;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.2px;
    border-radius: 11px;
    transition: all 0.25s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 9px 24px rgba(168, 85, 247, 0.3);
}

/* Metric card hover */
[data-testid="stMetric"] {
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(139, 92, 246, 0.2);
}

/* Sidebar navigation animation */
section[data-testid="stSidebar"]
div[role="radiogroup"] label {
    transition: all 0.25s ease;
}

section[data-testid="stSidebar"]
div[role="radiogroup"] label:hover {
    transform: translateX(5px);
}

/* Expander hover */
details {
    transition: border-color 0.25s ease;
}

details:hover {
    border-color: #9875ff;
}

/* Responsive layout */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem !important;
    }

    .hero {
        padding: 22px;
    }

    .hero h2 {
        font-size: 23px !important;
    }

    div[data-testid="stForm"] {
        padding: 17px;
    }
}

/* Hide Streamlit footer */
footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. DATABASE
# ==================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            transcript TEXT NOT NULL,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            meeting_date TEXT NOT NULL,
            meeting_time TEXT NOT NULL,
            participants TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task TEXT NOT NULL,
            assignee TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    for table in ("meetings", "schedules", "tasks"):

        columns = [
            row[1]
            for row in cur.execute(f"PRAGMA table_info({table})")
        ]

        if "user_id" not in columns:
            cur.execute(
                f"ALTER TABLE {table} ADD COLUMN user_id INTEGER"
            )

    conn.commit()
    conn.close()


def hash_password(password, salt=None):

    salt = salt or secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        200000
    ).hex()

    return password_hash, salt


def verify_password(password, stored_hash, salt):

    calculated_hash, _ = hash_password(password, salt)

    return secrets.compare_digest(
        calculated_hash,
        stored_hash
    )


initialize_database()


# ==================================================
# 4. SESSION STATE
# ==================================================

defaults = {
    "analysis_result": None,
    "analysis_title": "",
    "analysis_transcript": "",
    "chat_history": [],
    "user_id": None,
    "user_name": None,
    "user_email": None,
    "auth_mode": "Sign In"
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value
        # ==================================================
# 5. GEMINI FUNCTION
# ==================================================

def ask_gemini(prompt):

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text.strip()


# ==================================================
# 6. FILE EXTRACTION
# ==================================================

def extract_uploaded_content(uploaded_file):

    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    if file_name.endswith(".txt"):

        return file_bytes.decode(
            "utf-8",
            errors="replace"
        )

    if file_name.endswith(".pdf"):

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))

        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        ).strip()

    if file_name.endswith(".docx"):

        from docx import Document

        document = Document(io.BytesIO(file_bytes))

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        ).strip()

    audio_extensions = (
        ".mp3", ".wav", ".m4a",
        ".aac", ".flac", ".ogg"
    )

    if file_name.endswith(audio_extensions):

        suffix = Path(file_name).suffix
        temp_path = None

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as temp_file:

                temp_file.write(file_bytes)
                temp_path = temp_file.name

            uploaded_audio = client.files.upload(
                file=temp_path
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    uploaded_audio,
                    (
                        "Transcribe the audio accurately. "
                        "Return only the spoken words as a meeting transcript. "
                        "Preserve speaker names when clearly spoken. "
                        "Do not summarize or invent missing words."
                    )
                ]
            )

            if not response.text:
                raise ValueError("Gemini could not transcribe this audio.")

            return response.text.strip()

        finally:

            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    raise ValueError(
        "Unsupported file type. Upload PDF, DOCX, TXT, or audio."
    )


# ==================================================
# 7. MEETING ANALYSIS
# ==================================================

def analyze_meeting(transcript):

    prompt = f"""
You are an AI meeting analysis assistant.

Analyze the following meeting transcript.

Use these sections:

1. Executive Summary
2. Key Discussion Points
3. Decisions
4. Action Items

For action items, include the task, responsible person,
and deadline only when explicitly mentioned.

Rules:
- Do not invent information.
- Do not invent participants or decisions.
- If a responsible person is unclear, write Not specified.
- If a deadline is missing, write Not specified.
- Preserve the actual meaning of the discussion.

Meeting Transcript:
{transcript}
"""

    return ask_gemini(prompt)


# ==================================================
# 8. TASK EXTRACTION
# ==================================================

def extract_tasks(transcript):

    prompt = f"""
You are an AI task extraction assistant.

Extract all action items from the transcript.

Return ONLY valid JSON in this format:

[
    {{
        "task": "Task description",
        "assignee": "Person responsible",
        "due_date": "Deadline"
    }}
]

Rules:
- Extract only explicitly assigned tasks.
- Do not invent names or deadlines.
- Missing assignee: Not specified.
- Missing deadline: Not specified.
- Return [] if there are no action items.

Transcript:
{transcript}
"""

    response = ask_gemini(prompt)

    try:

        cleaned = response.replace("```json", "").replace("```", "").strip()
        tasks = json.loads(cleaned)

        return tasks if isinstance(tasks, list) else []

    except json.JSONDecodeError:

        return []


# ==================================================
# 9. AUTHENTICATION FUNCTIONS
# ==================================================

def authenticate_user(email, password):

    conn = get_connection()

    row = conn.execute("""
        SELECT id, name, email, password_hash, password_salt
        FROM users
        WHERE email = ? COLLATE NOCASE
    """, (email.strip(),)).fetchone()

    conn.close()

    if row and verify_password(password, row[3], row[4]):

        return {
            "id": row[0],
            "name": row[1],
            "email": row[2]
        }

    return None


def create_user(name, email, password):

    password_hash, salt = hash_password(password)

    conn = get_connection()

    try:

        cur = conn.execute("""
            INSERT INTO users
            (name, email, password_hash, password_salt)
            VALUES (?, ?, ?, ?)
        """, (
            name.strip(),
            email.strip().lower(),
            password_hash,
            salt
        ))

        conn.commit()

        return cur.lastrowid

    finally:

        conn.close()


# ==================================================
# 10. AUTHENTICATION SCREEN
# ==================================================

if not st.session_state.user_id:

    st.markdown("""
    <div style="text-align:center; padding-top:25px; padding-bottom:22px;">
        <div style="font-size:62px; margin-bottom:5px;">🤖</div>
        <div class="brand-title" style="font-size:38px;">
            MeetingMate
        </div>
        <div class="brand-subtitle" style="font-size:15px;">
            Your intelligent AI-powered meeting companion
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Use almost the full page width instead of a narrow centered column.
    left_space, auth_col, right_space = st.columns(
        [0.18, 3.64, 0.18],
        gap="large"
    )

    with auth_col:

        st.markdown("""
        <div class="hero">
            <div style="font-size:13px; font-weight:700; letter-spacing:1.5px;
                        color:#c9b8ff; margin-bottom:10px;">
                YOUR AI-POWERED WORKSPACE
            </div>
            <h2>Meet smarter. Work better. ✨</h2>
            <p>
                Turn meeting conversations into clear summaries,
                important decisions, and actionable tasks — all in one place.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Both authentication buttons remain visible.
        sign_col, create_col = st.columns(2, gap="medium")

        with sign_col:

            if st.button(
                "🔐  Sign In",
                key="signin_mode",
                use_container_width=True
            ):

                st.session_state.auth_mode = "Sign In"

        with create_col:

            if st.button(
                "✨  Create Account",
                key="create_mode",
                use_container_width=True
            ):

                st.session_state.auth_mode = "Create Account"

        st.markdown("---")

        if st.session_state.auth_mode == "Sign In":

            st.subheader("Welcome Back")
            st.caption("Sign in to continue to your personal workspace.")

            with st.form("login_form"):

                login_email = st.text_input(
                    "Email Address",
                    placeholder="you@example.com"
                )

                login_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )

                login_submitted = st.form_submit_button(
                    "Sign In →",
                    type="primary",
                    use_container_width=True
                )

            if login_submitted:

                if not login_email.strip() or not login_password:

                    st.warning("Enter your email address and password.")

                else:

                    user = authenticate_user(
                        login_email,
                        login_password
                    )

                    if user:

                        st.session_state.user_id = user["id"]
                        st.session_state.user_name = user["name"]
                        st.session_state.user_email = user["email"]
                        st.session_state.chat_history = []

                        st.rerun()

                    else:

                        st.error("Invalid email address or password.")

        else:

            st.subheader("Create Your Account")
            st.caption("Set up your personal MeetingMate workspace.")

            with st.form("register_form"):

                register_name = st.text_input(
                    "Full Name",
                    placeholder="Your name"
                )

                register_email = st.text_input(
                    "Email Address",
                    placeholder="you@example.com"
                )

                register_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters"
                )

                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password"
                )

                register_submitted = st.form_submit_button(
                    "Create Account →",
                    type="primary",
                    use_container_width=True
                )

            if register_submitted:

                if (
                    not register_name.strip()
                    or not register_email.strip()
                    or not register_password
                ):

                    st.warning("Please complete all fields.")

                elif (
                    "@" not in register_email
                    or "." not in register_email.rsplit("@", 1)[-1]
                ):

                    st.warning("Enter a valid email address.")

                elif len(register_password) < 8:

                    st.warning("Password must contain at least 8 characters.")

                elif register_password != confirm_password:

                    st.warning("Passwords do not match.")

                else:

                    try:

                        new_user_id = create_user(
                            register_name,
                            register_email,
                            register_password
                        )

                        st.session_state.user_id = new_user_id
                        st.session_state.user_name = register_name.strip()
                        st.session_state.user_email = register_email.strip().lower()
                        st.session_state.chat_history = []

                        st.success("Account created successfully!")
                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error("An account with this email already exists.")

    st.stop()
    # ==================================================
# 11. SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:

    st.markdown("""
    <div style="text-align:center; padding:12px 0 22px;">
        <div style="font-size:40px;">🤖</div>
        <div class="brand-title" style="font-size:25px;">
            MeetingMate
        </div>
        <div class="brand-subtitle">AI Meeting Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 👤 Your Workspace")

    st.markdown(
        f"**{st.session_state.user_name}**"
    )

    st.caption(st.session_state.user_email)

    st.divider()

    st.markdown("### 🧭 MAIN MENU")

    navigation_options = [
        "🏠  Dashboard",
        "📄  Analyze Meeting",
        "📚  Meeting History",
        "📅  Schedule Meeting",
        "💬  AI Chat Assistant",
        "✅  Task Management"
    ]

    selected_page = st.radio(
        "Navigate",
        navigation_options,
        label_visibility="collapsed"
    )

    page = selected_page.split("  ", 1)[1]

    st.divider()

    st.markdown("""
    <div style="background:#1b2944; padding:13px; border-radius:10px;">
        <div style="font-weight:700; color:#d8c8ff;">
            ✨ MeetingMate AI
        </div>
        <div style="font-size:12px; color:#aeb8d0; margin-top:5px;">
            Stay organized. Save time. Get more done.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    if st.button("🚪  Sign Out", use_container_width=True):

        for key in (
            "user_id",
            "user_name",
            "user_email",
            "analysis_result",
            "analysis_title",
            "analysis_transcript",
            "chat_history"
        ):

            st.session_state[key] = (
                [] if key == "chat_history" else None
            )

        st.rerun()


# ==================================================
# 12. DASHBOARD
# ==================================================

if page == "Dashboard":

    st.markdown("""
    <div class="hero">
        <h2>👋 Welcome to your workspace</h2>
        <p>
            Manage meetings, discover insights, and keep track
            of every important action item in one place.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.title("📊 Dashboard")

    st.write("Your meeting activity at a glance.")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM meetings WHERE user_id = ?",
        (st.session_state.user_id,)
    )
    total_meetings = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM schedules WHERE user_id = ?",
        (st.session_state.user_id,)
    )
    total_schedules = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id = ?",
        (st.session_state.user_id,)
    )
    total_tasks = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE status = 'Pending' AND user_id = ?
    """, (st.session_state.user_id,))
    pending_tasks = cur.fetchone()[0]

    conn.close()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📄 Total Meetings", total_meetings)
    col2.metric("📅 Scheduled Meetings", total_schedules)
    col3.metric("✅ Total Tasks", total_tasks)
    col4.metric("⏳ Pending Tasks", pending_tasks)

    st.divider()

    st.subheader("📅 Upcoming Meetings")

    conn = get_connection()

    upcoming = conn.execute("""
        SELECT title, meeting_date, meeting_time, participants
        FROM schedules
        WHERE meeting_date >= ? AND user_id = ?
        ORDER BY meeting_date, meeting_time
        LIMIT 5
    """, (
        date.today().isoformat(),
        st.session_state.user_id
    )).fetchall()

    conn.close()

    if upcoming:

        for meeting in upcoming:

            title, meeting_date, meeting_time, participants = meeting

            with st.container(border=True):

                st.markdown(f"**📌 {title}**")
                st.write(f"🗓️ Date: {meeting_date}")
                st.write(f"🕒 Time: {meeting_time}")
                st.write(f"👥 Participants: {participants or 'Not specified'}")

    else:

        st.info("No upcoming meetings scheduled.")


# ==================================================
# 13. ANALYZE MEETING
# ==================================================

elif page == "Analyze Meeting":

    st.title("📄 Analyze Meeting")

    st.write(
        "Upload a meeting document or audio recording, "
        "or paste your transcript below."
    )

    title = st.text_input(
        "Meeting Title",
        placeholder="Example: Weekly Project Review"
    )

    uploaded_meeting_file = st.file_uploader(
        "📎 Upload Meeting Document or Audio",
        type=[
            "pdf", "docx", "txt",
            "mp3", "wav", "m4a",
            "aac", "flac", "ogg"
        ]
    )

    transcript = st.text_area(
        "Meeting Transcript",
        height=250,
        placeholder="Paste your meeting transcript here..."
    )

    if st.button(
        "🔍 Run Meeting Analysis",
        type="primary",
        use_container_width=True
    ):

        if not title.strip():

            st.warning("Please enter a meeting title.")

        elif not transcript.strip() and uploaded_meeting_file is None:

            st.warning("Upload a file or paste a transcript.")

        else:

            try:

                with st.spinner("Analyzing your meeting with Gemini..."):

                    source_transcript = transcript.strip()

                    if uploaded_meeting_file is not None:

                        extracted_content = extract_uploaded_content(
                            uploaded_meeting_file
                        )

                        if not extracted_content.strip():

                            raise ValueError(
                                "No readable content was found in the uploaded file."
                            )

                        if source_transcript:

                            source_transcript += "\n\n" + extracted_content

                        else:

                            source_transcript = extracted_content

                    result = analyze_meeting(source_transcript)

                st.session_state.analysis_result = result
                st.session_state.analysis_title = title
                st.session_state.analysis_transcript = source_transcript

                st.success("Meeting analysis completed!")

                if uploaded_meeting_file is not None and uploaded_meeting_file.name.lower().endswith(
                    (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg")
                ):

                    st.info("Audio transcription completed.")

                with st.expander("📃 View Extracted Transcript"):

                    st.text(source_transcript)

            except Exception as e:

                st.error(f"Analysis failed: {e}")

    if st.session_state.analysis_result:

        st.divider()

        st.subheader("✨ Analysis Results")

        st.markdown(st.session_state.analysis_result)

        st.divider()

        if st.button("💾 Save Meeting", type="primary"):

            try:

                with st.spinner("Saving meeting and extracting tasks..."):

                    extracted_tasks = extract_tasks(
                        st.session_state.analysis_transcript
                    )

                    conn = get_connection()
                    cur = conn.cursor()

                    cur.execute("""
                        INSERT INTO meetings
                        (user_id, title, transcript, analysis)
                        VALUES (?, ?, ?, ?)
                    """, (
                        st.session_state.user_id,
                        st.session_state.analysis_title,
                        st.session_state.analysis_transcript,
                        st.session_state.analysis_result
                    ))

                    for task in extracted_tasks:

                        cur.execute("""
                            INSERT INTO tasks
                            (user_id, task, assignee, due_date)
                            VALUES (?, ?, ?, ?)
                        """, (
                            st.session_state.user_id,
                            task.get("task", "Not specified"),
                            task.get("assignee", "Not specified"),
                            task.get("due_date", "Not specified")
                        ))

                    conn.commit()
                    conn.close()

                st.session_state.analysis_result = None
                st.session_state.analysis_title = ""
                st.session_state.analysis_transcript = ""

                st.success(
                    f"Meeting saved! {len(extracted_tasks)} tasks added."
                )

                st.rerun()

            except Exception as e:

                st.error(f"Could not save meeting: {e}")
                # ==================================================
# 14. MEETING HISTORY
# ==================================================

elif page == "Meeting History":

    st.title("📚 Meeting History")

    st.write("Access your previously analyzed and saved meetings.")

    conn = get_connection()

    meetings = conn.execute("""
        SELECT id, title, transcript, analysis, created_at
        FROM meetings
        WHERE user_id = ?
        ORDER BY id DESC
    """, (st.session_state.user_id,)).fetchall()

    conn.close()

    if meetings:

        for meeting in meetings:

            meeting_id, title, transcript, analysis, created_at = meeting

            with st.expander(f"📌 {title} — {created_at}"):

                st.subheader("✨ Meeting Analysis")
                st.markdown(analysis or "No analysis available.")

                st.divider()

                st.subheader("📃 Original Transcript")
                st.text(transcript)

    else:

        st.info("No meetings saved yet. Analyze your first meeting to get started.")


# ==================================================
# 15. SCHEDULE MEETING
# ==================================================

elif page == "Schedule Meeting":

    st.title("📅 Schedule Meeting")

    st.write("Plan your upcoming meetings and keep everyone informed.")

    with st.form("schedule_form"):

        meeting_title = st.text_input(
            "Meeting Title",
            placeholder="Example: Sprint Planning"
        )

        meeting_date = st.date_input(
            "Meeting Date",
            min_value=date.today()
        )

        meeting_time = st.time_input(
            "Meeting Time",
            value=time(10, 0)
        )

        participants = st.text_input(
            "Participants",
            placeholder="Enter names separated by commas"
        )

        submitted = st.form_submit_button(
            "📅 Schedule Meeting",
            type="primary"
        )

        if submitted:

            if not meeting_title.strip():

                st.warning("Please enter a meeting title.")

            else:

                conn = get_connection()

                conn.execute("""
                    INSERT INTO schedules
                    (user_id, title, meeting_date, meeting_time, participants)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    st.session_state.user_id,
                    meeting_title,
                    meeting_date.isoformat(),
                    meeting_time.strftime("%H:%M"),
                    participants
                ))

                conn.commit()
                conn.close()

                st.success("Meeting scheduled successfully!")
                st.rerun()

    st.divider()

    st.subheader("📋 Scheduled Meetings")

    conn = get_connection()

    schedules = conn.execute("""
        SELECT id, title, meeting_date, meeting_time, participants
        FROM schedules
        WHERE user_id = ?
        ORDER BY meeting_date, meeting_time
    """, (st.session_state.user_id,)).fetchall()

    conn.close()

    if schedules:

        for meeting in schedules:

            meeting_id, title, meeting_date, meeting_time, participants = meeting

            with st.container(border=True):

                col1, col2 = st.columns([4, 1])

                with col1:

                    st.markdown(f"**📌 {title}**")
                    st.write(f"🗓️ Date: {meeting_date}")
                    st.write(f"🕒 Time: {meeting_time}")
                    st.write(f"👥 Participants: {participants or 'Not specified'}")

                with col2:

                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_schedule_{meeting_id}"
                    ):

                        conn = get_connection()

                        conn.execute("""
                            DELETE FROM schedules
                            WHERE id = ? AND user_id = ?
                        """, (
                            meeting_id,
                            st.session_state.user_id
                        ))

                        conn.commit()
                        conn.close()

                        st.rerun()

    else:

        st.info("No meetings scheduled yet.")


# ==================================================
# 16. AI CHAT ASSISTANT
# ==================================================

elif page == "AI Chat Assistant":

    st.title("💬 AI Chat Assistant")

    st.write(
        "Ask questions about your saved meetings, "
        "decisions, participants, and action items."
    )

    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input(
        "Ask something about your meetings..."
    )

    if user_question:

        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.markdown(user_question)

        try:

            conn = get_connection()

            previous_meetings = conn.execute("""
                SELECT title, transcript, analysis
                FROM meetings
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 5
            """, (st.session_state.user_id,)).fetchall()

            conn.close()

            meeting_context = ""

            for meeting in previous_meetings:

                meeting_context += f"""
Meeting Title: {meeting[0]}

Transcript:
{meeting[1]}

Analysis:
{meeting[2]}

-------------------------
"""

            if not meeting_context:

                meeting_context = "No saved meetings are available."

            prompt = f"""
You are MeetingMate, an AI meeting assistant.

Answer the user's question using the saved meeting information below.

Rules:
- Use the meeting information as your source.
- Do not invent details.
- If the answer is not available, clearly say so.
- Give simple and clear answers.

Saved Meeting Information:
{meeting_context}

User Question:
{user_question}
"""

            with st.chat_message("assistant"):

                with st.spinner("Thinking..."):

                    answer = ask_gemini(prompt)

                st.markdown(answer)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:

            st.error(f"Chat assistant error: {e}")


# ==================================================
# 17. TASK MANAGEMENT
# ==================================================

elif page == "Task Management":

    st.title("✅ Task Management")

    st.write(
        "Track action items extracted from your meetings "
        "and manage their completion."
    )

    st.subheader("➕ Add Task Manually")

    with st.form("manual_task_form"):

        task_name = st.text_input(
            "Task Description",
            placeholder="Enter the task"
        )

        assignee = st.text_input(
            "Assigned To",
            placeholder="Person responsible"
        )

        due_date = st.text_input(
            "Due Date",
            placeholder="Example: 2026-11-10 or Not specified"
        )

        add_task = st.form_submit_button(
            "➕ Add Task",
            type="primary"
        )

        if add_task:

            if not task_name.strip():

                st.warning("Please enter a task description.")

            else:

                conn = get_connection()

                conn.execute("""
                    INSERT INTO tasks
                    (user_id, task, assignee, due_date)
                    VALUES (?, ?, ?, ?)
                """, (
                    st.session_state.user_id,
                    task_name,
                    assignee or "Not specified",
                    due_date or "Not specified"
                ))

                conn.commit()
                conn.close()

                st.success("Task added successfully!")
                st.rerun()

    st.divider()

    st.subheader("📋 All Tasks")

    conn = get_connection()

    tasks = conn.execute("""
        SELECT id, task, assignee, due_date, status
        FROM tasks
        WHERE user_id = ?
        ORDER BY id DESC
    """, (st.session_state.user_id,)).fetchall()

    conn.close()

    if tasks:

        for task in tasks:

            task_id, task_name, assignee, due_date, status = task

            with st.container(border=True):

                col1, col2 = st.columns([4, 2])

                with col1:

                    st.markdown(f"**{task_name}**")
                    st.write(f"👤 Assigned to: {assignee}")
                    st.write(f"📅 Due date: {due_date}")

                    if status == "Completed":

                        st.success("Completed")

                    else:

                        st.warning("Pending")

                with col2:

                    new_status = st.selectbox(
                        "Task Status",
                        ["Pending", "Completed"],
                        index=1 if status == "Completed" else 0,
                        key=f"status_{task_id}"
                    )

                    if st.button(
                        "🔄 Update Status",
                        key=f"update_{task_id}"
                    ):

                        conn = get_connection()

                        conn.execute("""
                            UPDATE tasks
                            SET status = ?
                            WHERE id = ? AND user_id = ?
                        """, (
                            new_status,
                            task_id,
                            st.session_state.user_id
                        ))

                        conn.commit()
                        conn.close()

                        st.success("Task status updated!")
                        st.rerun()

                    if st.button(
                        "🗑️ Delete Task",
                        key=f"delete_task_{task_id}"
                    ):

                        conn = get_connection()

                        conn.execute("""
                            DELETE FROM tasks
                            WHERE id = ? AND user_id = ?
                        """, (
                            task_id,
                            st.session_state.user_id
                        ))

                        conn.commit()
                        conn.close()

                        st.rerun()

    else:

        st.info("No tasks available yet. Analyze a meeting or add a task manually.")