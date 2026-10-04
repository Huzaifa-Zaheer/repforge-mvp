from fastapi import FastAPI
from app.core.config import settings

from app.api.routes import athletes, programs, workouts, jobs

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(athletes.router, prefix="/api/v1/athletes", tags=["athletes"])
app.include_router(programs.router, prefix="/api/v1/programs", tags=["programs"])
app.include_router(workouts.router, prefix="/api/v1/workouts", tags=["workouts"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])

@app.get("/")
def root():
    return {"message": "Welcome to RepForge API"}

@app.get("/health")
def health():
    return {"status": "ok"}

