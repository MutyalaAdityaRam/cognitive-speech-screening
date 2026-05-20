import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from pathlib import Path
import json
from functools import lru_cache

KNOWLEDGE_BASE = [
    "Longer and more frequent pauses are commonly discussed as speech markers related to cognitive load and reduced verbal fluency in cognitive screening contexts.",
    "Reduced speech rate can be consistent with slowed word retrieval, planning effort, or reduced fluency in screening contexts.",
    "Lower lexical diversity may indicate restricted word choice, but must be interpreted with task, education, language, and recording context.",
    "Hesitations and fillers (um, uh, like) may reflect word-finding effort, uncertainty, or recording-task effects.",
    "MFCC (Mel-Frequency Cepstral Coefficients) patterns in speech can capture acoustic characteristics that may be associated with cognitive changes.",
    "This system is an AI-assisted cognitive screening tool and not a medical diagnosis. Please consult a qualified healthcare professional.",
    "Speech-based cognitive screening is a supportive tool and should never replace clinical evaluation.",
    "Cognitive decline markers in speech may include changes in fluency, syntax, vocabulary, and acoustic features.",
    "Dementia and cognitive decline screening requires comprehensive clinical assessment.",
    "Speech markers alone are not sufficient for diagnosis of dementia or any cognitive condition.",
    "Clinical speech findings in cognitive screening include reduced phrase length, increased pauses, and word-finding difficulties.",
    "Safe healthcare explanations emphasize that screening tools are adjuncts to professional care.",
    "Healthcare disclaimers are mandatory to prevent misinterpretation of AI-assisted screening results.",
    "Cognitive speech screening provides insights that should be discussed with a qualified healthcare provider.",
    "Linguistic decline patterns may involve simplified syntax, reduced vocabulary, and increased repetitions.",
]

@lru_cache(maxsize=1)
def get_rag_resources():
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(KNOWLEDGE_BASE)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    return model, index

def retrieve(query: str, top_k: int = 4, max_distance: float = 1.25) -> List[str]:
    if not (query or "").strip():
        return []
    model, index = get_rag_resources()
    query_embedding = model.encode([query])
    distances, indices = index.search(np.array(query_embedding).astype('float32'), top_k)
    results = []
    for distance, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(KNOWLEDGE_BASE):
            if float(distance) > max_distance:
                continue
            results.append(KNOWLEDGE_BASE[idx])
    return results

GROUNDING = [{"topic": "default", "text": item} for item in KNOWLEDGE_BASE]
