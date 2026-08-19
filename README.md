# SkillBridge — AI Placement Assistant (RAG + Endee Vector DB + Groq LLM)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.0-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20API-f50057?style=flat-square)](https://groq.com/)
[![Endee](https://img.shields.io/badge/Vector%20DB-Endee-00ADB5?style=flat-square)](https://github.com/PujithAmar/Endee_Project26)
[![License](https://img.shields.io/badge/License-MIT-blue.style=flat-square)](LICENSE)

An intelligent, retrieval-grounded **AI Placement Assistant** built to help candidates evaluate their resume fit against specific job descriptions. Using a custom Retrieval-Augmented Generation (RAG) pipeline powered by **Endee Vector Database** and **Groq LLM**, SkillBridge provides role match scores, missing skill gap analysis, actionable resume improvement suggestions, and tailored technical & HR interview questions.

---

## 📌 Problem Statement

Students and job seekers frequently apply to open positions without a clear understanding of:
- Their explicit skill gaps relative to the job description.
- How ATS systems and recruiters evaluate their resume.
- Role-specific technical and HR interview questions they will face.

Existing resume scanners generate generic keyword scores without contextual reasoning or grounded candidate profile Q&A.

---

## 💡 Solution

**SkillBridge** provides grounded, personalized career insights by indexing candidate resumes alongside job requirements in a high-dimensional vector space:

- **Match Score (0–100)**: Quantitative job alignment score backed by explicit reasoning.
- **Skill Gap Extraction**: Automatically pinpoints missing technical skills and concepts.
- **Actionable Suggestions**: Step-by-step improvement recommendations and learning roadmaps.
- **Role-Tailored Interview Questions**: Generates technical and HR interview questions specific to the resume & job description.
- **Grounded Profile Chat**: Ask custom questions ("Does the candidate know Docker?", "What is their experience with microservices?") grounded strictly on the candidate's indexed profile.
- **Analysis History**: Persists and displays past candidate evaluation sessions.

---

## 🏗️ System Architecture

```
[ Candidate Resume (PDF / Text) ]       [ Job Description (Text) ]
                │                                    │
                └───► [ Text Extraction & Chunking ] ◄───┘
                                  │
                       ( 300-Token Chunks )
                                  │
                                  ▼
               [ Embeddings: all-MiniLM-L6-v2 (384-dim) ]
                                  │
                                  ▼
               [ Endee Serverless Vector Database ]
                     ( HNSW + Cosine Index )
                                  │
                                  ▼
             [ Top-K RAG Context Retrieval (JD ↔ Resume) ]
                                  │
                                  ▼
              [ Groq LLM (gpt-oss-120b / llama-3.3-70b) ]
                   ( Structured JSON Generation )
                                  │
                                  ▼
       [ Final Insights: Score + Skill Gaps + Interview Qs ]
```

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React, Tailwind CSS, Lucide React, Shadcn UI |
| **Backend** | FastAPI, Uvicorn, Python 3.12 |
| **Vector Database** | Endee Serverless Vector DB (INT8, Cosine, HNSW) |
| **LLM Provider** | Groq API (`openai/gpt-oss-120b`, `qwen/qwen3.6-27b`, `groq/compound`) |
| **Embeddings** | Local `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim) |
| **PDF Extraction** | `pdfplumber` |
| **Database** | MongoDB / Supabase / Local Persistent Store |

---

## ✨ Features

- 📄 **PDF & Raw Text Resume Support**: Drag-and-drop resume PDFs or paste raw text.
- 🎯 **Match Score & Reason**: Dynamic animated match score ring with comprehensive feedback.
- 🔍 **Skill Gap Identification**: Highlights matched skills vs missing required technologies.
- 🧠 **Tailored Interview Preparation**: Generates specific technical and HR questions to practice.
- 💬 **Session-Grounded Semantic Chat**: Interactive profile Q&A using RAG context.
- 📜 **Analysis History**: Store, retrieve, inspect, and manage past resume reports.

---

## 🚀 Quick Start & Setup

### Prerequisites
- Python 3.10+
- Node.js v18+ & npm / yarn

### 1. Repository Setup
```bash
git clone https://github.com/PujithAmar/Endee_Project26.git
cd Endee_Project26
```

### 2. Backend Setup
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Configure Environment Variables in backend/.env
GROQ_API_KEY="your_groq_api_key_here"
ENDEE_TOKEN="your_endee_token_here"
ENDEE_INDEX_NAME="skillbridge"
MONGO_URL="mongodb://localhost:27017"
DB_NAME="skillbridge_db"

# Start FastAPI Backend Server
python3 -m uvicorn server:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd ../frontend

# Install dependencies & configure frontend/.env
npm install

# Start React Development Server
npm start
```
Open **[http://localhost:3007](http://localhost:3007)** (or **http://localhost:3000**) in your browser.

---

## 📑 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health probe verifying Vector Store, Database, and Groq API status |
| `POST` | `/api/analyze` | Multipart upload for Resume PDF / text + Job Description |
| `POST` | `/api/analyze-text` | JSON payload for text resume analysis |
| `POST` | `/api/chat` | RAG-grounded profile Q&A for active session |
| `GET` | `/api/chat/{session_id}` | Retrieve chat history for session |
| `GET` | `/api/history` | List all past analysis sessions |
| `GET` | `/api/history/{id}` | Get detail view of analysis record |
| `DELETE` | `/api/history/{id}` | Delete an analysis record |

---

## 👤 Author Information

* **Author**: **Pujith Amar Sunkavalli**
* **Email**: [`pujithamar@gmail.com`](mailto:pujithamar@gmail.com)
* **GitHub**: [@PujithAmar](https://github.com/PujithAmar)
* **Project Repository**: [Endee_Project26](https://github.com/PujithAmar/Endee_Project26)

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
