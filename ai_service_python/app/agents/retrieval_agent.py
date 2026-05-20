from ..rag.knowledge_base import retrieve


class RetrievalAgent:
    def run(self, payload: dict[str, object]) -> dict[str, object]:
        query = " ".join([
            str(payload.get("prediction", "")),
            " ".join(payload.get("supporting_observations", [])),
            " ".join(payload.get("behavioral_indicators", [])),
        ])
        retrieved = retrieve(query)
        payload["retrieved_knowledge"] = retrieved
        return payload

