import httpx, time
BASE_URL = 'http://localhost:8000/api/v1'

def run():
    # Get session
    r = httpx.post(f'{BASE_URL}/athletes/', json={'name': 'Demo', 'experience_level': 'intermediate', 'bodyweight_kg': 80})
    athlete_id = r.json()['id']
    
    r = httpx.post(f'{BASE_URL}/programs/', json={'athlete_id': athlete_id, 'methodology': 'hybrid', 'goal': 'strength'})
    program_id = r.json()['id']
    
    r = httpx.post(f'{BASE_URL}/workouts/', json={'athlete_id': athlete_id, 'program_id': program_id, 'exercise': 'squat'})
    session_id = r.json()['id']
    
    # warmups
    r = httpx.post(f'{BASE_URL}/workouts/{session_id}/sets', json={'set_number': 1, 'set_type': 'warmup', 'weight_kg': 120, 'reps': 5})
    w1 = r.json()['id']
    
    r = httpx.post(f'{BASE_URL}/workouts/{session_id}/sets', json={'set_number': 2, 'set_type': 'warmup', 'weight_kg': 150, 'reps': 3})
    w2 = r.json()['id']
    
    # analyze
    r = httpx.post(f'{BASE_URL}/workouts/{session_id}/analyze', json={'set_ids': [w1, w2]})
    time.sleep(2)
    
    # recommend
    r = httpx.get(f'{BASE_URL}/workouts/{session_id}/recommendation')
    print('RESULT:', r.json())

run()
