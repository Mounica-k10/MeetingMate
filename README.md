# 🤖 MeetingMate – Agentic AI Meeting Assistant

MeetingMate is an AI-powered meeting assistant designed to simplify meeting management by automatically analyzing meeting conversations, generating summaries, identifying important decisions, extracting action items, and helping users retrieve information from previously saved meetings.

It uses Google's Gemini API to transform meeting discussions into structured and meaningful information, making meeting follow-ups easier and more efficient.

## 🚀 Live Demo

**Try MeetingMate here:**

🌐 https://meetingmate-ai-assistant.streamlit.app/

## ✨ Features

### 1. AI-Powered Meeting Analysis
- Generate executive summaries of meetings.
- Identify key discussion points.
- Extract important decisions.
- Identify tasks, responsible persons and deadlines.

### 2. Multiple File Upload Support
- Upload meeting transcripts in TXT format.
- Upload PDF documents.
- Upload DOCX documents.
- Upload audio recordings for transcription and analysis.

### 3. Meeting History
- Save analyzed meetings.
- View previously analyzed meetings.
- Access saved meeting summaries and transcripts.

### 4. Meeting Scheduling
- Schedule upcoming meetings.
- Store meeting titles, dates, times and participants.
- View upcoming scheduled meetings.

### 5. AI Chat Assistant
- Ask questions about previously saved meetings.
- Retrieve tasks, deadlines and meeting decisions.
- Get information from historical meeting records.
- Handle questions about information that is not available in the meeting context.

### 6. Task Management
- Automatically extract action items from meeting discussions.
- Store tasks with assigned persons and deadlines.
- Add tasks manually.
- Update task statuses.
- Delete completed or unnecessary tasks.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application interface |
| Google Gemini API | AI-powered meeting analysis and chatbot |
| SQLite | Database management |
| LangGraph | Agent workflow framework |
| PyPDF | PDF text extraction |
| python-docx | Word document processing |
| python-dotenv | Environment variable management |

## 🏗️ Project Structure

```text
MeetingMate/
│
├── app.py
├── requirements.txt
├── .gitignore
├── meetingmate.db
└── README.md
```

The SQLite database is created locally when the application runs. It is not included in the GitHub repository.

## ⚙️ Installation and Setup

### Prerequisites
- Python 3.10 or above
- Git
- Google Gemini API key

### Step 1: Clone the Repository

```bash
git clone https://github.com/Mounica-k10/MeetingMate.git
```

### Step 2: Navigate to the Project Folder

```bash
cd MeetingMate
```

### Step 3: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure the Gemini API Key

Create a `.env` file in the project root directory.

Add your API key:

```env
GOOGLE_API_KEY=your_gemini_api_key
```

Replace the placeholder with your actual Gemini API key.

### Step 6: Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at:

```text
http://localhost:8501
```

## 🔐 Security

- API keys are stored in environment variables.
- Sensitive configuration files are excluded using `.gitignore`.
- Never upload your `.env` file or expose your API key publicly.

## 🎯 Applications

- Automating meeting documentation.
- Improving team collaboration.
- Tracking project responsibilities and deadlines.
- Managing meeting records.
- Retrieving information from previous discussions.
- Reducing manual meeting follow-up work.

## 🔮 Future Enhancements

- Fully integrated multi-agent workflow using LangGraph.
- Advanced retrieval-augmented generation (RAG) for historical meetings.
- Persistent cloud database integration.
- Calendar integration and automated reminders.
- Enhanced task assignment and tracking.
- Improved meeting validation and accuracy.

**MeetingMate – Making Every Meeting More Productive.**
