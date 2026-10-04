from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any, Dict

class ProgramBase(BaseModel):
    athlete_id: UUID
    methodology: str
    goal: str

class ProgramCreate(ProgramBase):
    pass

class ProgramResponse(ProgramBase):
    id: UUID
    program_data: Dict[str, Any]
    current_week: int
    created_at: datetime

    class Config:
        from_attributes = True
