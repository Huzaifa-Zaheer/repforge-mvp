from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class WorkoutSessionCreate(BaseModel):
    athlete_id: UUID
    program_id: UUID
    exercise: str

class WorkoutSessionResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    program_id: UUID
    exercise: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WorkoutSetCreate(BaseModel):
    set_number: int
    set_type: str # warmup, working
    weight_kg: float
    reps: int
    target_rpe: Optional[float] = None
    video_ref: Optional[str] = None

class WorkoutSetComplete(BaseModel):
    weight_kg: float
    reps: int
    video_ref: Optional[str] = None
    athlete_rpe: Optional[float] = None

class WorkoutSetResponse(BaseModel):
    id: UUID
    session_id: UUID
    set_number: int
    set_type: str
    planned_weight_kg: float
    planned_reps: int
    target_rpe: Optional[float] = None
    actual_weight_kg: Optional[float] = None
    actual_reps: Optional[float] = None
    athlete_rpe: Optional[float] = None
    video_ref: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    exercise: str
    previous_plan: dict
    recommendation: dict
    predicted_rpe: float
    adjustment_kg: float
    reason: str
