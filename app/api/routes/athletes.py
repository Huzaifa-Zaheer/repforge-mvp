from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.db.models import Athlete
from app.schemas.athlete import AthleteCreate, AthleteResponse

router = APIRouter()

@router.post("/", response_model=AthleteResponse)
def create_athlete(athlete_in: AthleteCreate, db: Session = Depends(get_db)):
    db_athlete = Athlete(**athlete_in.model_dump())
    db.add(db_athlete)
    db.commit()
    db.refresh(db_athlete)
    return db_athlete

@router.get("/{athlete_id}", response_model=AthleteResponse)
def get_athlete(athlete_id: str, db: Session = Depends(get_db)):
    db_athlete = db.query(Athlete).filter(Athlete.id == athlete_id).first()
    if not db_athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return db_athlete
