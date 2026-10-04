import time

def test_full_workflow(client):
    # 1. Create Athlete
    response = client.post("/api/v1/athletes/", json={
        "name": "Test Athlete",
        "experience_level": "intermediate",
        "bodyweight_kg": 80.0
    })
    assert response.status_code == 200
    athlete_id = response.json()["id"]
    
    # 2. Create Program
    response = client.post("/api/v1/programs/", json={
        "athlete_id": athlete_id,
        "methodology": "hybrid_rpe_percentage",
        "goal": "strength"
    })
    assert response.status_code == 200
    program_id = response.json()["id"]
    
    # 3. Start Workout
    response = client.post("/api/v1/workouts/", json={
        "athlete_id": athlete_id,
        "program_id": program_id,
        "exercise": "squat"
    })
    assert response.status_code == 200
    session_id = response.json()["id"]
    
    # 4. Submit Warmup 1
    response = client.post(f"/api/v1/workouts/{session_id}/sets", json={
        "set_number": 1,
        "set_type": "warmup",
        "weight_kg": 120.0,
        "reps": 5,
        "video_ref": "demo://squat/warmup-1"
    })
    assert response.status_code == 200
    set1_id = response.json()["id"]
    
    # 5. Submit Warmup 2 (150kg to trigger BAD_DAY in mock)
    response = client.post(f"/api/v1/workouts/{session_id}/sets", json={
        "set_number": 2,
        "set_type": "warmup",
        "weight_kg": 150.0,
        "reps": 3,
        "video_ref": "demo://squat/warmup-2"
    })
    assert response.status_code == 200
    set2_id = response.json()["id"]
    
    # 6. Analyze
    response = client.post(f"/api/v1/workouts/{session_id}/analyze", json={
        "set_ids": [set1_id, set2_id]
    })
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    
    # Wait for background task
    time.sleep(1)
    
    # 7. Check Job Status
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    job_data = response.json()
    if job_data["status"] != "COMPLETED":
        print(f"Job failed: {job_data}")
    assert job_data["status"] == "COMPLETED"
    
    # 8. Get Recommendation
    response = client.get(f"/api/v1/workouts/{session_id}/recommendation")
    assert response.status_code == 200
    data = response.json()
    assert data["adjustment_kg"] < 0  # Should reduce weight due to BAD_DAY
    
    # 9. Create Working Set
    response = client.post(f"/api/v1/workouts/{session_id}/sets", json={
        "set_number": 3,
        "set_type": "working",
        "weight_kg": data["recommendation"]["weight_kg"],
        "reps": 5,
        "target_rpe": 8.0
    })
    assert response.status_code == 200
    work_set_id = response.json()["id"]

    # 10. Complete Working Set
    response = client.post(f"/api/v1/workouts/{session_id}/sets/{work_set_id}/complete", json={
        "weight_kg": data["recommendation"]["weight_kg"],
        "reps": 5,
        "athlete_rpe": 8.0,
        "video_ref": "demo://squat/working-1"
    })
    assert response.status_code == 200
    assert "next_action" in response.json()

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_state_machine_conflict_invalid_recommendation(client):
    # Create Athlete
    response = client.post("/api/v1/athletes/", json={
        "name": "State Test Athlete",
        "experience_level": "advanced",
        "bodyweight_kg": 90.0
    })
    assert response.status_code == 200
    athlete_id = response.json()["id"]

    # Create Program
    response = client.post("/api/v1/programs/", json={
        "athlete_id": athlete_id,
        "methodology": "linear",
        "goal": "strength"
    })
    assert response.status_code == 200
    program_id = response.json()["id"]

    # Start Workout
    response = client.post("/api/v1/workouts/", json={
        "athlete_id": athlete_id,
        "program_id": program_id,
        "exercise": "squat"
    })
    assert response.status_code == 200
    session_id = response.json()["id"]

    # Immediately request recommendation before warm-ups/analysis -> Expect 409 Conflict
    rec_response = client.get(f"/api/v1/workouts/{session_id}/recommendation")
    assert rec_response.status_code == 409
    assert "Analysis incomplete" in rec_response.json()["detail"]

