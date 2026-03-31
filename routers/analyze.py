from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.schemas import InterviewSession
from pydantic import BaseModel

router = APIRouter()

class InterviewRequest(BaseModel):
    candidatename: str = "Anonymous"
    question: str
    response_text: str

@router.post("/analyze")
def analyze(request: InterviewRequest, db: Session = Depends(get_db)):
    text = request.response_text
    text_lower = text.lower()

    filler_words = ["um", "uh", "like", "you know", "basically", "literally"]
    found_fillers = [word for word in filler_words if word in text_lower]

    hedging_words = ["i think", "i believe", "maybe", "perhaps", "i guess", "probably", "not sure", "i feel like"]
    found_hedging = [word for word in hedging_words if word in text_lower]

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

    total_signals = len(found_fillers) + len(found_hedging) + len(contradictions_found)
    confidence_score = max(0, 100 - (total_signals * 10) - length_penalty)
    deception_likelihood = 100 - confidence_score

    if deception_likelihood >= 70:
        risk_level = "High"
    elif deception_likelihood >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    signals = []
    if len(found_fillers) > 0:
        signals.append(f"{len(found_fillers)} filler word(s) detected")
    if len(found_hedging) > 0:
        signals.append(f"{len(found_hedging)} hedging word(s) detected")
    if len(contradictions_found) > 0:
        signals.append(f"Contradiction found: {', '.join(contradictions_found)}")
    if word_count < 10:
        signals.append("Response too short")

    session = InterviewSession(
        candidatename=request.candidatename,
        question=request.question,
        response_text=text,
        filler_count=len(found_fillers),
        hedging_count=len(found_hedging),
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
        "filler_count": len(found_fillers),
        "hedging_words_found": found_hedging,
        "hedging_count": len(found_hedging),
        "contradictions_found": contradictions_found,
        "contradiction_count": len(contradictions_found),
        "confidence_score": confidence_score,
        "deception_likelihood": deception_likelihood,
        "risk_level": risk_level,
        "signals": signals
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
