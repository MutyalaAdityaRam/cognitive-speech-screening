from ..decision_rules import decide_risk


class DecisionAgent:
    def run(self, payload: dict[str, object]) -> dict[str, object]:
        outputs = payload["model_outputs"]
        probabilities = [float(item["risk_probability"]) for item in outputs]
        decision = decide_risk(probabilities)
        decision["model_outputs"] = outputs
        return decision

