from typing import Dict, Any

class MockVisionService:
    @staticmethod
    def analyze_video(video_ref: str) -> Dict[str, Any]:
        return {
            "exercise": "squat",
            "movement_detected": True,
            "frames_analyzed": 120
        }

class MockRPEModel:
    @staticmethod
    def predict_rpe(weight_kg: float, reps: int, expected_rpe: float) -> float:
        # A simple deterministic mock. If expected is 6.5, we return 7.5 to simulate "BAD_DAY"
        # Let's say if weight_kg == 150, we return expected_rpe + 1.0 (harder)
        # Otherwise if 120 we return expected_rpe + 0.5
        if weight_kg == 150:
            return expected_rpe + 1.0
        elif weight_kg == 120:
            return expected_rpe + 0.5
        return expected_rpe

class MockTechniqueAnalyzer:
    @staticmethod
    def analyze_technique() -> Dict[str, float]:
        return {
            "technique_score": 91,
            "rom_score": 95,
            "tempo_score": 88,
            "bar_path_score": 90
        }

class MockCoach:
    @staticmethod
    def generate_explanation(reason: str) -> str:
        return f"Coach explanation: {reason}"
