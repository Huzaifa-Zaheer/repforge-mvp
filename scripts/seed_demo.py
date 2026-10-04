import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import SessionLocal
from app.db.models import Athlete, Program, WorkoutSession, WorkoutSet

def seed_demo_data():
    """
    Idempotent database seeding script.
    Checks for the demo athlete by name and deterministic criteria before creating.
    Creates:
    - Demo Athlete (Intermediate, 74 kg)
    - Squat program
    - Workout session
    - Warm-up 1 (120 kg, 5 reps)
    - Warm-up 2 (150 kg, 3 reps)
    - Working Set 1 (planned 180 kg, 5 reps, target RPE 8.0)
    - Working Set 2 (planned 180 kg, 5 reps, target RPE 8.0)
    """
    print("Checking / seeding demo data directly in database...")
    db = SessionLocal()
    try:
        # Check if demo athlete already exists
        athlete = db.query(Athlete).filter(Athlete.name == "Muhammad (Demo)").first()
        if not athlete:
            athlete = Athlete(
                name="Muhammad (Demo)",
                experience_level="intermediate",
                bodyweight_kg=74.0
            )
            db.add(athlete)
            db.commit()
            db.refresh(athlete)
            print(f"Created demo athlete: {athlete.id} ({athlete.name})")
        else:
            print(f"Demo athlete already exists: {athlete.id} ({athlete.name})")

        # Check if program exists for this athlete
        program = db.query(Program).filter(
            Program.athlete_id == athlete.id,
            Program.goal == "strength"
        ).first()

        if not program:
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
            program = Program(
                athlete_id=athlete.id,
                methodology="hybrid_rpe_percentage",
                goal="strength",
                program_data=program_data,
                current_week=1
            )
            db.add(program)
            db.commit()
            db.refresh(program)
            print(f"Created demo program: {program.id}")
        else:
            print(f"Demo program already exists: {program.id}")

        # Check if active demo session exists
        session = db.query(WorkoutSession).filter(
            WorkoutSession.athlete_id == athlete.id,
            WorkoutSession.program_id == program.id,
            WorkoutSession.exercise == "squat"
        ).first()

        if not session:
            session = WorkoutSession(
                athlete_id=athlete.id,
                program_id=program.id,
                exercise="squat",
                status="WARMUP_2_COMPLETE"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            print(f"Created demo workout session: {session.id}")

            # Warm-up 1
            w1 = WorkoutSet(
                session_id=session.id,
                set_number=1,
                set_type="warmup",
                planned_weight_kg=120.0,
                planned_reps=5,
                actual_weight_kg=120.0,
                actual_reps=5,
                video_ref="demo://squat/warmup-1",
                status="completed"
            )
            # Warm-up 2
            w2 = WorkoutSet(
                session_id=session.id,
                set_number=2,
                set_type="warmup",
                planned_weight_kg=150.0,
                planned_reps=3,
                actual_weight_kg=150.0,
                actual_reps=3,
                video_ref="demo://squat/warmup-2",
                status="completed"
            )
            # Working Set 1 (planned)
            ws1 = WorkoutSet(
                session_id=session.id,
                set_number=3,
                set_type="working",
                planned_weight_kg=180.0,
                planned_reps=5,
                target_rpe=8.0,
                status="planned"
            )
            # Working Set 2 (planned)
            ws2 = WorkoutSet(
                session_id=session.id,
                set_number=4,
                set_type="working",
                planned_weight_kg=180.0,
                planned_reps=5,
                target_rpe=8.0,
                status="planned"
            )
            db.add_all([w1, w2, ws1, ws2])
            db.commit()
            print("Created warm-ups and working sets for demo session.")
        else:
            print(f"Demo workout session already exists: {session.id} (status: {session.status})")

        print("Seeding demo data completed successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
