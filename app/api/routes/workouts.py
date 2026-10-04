from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db, SessionLocal
from app.db.models import WorkoutSession, WorkoutSet, Program, Analysis, AdaptationDecision, Athlete
from app.schemas.workout import (
    WorkoutSessionCreate, WorkoutSessionResponse, 
    WorkoutSetCreate, WorkoutSetResponse, 
    WorkoutSetComplete, RecommendationResponse
)
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.jobs import JobService
from app.services.mock_ai import MockVisionService, MockRPEModel, MockTechniqueAnalyzer, MockCoach
from app.services.adaptation import AdaptiveLoadEngine

router = APIRouter()

@router.post("/", response_model=WorkoutSessionResponse)
def start_workout(workout_in: WorkoutSessionCreate, db: Session = Depends(get_db)):
    program = db.query(Program).filter(Program.id == str(workout_in.program_id)).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
        
    athlete = db.query(Athlete).filter(Athlete.id == str(workout_in.athlete_id)).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
        
    session = WorkoutSession(
        athlete_id=str(workout_in.athlete_id),
        program_id=str(workout_in.program_id),
        exercise=workout_in.exercise,
        status="CREATED"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/{session_id}", response_model=WorkoutSessionResponse)
def get_workout(session_id: str, db: Session = Depends(get_db)):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/{session_id}/sets", response_model=WorkoutSetResponse)
def create_set(session_id: str, set_in: WorkoutSetCreate, db: Session = Depends(get_db)):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status == "COMPLETED":
        raise HTTPException(status_code=409, detail="Session is already completed")
        
    # State validation
    if set_in.set_number == 1 and session.status != "CREATED":
        pass # allow recovery or repeated creation? For MVP let's just allow it
        
    db_set = WorkoutSet(
        session_id=session_id,
        set_number=set_in.set_number,
        set_type=set_in.set_type,
        planned_weight_kg=set_in.weight_kg,
        planned_reps=set_in.reps,
        target_rpe=set_in.target_rpe,
        actual_weight_kg=set_in.weight_kg,  # assumed same for submission endpoint per MVP requirements, actual values could be passed here
        actual_reps=set_in.reps,
        video_ref=set_in.video_ref,
        status="completed" if set_in.set_type == "warmup" else "planned"
    )
    db.add(db_set)
    
    if set_in.set_number == 1:
        session.status = "WARMUP_1_COMPLETE"
    elif set_in.set_number == 2:
        session.status = "WARMUP_2_COMPLETE"
    elif set_in.set_number == 3:
        session.status = "WORKING_SET_1_COMPLETE"
        
    db.commit()
    db.refresh(db_set)
    return db_set

def run_analysis_task(job_id: str, set_ids: list, session_id: str):
    try:
        JobService.update_job(job_id, "PROCESSING")
        
        db = SessionLocal()
        session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
        
        last_rpe = None
        for set_id in set_ids:
            w_set = db.query(WorkoutSet).filter(WorkoutSet.id == set_id).first()
            if not w_set:
                continue
                
            # MOCK AI Logic
            vision_result = MockVisionService.analyze_video(w_set.video_ref)
            
            # Simple assumption for expected RPE based on load
            expected_rpe = 5.5 if w_set.planned_weight_kg < 140 else 6.5
            ai_rpe = MockRPEModel.predict_rpe(w_set.actual_weight_kg, w_set.actual_reps, expected_rpe)
            last_rpe = ai_rpe
            
            technique = MockTechniqueAnalyzer.analyze_technique()
            
            analysis = Analysis(
                set_id=w_set.id,
                predicted_rpe=ai_rpe,
                technique_score=technique["technique_score"],
                rom_score=technique["rom_score"],
                tempo_score=technique["tempo_score"],
                bar_path_score=technique["bar_path_score"],
                confidence=0.95,
                analysis_payload={"vision": vision_result, "technique": technique}
            )
            db.add(analysis)
        
        session.status = "READY_FOR_WORKING_SET"
        db.commit()
        
        JobService.update_job(job_id, "COMPLETED", result={"predicted_rpe_latest": last_rpe, "status": "Ready for working set"})
    except Exception as e:
        JobService.update_job(job_id, "FAILED", result={"error": str(e)})


@router.post("/{session_id}/analyze", status_code=202, response_model=AnalysisResponse)
def trigger_analysis(session_id: str, request: AnalysisRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status not in ["WARMUP_2_COMPLETE", "WORKING_SET_1_COMPLETE"]:
        raise HTTPException(status_code=409, detail="Not ready for analysis")
        
    session.status = "READY_FOR_ANALYSIS"
    db.commit()
    
    job_id = JobService.create_job()
    background_tasks.add_task(run_analysis_task, job_id, [str(uid) for uid in request.set_ids], session_id)
    
    return {"job_id": job_id, "status": "queued"}

@router.get("/{session_id}/recommendation", response_model=RecommendationResponse)
def get_recommendation(session_id: str, db: Session = Depends(get_db)):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status != "READY_FOR_WORKING_SET":
        raise HTTPException(status_code=409, detail="Analysis incomplete for current session")
        
    # Get last warmup set
    warmups = db.query(WorkoutSet).filter(WorkoutSet.session_id == session_id, WorkoutSet.set_type == "warmup").order_by(WorkoutSet.set_number.desc()).all()
    if not warmups:
        raise HTTPException(status_code=404, detail="No warmups found to base recommendation on")
        
    last_warmup = warmups[0]
    last_analysis = db.query(Analysis).filter(Analysis.set_id == last_warmup.id).first()
    
    if not last_analysis:
        raise HTTPException(status_code=409, detail="Analysis missing for last warmup")
        
    expected_rpe = 6.5
    predicted_rpe = last_analysis.predicted_rpe
    
    program = session.program
    planned_work = program.program_data.get("working_set", {})
    planned_weight = planned_work.get("weight_kg", 180)
    target_rpe = planned_work.get("target_rpe", 8.0)
    
    decision = AdaptiveLoadEngine.calculate_adjustment(planned_weight, expected_rpe, predicted_rpe)
    
    db_decision = AdaptationDecision(
        session_id=session_id,
        previous_weight_kg=planned_weight,
        recommended_weight_kg=decision["recommended_weight_kg"],
        target_rpe=target_rpe,
        predicted_rpe=predicted_rpe,
        expected_rpe=expected_rpe,
        rpe_delta=decision["rpe_delta"],
        adjustment_percent=decision["adjustment_percent"],
        reason=decision["reason"]
    )
    db.add(db_decision)
    db.commit()
    
    return {
        "exercise": session.exercise,
        "previous_plan": planned_work,
        "recommendation": {
            "weight_kg": decision["recommended_weight_kg"],
            "reps": planned_work.get("reps", 5),
            "target_rpe": target_rpe
        },
        "predicted_rpe": predicted_rpe,
        "adjustment_kg": decision["recommended_weight_kg"] - planned_weight,
        "reason": MockCoach.generate_explanation(decision["reason"])
    }

@router.post("/{session_id}/sets/{set_id}/complete")
def complete_working_set(session_id: str, set_id: str, data: WorkoutSetComplete, db: Session = Depends(get_db)):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    w_set = db.query(WorkoutSet).filter(WorkoutSet.id == set_id, WorkoutSet.session_id == session_id).first()
    if not w_set:
        raise HTTPException(status_code=404, detail="Set not found")
        
    if w_set.status == "completed":
        raise HTTPException(status_code=409, detail="Set already completed")
        
    w_set.actual_weight_kg = data.weight_kg
    w_set.actual_reps = data.reps
    w_set.athlete_rpe = data.athlete_rpe
    w_set.video_ref = data.video_ref
    w_set.status = "completed"
    
    session.status = "COMPLETED"
    
    # Mock AI analysis for working set
    ai_rpe = MockRPEModel.predict_rpe(data.weight_kg, data.reps, w_set.target_rpe or 8.0)
    
    db.commit()
    
    status = "on_target" if abs(ai_rpe - (w_set.target_rpe or 8.0)) < 0.5 else ("above_target" if ai_rpe > (w_set.target_rpe or 8.0) else "below_target")
    next_action = "hold_load" if status == "on_target" else ("reduce_next_set" if status == "above_target" else "increase_next_set")
    
    return {
        "observed_rpe": data.athlete_rpe,
        "ai_rpe": ai_rpe,
        "target_rpe": w_set.target_rpe,
        "status": status,
        "next_action": next_action
    }
