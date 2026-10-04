from math import floor
from app.db import models

class AdaptiveLoadEngine:
    @staticmethod
    def calculate_adjustment(planned_weight_kg: float, expected_rpe: float, predicted_rpe: float) -> dict:
        delta = predicted_rpe - expected_rpe
        
        # Bounded logic:
        # delta <= -0.5 -> +2.5%
        # -0.5 < delta < +0.5 -> 0%
        # +0.5 <= delta < +1.0 -> -2.5%
        # delta >= +1.0 -> -5%
        
        if delta <= -0.5:
            adjustment_percent = 2.5
            reason = "Warm-up performance was easier than expected."
        elif delta >= 1.0:
            adjustment_percent = -5.0
            reason = "Warm-up performance indicates higher-than-expected effort."
        elif delta >= 0.5:
            adjustment_percent = -2.5
            reason = "Warm-up effort was slightly higher than expected."
        else:
            adjustment_percent = 0.0
            reason = "Warm-up effort was on target."
        
        new_weight = planned_weight_kg * (1 + (adjustment_percent / 100))
        
        # Round to nearest 2.5kg
        rounded_weight = round(new_weight / 2.5) * 2.5
        
        return {
            "recommended_weight_kg": rounded_weight,
            "adjustment_percent": adjustment_percent,
            "rpe_delta": delta,
            "reason": reason
        }
