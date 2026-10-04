from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.db.models import Program, Athlete
from app.schemas.program import ProgramCreate, ProgramResponse

router = APIRouter()

@router.post("/", response_model=ProgramResponse)
def create_program(program_in: ProgramCreate, db: Session = Depends(get_db)):
    # Check if athlete exists
    athlete = db.query(Athlete).filter(Athlete.id == str(program_in.athlete_id)).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
        
    # Generate program data using a "HybridRPEPercentageStrategy" concept for the MVP
    program_data = {
        "exercise": "squat",
        "warmups": [
            {"weight_kg": 120, "reps": 5},
            {"weight_kg": 150, "reps": 3}
        ],
        "working_set": {
            "weight_kg": 180,
            "reps": 5,
            "target_rpe": 8.0
        }
    }
    
    db_program = Program(
        athlete_id=str(program_in.athlete_id),
        methodology=program_in.methodology,
        goal=program_in.goal,
        program_data=program_data
    )
    db.add(db_program)
    db.commit()
    db.refresh(db_program)
    return db_program

@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(program_id: str, db: Session = Depends(get_db)):
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program
