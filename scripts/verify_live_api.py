import time
import httpx

BASE_URL = "https://three-hands-smile.loca.lt"
HEADERS = {"bypass-tunnel-reminder": "true"}

def test_live_workflow():
    client = httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=15.0)

    print("--- 1. Checking /health ---")
    r = client.get("/health")
    print(f"/health response: {r.status_code} -> {r.json()}")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    print("--- 2. Checking /docs ---")
    r = client.get("/docs")
    print(f"/docs response status: {r.status_code}")
    assert r.status_code == 200

    print("--- 3. Create Athlete ---")
    r = client.post("/api/v1/athletes/", json={
        "name": "Live Cloud Athlete",
        "experience_level": "intermediate",
        "bodyweight_kg": 74.0
    })
    r.raise_for_status()
    athlete_id = r.json()["id"]
    print(f"Athlete ID: {athlete_id}")

    print("--- 4. Create Program ---")
    r = client.post("/api/v1/programs/", json={
        "athlete_id": athlete_id,
        "methodology": "hybrid_rpe_percentage",
        "goal": "strength"
    })
    r.raise_for_status()
    program_id = r.json()["id"]
    print(f"Program ID: {program_id}")

    print("--- 5. Start Workout Session ---")
    r = client.post("/api/v1/workouts/", json={
        "athlete_id": athlete_id,
        "program_id": program_id,
        "exercise": "squat"
    })
    r.raise_for_status()
    session_id = r.json()["id"]
    print(f"Session ID: {session_id} (Status: {r.json()['status']})")

    print("--- 6. State Machine Verification: Premature Recommendation Check ---")
    r_bad = client.get(f"/api/v1/workouts/{session_id}/recommendation")
    print(f"Premature recommendation status code: {r_bad.status_code} ({r_bad.json()['detail']})")
    assert r_bad.status_code == 409

    print("--- 7. Submit Warm-up 1 ---")
    r = client.post(f"/api/v1/workouts/{session_id}/sets", json={
        "set_number": 1,
        "set_type": "warmup",
        "weight_kg": 120.0,
        "reps": 5,
        "video_ref": "demo://squat/warmup-1"
    })
    r.raise_for_status()
    set1_id = r.json()["id"]
    print(f"Warm-up 1 ID: {set1_id}")

    print("--- 8. Submit Warm-up 2 (150 kg triggers BAD_DAY RPE) ---")
    r = client.post(f"/api/v1/workouts/{session_id}/sets", json={
        "set_number": 2,
        "set_type": "warmup",
        "weight_kg": 150.0,
        "reps": 3,
        "video_ref": "demo://squat/warmup-2"
    })
    r.raise_for_status()
    set2_id = r.json()["id"]
    print(f"Warm-up 2 ID: {set2_id}")

    print("--- 9. Trigger Asynchronous Analysis Job ---")
    r = client.post(f"/api/v1/workouts/{session_id}/analyze", json={
        "set_ids": [set1_id, set2_id]
    })
    r.raise_for_status()
    job_id = r.json()["job_id"]
    print(f"Job triggered: {job_id} (Initial status: {r.json()['status']})")

    print("--- 10. Poll Job Status ---")
    for _ in range(5):
        time.sleep(1)
        r = client.get(f"/api/v1/jobs/{job_id}")
        r.raise_for_status()
        status = r.json()["status"]
        print(f"Polled job status: {status}")
        if status == "COMPLETED":
            break
    assert status == "COMPLETED"

    print("--- 11. Request Recommendation & Adaptive Load ---")
    r = client.get(f"/api/v1/workouts/{session_id}/recommendation")
    r.raise_for_status()
    rec_data = r.json()
    print(f"Recommended Weight: {rec_data['recommendation']['weight_kg']} kg")
    print(f"Predicted RPE: {rec_data['predicted_rpe']}")
    print(f"Adjustment: {rec_data['adjustment_kg']} kg")
    assert rec_data["adjustment_kg"] < 0  # 180kg planned -> -5% -> rounded
    assert rec_data["recommendation"]["weight_kg"] < 180.0

    print("--- 12. Create Working Set ---")
    r = client.post(f"/api/v1/workouts/{session_id}/sets", json={
        "set_number": 3,
        "set_type": "working",
        "weight_kg": rec_data["recommendation"]["weight_kg"],
        "reps": 5,
        "target_rpe": 8.0
    })
    r.raise_for_status()
    work_set_id = r.json()["id"]
    print(f"Working Set ID: {work_set_id}")

    print("--- 13. Complete Working Set ---")
    r = client.post(f"/api/v1/workouts/{session_id}/sets/{work_set_id}/complete", json={
        "weight_kg": rec_data["recommendation"]["weight_kg"],
        "reps": 5,
        "athlete_rpe": 8.0,
        "video_ref": "demo://squat/working-1"
    })
    r.raise_for_status()
    complete_data = r.json()
    print(f"Set completed! Next Action: {complete_data['next_action']}, AI RPE: {complete_data['ai_rpe']}")

    print("--- 14. Verify Final Workout Session Status ---")
    r = client.get(f"/api/v1/workouts/{session_id}")
    r.raise_for_status()
    print(f"Final Session Status: {r.json()['status']}")
    assert r.json()["status"] == "COMPLETED"

    print("\n>>> LIVE WORKFLOW FULLY VERIFIED ON PUBLIC URL! <<<")

if __name__ == "__main__":
    test_live_workflow()
