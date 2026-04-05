from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.schemas import InterviewSession
from pydantic import BaseModel
import httpx
import os
import re

router = APIRouter()

ASSEMBLYAI_KEY = os.getenv("ASSEMBLYAI_KEY")

class InterviewRequest(BaseModel):
    candidatename: str = "Anonymous"
    question: str
    response_text: str

@router.get("/assemblyai-token")
async def get_assemblyai_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.assemblyai.com/v3/streaming/token",
            headers={"Authorization": ASSEMBLYAI_KEY},
            json={"expires_in": 3600}
        )
        data = response.json()
        return {"token": data["token"]}

@router.post("/analyze")
def analyze(request: InterviewRequest, db: Session = Depends(get_db)):
    text = request.response_text
    text_lower = text.lower()

    # ✅ FIXED: regex se proper count ho raha hai
    filler_words = ["um", "uh", "like", "you know", "basically", "literally", "hmm", "ahh"]
    filler_count = 0
    found_fillers = []
    for word in filler_words:
        matches = re.findall(r'\b' + re.escape(word) + r'\b', text_lower)
        if matches:
            filler_count += len(matches)
            found_fillers.append(f"{word}({len(matches)})")

    hedging_words = ["i think", "i believe", "maybe", "perhaps", "i guess", "probably", "not sure", "i feel like"]
    hedging_count = 0
    found_hedging = []
    for word in hedging_words:
        matches = re.findall(re.escape(word), text_lower)
        if matches:
            hedging_count += len(matches)
            found_hedging.append(word)

    contradiction_pairs = [
        ("always", "never"),
        ("expert", "beginner"),
        ("experienced", "fresher"),
        ("yes", "no"),
        ("know", "don't know")
    ]
    contradictions_found = []
    for pair in contradiction_pairs:
        if pair[0] in text_lower and pair[1] in text_lower:
            contradictions_found.append(f"{pair[0]} vs {pair[1]}")

    word_count = len(text.split())
    if word_count < 10:
        length_penalty = 30
    elif word_count < 20:
        length_penalty = 15
    else:
        length_penalty = 0

    total_signals = filler_count + hedging_count + len(contradictions_found)
    confidence_score = max(0, 100 - (total_signals * 10) - length_penalty)
    deception_likelihood = 100 - confidence_score

    if deception_likelihood >= 70:
        risk_level = "High"
    elif deception_likelihood >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    signals = []
    if filler_count > 0:
        signals.append(f"{filler_count} filler word(s) detected")
    if hedging_count > 0:
        signals.append(f"{hedging_count} hedging phrase(s) detected")
    if len(contradictions_found) > 0:
        signals.append(f"Contradiction found: {', '.join(contradictions_found)}")
    if word_count < 10:
        signals.append("Response too short")

    session = InterviewSession(
        candidatename=request.candidatename,
        question=request.question,
        response_text=text,
        filler_count=filler_count,
        hedging_count=hedging_count,
        contradiction_count=len(contradictions_found),
        confidence_score=confidence_score,
        deception_likelihood=deception_likelihood,
        risk_level=risk_level
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "candidatename": session.candidatename,
        "question": request.question,
        "word_count": word_count,
        "filler_words_found": found_fillers,
        "filler_word_count": filler_count,
        "hedging_phrases": found_hedging,
        "hedging_count": hedging_count,
        "contradictions_found": contradictions_found,
        "contradiction_detected": len(contradictions_found) > 0,
        "contradiction_count": len(contradictions_found),
        "confidence_score": confidence_score,
        "deception_likelihood": deception_likelihood,
        "risk_level": risk_level,
        "signals": signals,
        "signals_summary": ", ".join(signals) if signals else "No significant signals detected"
    }

@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(InterviewSession).all()
    return sessions

@router.get("/sessions/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        return {"error": "Session not found"}
    return session

@router.get("/sessions/candidate/{name}")
def get_candidate_sessions(name: str, db: Session = Depends(get_db)):
    sessions = db.query(InterviewSession).filter(InterviewSession.candidatename == name).all()
    return sessions

@router.get("/candidate/{name}/score")
def get_candidate_score(name: str, db: Session = Depends(get_db)):
    sessions = db.query(InterviewSession).filter(InterviewSession.candidatename == name).all()
    if not sessions:
        return {"error": "No sessions found for this candidate"}

    avg_deception = sum(s.deception_likelihood for s in sessions) / len(sessions)
    avg_confidence = sum(s.confidence_score for s in sessions) / len(sessions)

    if avg_deception >= 70:
        overall_risk = "High"
    elif avg_deception >= 40:
        overall_risk = "Medium"
    else:
        overall_risk = "Low"

    return {
        "candidatename": name,
        "total_questions": len(sessions),
        "avg_confidence_score": round(avg_confidence, 2),
        "avg_deception_likelihood": round(avg_deception, 2),
        "overall_risk": overall_risk
    }