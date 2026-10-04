from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class AthleteBase(BaseModel):
    name: str
    experience_level: str
    bodyweight_kg: float

class AthleteCreate(AthleteBase):
    pass

class AthleteResponse(AthleteBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
