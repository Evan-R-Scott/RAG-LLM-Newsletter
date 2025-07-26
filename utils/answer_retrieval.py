import numpy as np
from utils.embedding_handler import compute_embeddings
from settings.app_config import config
from typing import Dict, List, Tuple

def retrieve_top_k_scores(
        query:str,
        mapped_document_db:Dict[str, Dict[str, List[float]]]
        ) -> List[Tuple[str, str, float]]:
    """
    
    """
    query_embeddings = np.array(compute_embeddings(query))
    query_embeddings = normalize_vector(query_embeddings)

    scores = []

    for doc_id, document_chunks in mapped_document_db.items():
        for chunk_id, chunk_embeddings in document_chunks.items():

            chunk_embeddings = np.array(chunk_embeddings)
            chunk_embeddings = normalize_vector(chunk_embeddings)
            cosine_similarity_score = np.dot(query_embeddings, chunk_embeddings)
            scores.append((doc_id, chunk_id, cosine_similarity_score))

    scores.sort(key=lambda x: x[2], reverse=True)

    return scores[:config.top_k]

def normalize_vector(vector: np.array) -> float:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm