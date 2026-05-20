import numpy as np
import pandas as pd

# Set deterministic seeds for reproducibility
np.random.seed(42)

from ..model_assets import load_models


class PredictionAgent:
    def run(self, payload: dict[str, object]) -> dict[str, object]:
        features = payload["features"]
        if not isinstance(features, pd.DataFrame):
            raise TypeError("PredictionAgent expects a pandas DataFrame.")

        # Ensure deterministic prediction order
        np.random.seed(42)
        
        model1, model2 = load_models()
        # CRITICAL FIX: Use [0][0] for Class 0 (dementia/high-risk probability)
        # Previously used [0][1] which incorrectly represented non_dementia/low-risk
        # Set verbose=0 and disable any randomness in model inference
        prob1_array = model1.predict_proba(features)
        prob2_array = model2.predict_proba(features)
        
        # Extract dementia probability (Class 0) deterministically
        prob1 = float(prob1_array[0][0]) if len(prob1_array) > 0 else 0.0
        prob2 = float(prob2_array[0][0]) if len(prob2_array) > 0 else 0.0
        final_probability = 0.6 * prob2 + 0.4 * prob1
        prediction = "High Risk" if final_probability >= 0.5 else "Low Risk"
        return {
            "prob1": prob1,
            "prob2": prob2,
            "final_probability": final_probability,
            "confidence": final_probability,
            "prediction": prediction,
            "risk_level": prediction,
            "model_outputs": [
                {"model_name": "model_1_pipeline", "probability": prob1},
                {"model_name": "model_2_ensemble", "probability": prob2},
            ],
        }

