# ClearHire V2 — AI Interview Integrity Analyzer

Backend API with PostgreSQL database for persistent interview session storage.

## Features
- All V1 NLP analysis features
- PostgreSQL database integration
- Interview session storage
- Candidate history tracking
- Overall candidate risk scoring

## Tech Stack
- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic

## API Endpoints
- `POST /analyze` — Analyze response and save session
- `GET /sessions` — Get all sessions
- `GET /sessions/{id}` — Get single session
- `GET /sessions/candidate/{name}` — Get all sessions for a candidate
- `GET /candidate/{name}/score` — Get overall candidate score

## How to Run
1. Clone the repo
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate`
4. Install: `pip install -r requirements.txt`
5. Create `.env` with your `DATABASE_URL`
6. Run: `uvicorn main:app --reload`

