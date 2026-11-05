import os
import sqlite3
import json
import tempfile
from pathlib import Path
from datetime import date, time

import streamlit as st
from dotenv import load_dotenv
from google import genai


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="MeetingMate",
    page_icon="🤖",
    layout="wide"
)

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = "gemini-3.1-flash-lite"

if not API_KEY:
    st.error("Gemini API key not found. Please check your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)

DB_NAME = "meetingmate.db"


# --------------------------------------------------
# 2. DATABASE
# --------------------------------------------------

def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            transcript TEXT NOT NULL,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            meeting_date TEXT NOT NULL,
            meeting_time TEXT NOT NULL,
            participants TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            assignee TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()


initialize_database()


# --------------------------------------------------
# 3. SESSION STATE
# --------------------------------------------------

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "analysis_title" not in st.session_state:
    st.session_state.analysis_title = ""

if "analysis_transcript" not in st.session_state:
    st.session_state.analysis_transcript = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --------------------------------------------------
# 4. GEMINI FUNCTION
# --------------------------------------------------

def ask_gemini(prompt):
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text.strip()


def extract_uploaded_content(uploaded_file):
    """Extract transcript text from PDF, DOCX, TXT, or audio files."""

    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    # TXT FILE
    if file_name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace")

    # PDF FILE
    if file_name.endswith(".pdf"):
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(file_bytes))

        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        ).strip()

    # DOCX FILE
    if file_name.endswith(".docx"):
        from docx import Document
        import io

        document = Document(io.BytesIO(file_bytes))

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        ).strip()

    # AUDIO FILE
    audio_extensions = (
        ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"
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
                    "Transcribe the audio accurately. Return only the spoken "
                    "words as a meeting transcript. Preserve speaker names "
                    "when they are clearly spoken. Do not summarize or invent "
                    "missing words."
                ]
            )

            if not response.text:
                raise ValueError(
                    "Gemini could not transcribe this audio file."
                )

            return response.text.strip()

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    raise ValueError(
        "Unsupported file type. Upload PDF, DOCX, TXT, or an audio file."
    )


# --------------------------------------------------
# 5. MEETING ANALYSIS
# --------------------------------------------------

def analyze_meeting(transcript):

    prompt = f"""
You are an AI meeting analysis assistant.

Analyze the following meeting transcript.

Provide the output using these sections:

1. Executive Summary
Give a clear summary of the meeting.

2. Key Discussion Points
List the important topics discussed.

3. Decisions
List the decisions explicitly made during the meeting.

4. Action Items
List the tasks assigned, the responsible persons,
and deadlines only when explicitly mentioned.

IMPORTANT:
- Do not invent information.
- Do not invent participants or decisions.
- If a responsible person is not clear, write Not specified.
- If a deadline is not mentioned, write Not specified.
- Preserve the actual meaning of the discussion.

Meeting Transcript:
{transcript}
"""

    return ask_gemini(prompt)


# --------------------------------------------------
# 6. AUTOMATIC TASK EXTRACTION
# --------------------------------------------------

def extract_tasks(transcript):

    prompt = f"""
You are an accurate meeting action-item extraction assistant.

Extract all action items from the meeting transcript.

Return ONLY a valid JSON array.
Do not include markdown or explanations.

Use this exact structure:

[
    {{
        "task": "Task description",
        "assignee": "Person responsible",
        "due_date": "YYYY-MM-DD or Not specified"
    }}
]

Rules:
- Extract only actual action items.
- Do not convert general discussion into tasks.
- Do not invent tasks, assignees, or deadlines.
- If an assignee is missing, use "Not specified".
- If a deadline is missing, use "Not specified".
- If a date is mentioned without a year, do not guess the year.
  Use the date as stated in the transcript.
- If no action items exist, return [].

Meeting Transcript:
{transcript}
"""

    response = ask_gemini(prompt)
    cleaned = response.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    tasks = json.loads(cleaned)

    if not isinstance(tasks, list):
        raise ValueError("Invalid task format returned by Gemini.")

    for task in tasks:
        if not isinstance(task, dict) or not task.get("task"):
            raise ValueError("Gemini returned an invalid task.")

    return tasks


# --------------------------------------------------
# 7. CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #0b1020;
    color: #f1f5f9;
}

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #11182e 0%,
        #17132d 100%
    );
    border-right: 1px solid #303653;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #cbd5e1;
}

[data-testid="stSidebar"] h1 {
    color: #ffffff;
    font-size: 28px;
}

[data-testid="stSidebar"] .stRadio label {
    color: #e2e8f0 !important;
    font-size: 15px;
    padding: 8px 10px;
    border-radius: 8px;
}

[data-testid="stSidebar"] .stRadio label:hover {
    background-color: #29264b;
}

h1, h2, h3 {
    color: #f8fafc !important;
}

p, label {
    color: #cbd5e1;
}

[data-testid="stMetric"] {
    background: linear-gradient(
        135deg,
        #1c2540,
        #29204a
    );
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #37345e;
}

[data-testid="stMetricLabel"] {
    color: #c4b5fd !important;
}

[data-testid="stMetricValue"] {
    color: #ffffff !important;
}

.stButton button {
    background: linear-gradient(
        90deg,
        #7c3aed,
        #6366f1
    );
    color: white;
    border: none;
    border-radius: 9px;
    padding: 9px 18px;
    font-weight: 600;
}

.stButton button:hover {
    background: linear-gradient(
        90deg,
        #6d28d9,
        #4f46e5
    );
    color: white;
    border: none;
}

.stTextInput input,
.stTextArea textarea,
.stDateInput input,
.stTimeInput input {
    background-color: #171f35;
    color: white;
    border: 1px solid #394466;
    border-radius: 8px;
}

[data-testid="stFileUploader"] {
    background-color: #171f35;
    border: 1px dashed #7c3aed;
    border-radius: 12px;
    padding: 15px;
}

[data-testid="stExpander"] {
    background-color: #151d32;
    border: 1px solid #303b5b;
    border-radius: 10px;
}

hr {
    border-color: #303b5b;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# 8. SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:

    st.markdown(
        """
        <div style="padding:15px 5px 20px 5px;">
            <div style="font-size:34px;">🤖</div>
            <h1 style="margin-bottom:0;">MeetingMate</h1>
            <p style="color:#a5b4fc;font-size:13px;">
                Agentic AI Meeting Assistant
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown(
        """
        <p style="
            color:#a5b4fc;
            font-size:12px;
            font-weight:600;
            letter-spacing:1px;
        ">
        WORKSPACE
        </p>
        """,
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📄 Analyze Meeting",
            "📚 Meeting History",
            "📅 Schedule Meeting",
            "💬 AI Chat Assistant",
            "✅ Task Management"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,#29204a,#1c2540);
            padding:15px;
            border-radius:12px;
            margin-top:15px;
        ">
            <p style="font-size:13px;color:#c4b5fd;">
                ✨ YOUR PRODUCTIVITY HUB
            </p>
            <p style="font-size:12px;color:#cbd5e1;">
                Organize meetings, discover insights,
                and keep track of every action item.
            </p>
        </div>
        <br>
        <p style="font-size:12px;color:#94a3b8;text-align:center;">
            Powered by Google Gemini
        </p>
        """,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# 9. DASHBOARD
# --------------------------------------------------

if page == "🏠 Dashboard":

    st.title("🤖 MeetingMate Dashboard")

    st.write(
        "Your AI-powered assistant for meeting analysis "
        "and task management."
    )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM meetings")
    total_meetings = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM schedules")
    total_schedules = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE status = 'Pending'
    """)
    pending_tasks = cur.fetchone()[0]

    conn.close()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Meetings", total_meetings)
    col2.metric("Scheduled Meetings", total_schedules)
    col3.metric("Total Tasks", total_tasks)
    col4.metric("Pending Tasks", pending_tasks)

    st.divider()

    st.subheader("📅 Upcoming Meetings")

    conn = get_connection()

    upcoming = conn.execute("""
        SELECT title, meeting_date, meeting_time, participants
        FROM schedules
        WHERE meeting_date >= ?
        ORDER BY meeting_date, meeting_time
        LIMIT 5
    """, (date.today().isoformat(),)).fetchall()

    conn.close()

    if upcoming:

        for meeting in upcoming:

            title, meeting_date, meeting_time, participants = meeting

            with st.container(border=True):

                st.write(f"**{title}**")
                st.write(f"📅 Date: {meeting_date}")
                st.write(f"⏰ Time: {meeting_time}")
                st.write(
                    f"👥 Participants: {participants or 'Not specified'}"
                )

    else:
        st.info("No upcoming meetings scheduled.")


# --------------------------------------------------
# 10. ANALYZE MEETING
# --------------------------------------------------

elif page == "📄 Analyze Meeting":

    st.title("📄 Analyze Meeting")

    st.write(
        "Upload a meeting document or recording, "
        "or paste your meeting transcript."
    )

    title = st.text_input("Meeting Title")

    uploaded_meeting_file = st.file_uploader(
        "Upload a meeting document or audio recording",
        type=[
            "pdf", "docx", "txt", "mp3", "wav",
            "m4a", "aac", "flac", "ogg"
        ],
        help=(
            "Supported: PDF, DOCX, TXT, MP3, WAV, "
            "M4A, AAC, FLAC and OGG."
        )
    )

    transcript = st.text_area(
        "Or paste your Meeting Transcript",
        height=250,
        placeholder="Paste your meeting transcript here..."
    )

    if st.button("🔍 Run Meeting Analysis", type="primary"):

        if not title.strip():

            st.warning("Please enter a meeting title.")

        elif not transcript.strip() and uploaded_meeting_file is None:

            st.warning(
                "Please upload a meeting document/audio file "
                "or paste a transcript."
            )

        else:

            try:

                with st.spinner(
                    "Extracting transcript and analyzing your meeting..."
                ):

                    source_transcript = transcript.strip()

                    if uploaded_meeting_file is not None:

                        extracted_content = extract_uploaded_content(
                            uploaded_meeting_file
                        )

                        if not extracted_content.strip():

                            raise ValueError(
                                "No readable text was found. If this is "
                                "a scanned PDF, you may need OCR; if it "
                                "is audio, check that speech is audible."
                            )

                        if source_transcript:

                            source_transcript += (
                                "\n\n" + extracted_content
                            )

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

                    st.info(
                        "Audio transcription completed. "
                        "The generated transcript is included below."
                    )

                with st.expander("View extracted transcript"):
                    st.text(source_transcript)

            except Exception as e:

                st.error(f"Analysis failed: {e}")

    if st.session_state.analysis_result:

        st.divider()

        st.subheader("Analysis Results")

        st.markdown(st.session_state.analysis_result)

        st.divider()

        if st.button("💾 Save Meeting", type="primary"):

            try:

                with st.spinner(
                    "Extracting action items and saving meeting..."
                ):

                    extracted_tasks = extract_tasks(
                        st.session_state.analysis_transcript
                    )

                    conn = get_connection()
                    cur = conn.cursor()

                    cur.execute("""
                        INSERT INTO meetings
                        (title, transcript, analysis)
                        VALUES (?, ?, ?)
                    """, (
                        st.session_state.analysis_title,
                        st.session_state.analysis_transcript,
                        st.session_state.analysis_result
                    ))

                    for task in extracted_tasks:

                        cur.execute("""
                            INSERT INTO tasks
                            (task, assignee, due_date)
                            VALUES (?, ?, ?)
                        """, (
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
                    f"Meeting saved successfully! "
                    f"{len(extracted_tasks)} tasks added automatically."
                )

                st.rerun()

            except Exception as e:

                st.error(f"Could not save meeting: {e}")


# --------------------------------------------------
# 11. MEETING HISTORY
# --------------------------------------------------

elif page == "📚 Meeting History":

    st.title("📚 Meeting History")

    conn = get_connection()

    meetings = conn.execute("""
        SELECT id, title, transcript, analysis, created_at
        FROM meetings
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    if meetings:

        for meeting in meetings:

            meeting_id, title, transcript, analysis, created_at = meeting

            with st.expander(f"📌 {title} — {created_at}"):

                st.subheader("Meeting Analysis")

                st.markdown(analysis or "No analysis available.")

                st.divider()

                st.subheader("Original Transcript")

                st.text(transcript)

    else:

        st.info("No meetings saved yet.")


# --------------------------------------------------
# 12. SCHEDULE MEETING
# --------------------------------------------------

elif page == "📅 Schedule Meeting":

    st.title("📅 Schedule Meeting")

    st.write("Add and manage your upcoming meetings.")

    with st.form("schedule_form"):

        meeting_title = st.text_input("Meeting Title")

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
            placeholder="Enter participant names separated by commas"
        )

        submitted = st.form_submit_button(
            "Schedule Meeting",
            type="primary"
        )

        if submitted:

            if not meeting_title.strip():

                st.warning("Please enter a meeting title.")

            else:

                conn = get_connection()

                conn.execute("""
                    INSERT INTO schedules
                    (title, meeting_date, meeting_time, participants)
                    VALUES (?, ?, ?, ?)
                """, (
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

    st.subheader("Scheduled Meetings")

    conn = get_connection()

    schedules = conn.execute("""
        SELECT id, title, meeting_date, meeting_time, participants
        FROM schedules
        ORDER BY meeting_date, meeting_time
    """).fetchall()

    conn.close()

    if schedules:

        for meeting in schedules:

            meeting_id, title, meeting_date, meeting_time, participants = meeting

            with st.container(border=True):

                col1, col2 = st.columns([4, 1])

                with col1:

                    st.write(f"**{title}**")
                    st.write(f"📅 Date: {meeting_date}")
                    st.write(f"⏰ Time: {meeting_time}")

                    st.write(
                        f"👥 Participants: {participants or 'Not specified'}"
                    )

                with col2:

                    if st.button(
                        "Delete",
                        key=f"delete_schedule_{meeting_id}"
                    ):

                        conn = get_connection()

                        conn.execute(
                            "DELETE FROM schedules WHERE id = ?",
                            (meeting_id,)
                        )

                        conn.commit()
                        conn.close()

                        st.rerun()

    else:

        st.info("No meetings scheduled yet.")


# --------------------------------------------------
# 13. AI CHAT ASSISTANT
# --------------------------------------------------

elif page == "💬 AI Chat Assistant":

    st.title("💬 AI Chat Assistant")

    st.write(
        "Ask questions about your meetings and retrieve "
        "information from saved meeting history."
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
                ORDER BY id DESC
                LIMIT 5
            """).fetchall()

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


# --------------------------------------------------
# 14. TASK MANAGEMENT
# --------------------------------------------------

elif page == "✅ Task Management":

    st.title("✅ Task Management")

    st.write(
        "View automatically extracted tasks and manage "
        "their completion status."
    )

    st.subheader("➕ Add Task Manually")

    with st.form("manual_task_form"):

        task_name = st.text_input("Task Description")

        assignee = st.text_input("Assigned To")

        due_date = st.text_input(
            "Due Date",
            placeholder="Example: 2026-11-10 or Not specified"
        )

        add_task = st.form_submit_button("Add Task")

        if add_task:

            if not task_name.strip():

                st.warning("Please enter a task description.")

            else:

                conn = get_connection()

                conn.execute("""
                    INSERT INTO tasks
                    (task, assignee, due_date)
                    VALUES (?, ?, ?)
                """, (
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
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    if tasks:

        for task in tasks:

            task_id, task_name, assignee, due_date, status = task

            with st.container(border=True):

                col1, col2 = st.columns([4, 2])

                with col1:

                    st.write(f"**{task_name}**")
                    st.write(f"Assigned to: {assignee}")
                    st.write(f"Due date: {due_date}")

                    if status == "Completed":

                        st.success("Completed")

                    else:

                        st.warning("Pending")

                with col2:

                    new_status = st.selectbox(
                        "Task Status",
                        ["Pending", "Completed"],
                        index=(
                            1 if status == "Completed" else 0
                        ),
                        key=f"status_{task_id}"
                    )

                    if st.button(
                        "Update Status",
                        key=f"update_{task_id}"
                    ):

                        conn = get_connection()

                        conn.execute("""
                            UPDATE tasks
                            SET status = ?
                            WHERE id = ?
                        """, (new_status, task_id))

                        conn.commit()
                        conn.close()

                        st.success("Task status updated!")

                        st.rerun()

                    if st.button(
                        "Delete Task",
                        key=f"delete_task_{task_id}"
                    ):

                        conn = get_connection()

                        conn.execute(
                            "DELETE FROM tasks WHERE id = ?",
                            (task_id,)
                        )

                        conn.commit()
                        conn.close()

                        st.rerun()

    else:

        st.info("No tasks available yet.")