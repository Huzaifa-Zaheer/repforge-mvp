import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

# Standardize on string UUIDs for SQLite compatibility
class Athlete(Base):
    __tablename__ = "athletes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    experience_level = Column(String, nullable=False)
    bodyweight_kg = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    programs = relationship("Program", back_populates="athlete")
    sessions = relationship("WorkoutSession", back_populates="athlete")


class Program(Base):
    __tablename__ = "programs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    athlete_id = Column(String, ForeignKey("athletes.id"))
    methodology = Column(String, nullable=False)
    goal = Column(String, nullable=False)
    program_data = Column(JSON, nullable=False)
    current_week = Column(Integer, default=1)
    created_at = Column(DateTime, default=utc_now)
    
    athlete = relationship("Athlete", back_populates="programs")
    sessions = relationship("WorkoutSession", back_populates="program")


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    athlete_id = Column(String, ForeignKey("athletes.id"))
    program_id = Column(String, ForeignKey("programs.id"))
    exercise = Column(String, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    
    athlete = relationship("Athlete", back_populates="sessions")
    program = relationship("Program", back_populates="sessions")
    sets = relationship("WorkoutSet", back_populates="session", order_by="WorkoutSet.set_number")
    decisions = relationship("AdaptationDecision", back_populates="session")


class WorkoutSet(Base):
    __tablename__ = "workout_sets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("workout_sessions.id"))
    set_number = Column(Integer, nullable=False)
    set_type = Column(String, nullable=False)
    planned_weight_kg = Column(Float, nullable=False)
    planned_reps = Column(Integer, nullable=False)
    target_rpe = Column(Float, nullable=True)
    actual_weight_kg = Column(Float, nullable=True)
    actual_reps = Column(Integer, nullable=True)
    athlete_rpe = Column(Float, nullable=True)
    video_ref = Column(String, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    session = relationship("WorkoutSession", back_populates="sets")
    analyses = relationship("Analysis", back_populates="workout_set")


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    set_id = Column(String, ForeignKey("workout_sets.id"))
    predicted_rpe = Column(Float, nullable=False)
    technique_score = Column(Float, nullable=False)
    rom_score = Column(Float, nullable=False)
    tempo_score = Column(Float, nullable=False)
    bar_path_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    analysis_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    workout_set = relationship("WorkoutSet", back_populates="analyses")


class AdaptationDecision(Base):
    __tablename__ = "adaptation_decisions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("workout_sessions.id"))
    previous_weight_kg = Column(Float, nullable=False)
    recommended_weight_kg = Column(Float, nullable=False)
    target_rpe = Column(Float, nullable=False)
    predicted_rpe = Column(Float, nullable=False)
    expected_rpe = Column(Float, nullable=False)
    rpe_delta = Column(Float, nullable=False)
    adjustment_percent = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    session = relationship("WorkoutSession", back_populates="decisions")
