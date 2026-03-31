from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    candidatename = Column(String, default="Anonymous")
    question = Column(String)
    response_text = Column(String)
    filler_count = Column(Integer)
    hedging_count = Column(Integer)
    contradiction_count = Column(Integer)
    confidence_score = Column(Float)
    deception_likelihood = Column(Float)
    risk_level = Column(String)
    created_at = Column(DateTime, server_default=func.now())