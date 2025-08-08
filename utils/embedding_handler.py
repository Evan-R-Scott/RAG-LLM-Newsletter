from torch import no_grad
import numpy as np
from typing import List
from settings import Config, Logger

config = Config.get_instance()
daily_logger = Logger.get_daily_logger("data_fetch")


def prepare_embeddings(input: str) -> np.ndarray:
    """
    Entrypoint for the embedding computation

    Args:
        input: query to be embedded
    
    Returns:
        normalized embedding of the provided input
    """
    embeddings = np.array(compute_embeddings(input))
    embeddings = normalize_vector(embeddings)
    return embeddings

def compute_embeddings(query: str) -> List[float]:
    """
    Converts a given query into its embedding equivalent using BAAI/bge-small-en-v1.5

    Args:
        query: text to be tokenized into its vector representation
    
    Returns:
        embedding of the query
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # converts text input into tokens
    query_inputs = config.tokenizer(
        query,
        padding=True,
        truncation=True,
        return_tensors="pt")
    
    # creates vector embeddings of the tokens
    with no_grad():
        query_embeddings = config.embedding_model(**query_inputs).last_hidden_state.mean(dim=1).squeeze()
        query_embeddings = query_embeddings.tolist()

    return query_embeddings

def normalize_vector(vector: np.array) -> np.ndarray:
    """
    Normalization portion of cosine similarity to avoid repetitive computations during runtime
    """
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm