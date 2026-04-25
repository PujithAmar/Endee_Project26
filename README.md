# AI Placement Assistant using RAG + Endee Vector Database

## Problem Statement

Students often apply to jobs without understanding their skill gaps, resume quality, or job fit. 
Existing tools provide generic feedback and fail to give role-specific insights.

This leads to:
- Low shortlist rates
- Poor resume optimization
- Lack of targeted interview preparation

## Solution

This project is an AI-powered Placement Assistant that analyzes a candidate’s resume against a job description using a Retrieval-Augmented Generation (RAG) pipeline.

It provides:
- Match score (0–100)
- Missing skills
- Resume improvement suggestions
- Interview questions (technical + HR)

The system simulates how a recruiter evaluates a candidate and gives personalized insights.

## System Architecture

Resume + Job Description 
→ Text Extraction 
→ Chunking 
→ Embeddings (Sentence Transformers) 
→ Endee Vector Database 
→ Retrieval (Top-K relevant chunks) 
→ Gemini LLM 
→ Final Output (Insights)

## Tech Stack

- Frontend: React
- Backend: FastAPI
- Vector Database: Endee
- LLM: Gemini Flash
- Embeddings: sentence-transformers (all-MiniLM-L6-v2)
- PDF Parsing: pdfplumber
- Database: MongoDB

## Features

- Resume PDF upload and parsing
- Job description input
- Match score calculation
- Skill gap identification
- Personalized suggestions
- Interview question generation
- Semantic chat (RAG-based)
- Analysis history storage## Features

## Design Decisions

- Used RAG to improve accuracy by retrieving relevant context instead of sending full data to the LLM
- Used Endee as the vector database for efficient semantic search
- Built custom RAG pipeline instead of using frameworks to demonstrate deeper understanding
- Used sentence-transformers for fast and cost-effective local embeddings
- Used Gemini Flash for low-latency responses

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   pip install -r requirements.txt

3. Add API keys in .env file:
   ENDEE_API_KEY=your_key
   GEMINI_API_KEY=your_key

4. Run backend:
   uvicorn server:app --reload

5. Run frontend:
   npm start

## Sample Output

Match Score: 75%

Missing Skills:
- Docker
- System Design

Suggestions:
- Add backend project using APIs
- Improve resume bullet points

Interview Questions:
1. Explain REST API design
2. What is load balancing?

## Future Work

- ATS-based resume scoring
- Learning roadmap generation
- Multi-job comparison
- Advanced analytics dashboard
# Screenshots

<img width="1360" height="711" alt="Screenshot 2026-04-25 at 10 28 14 PM" src="https://github.com/user-attachments/assets/0eef2211-4008-4eea-9bff-c04b2b9c9643" />

<img width="1407" height="754" alt="Screenshot 2026-04-25 at 10 27 22 PM" src="https://github.com/user-attachments/assets/e465a46d-1d4d-4150-8c90-a7a12286edaa" />





## Author

Pujith Amar Sunkavalli  
B.Tech CSE | AI/ML Enthusiast
