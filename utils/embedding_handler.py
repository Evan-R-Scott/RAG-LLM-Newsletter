import torch
import numpy as np
from typing import Any, Dict, List
from settings import Config, Logger

config = Config.get_instance()
logger = Logger.get_daily_logger("data_fetch")

# def map_embeddings(
#         documents: Dict[str, Dict[str, Dict[str, Any]]]
#         ) -> Dict[str, Dict[str, List[float]]]:
#     """
#     Converts the texts that were chunked from the documents into vector representations and stores those embeddings for future similarity searches by LLM/RAG

#     Args:
#         documents: dictionary storing the chunked texts of the various documents, indexed by document_id and chunk_id

#     Returns:
#         A dictionary mapping document_id -> chunk_id -> embedding vectors

#     Example:

#         documents is passed in (see docstring in parse_documents.py for structure) and something like this is returned:

#         mapped_document_db = {
#             "oaooi20kdoamd": {
#                 chunk_01: [0.1, -0.3, 0.7, ...],
#                 chunk_02: [0.2, 0.1, -0.5, ...]
#                 },
#             "oasiiainia209a": {
#                 chunk_01: [0.6, 0.2, -0.1, ...],
#                 chunk_02: [-0.4, -0.9, 0.7, ...]
#                 }
#         }
#     """

def prepare_embeddings(input: str) -> np.ndarray:
    embeddings = np.array(compute_embeddings(input))
    embeddings = normalize_vector(embeddings)
    return embeddings

def compute_embeddings(query: str) -> List[float]:
    """
    A given query (string) is converted into its equivalent embedding for future comparision

    Args:
        query: text to be tokenized
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    query_inputs = config.tokenizer(
        query,
        padding=True,
        truncation=True,
        return_tensors="pt")
    
    with torch.no_grad():
        query_embeddings = config.embedding_model(**query_inputs).last_hidden_state.mean(dim=1).squeeze()
        query_embeddings = query_embeddings.tolist()

    return query_embeddings

def normalize_vector(vector: np.array) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm