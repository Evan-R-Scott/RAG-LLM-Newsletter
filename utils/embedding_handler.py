import torch
from typing import Any, Dict, List
from config import config

def map_embeddings(
        documents: Dict[str, Dict[str, Dict[str, Any]]]
        ) -> Dict[str, Dict[str, List[float]]]:
    """
    Converts the texts that were chunked from the documents into vector representations and stores those embeddings for future similarity searches by LLM/RAG

    Args:
        documents: dictionary storing the chunked texts of the various documents, indexed by document_id and chunk_id

    Returns:
        A dictionary mapping document_id -> chunk_id -> embedding vectors

    Example:

        documents is passed in (see docstring in parse_documents.py for structure) and something like this is returned:

        mapped_document_db = {
            "oaooi20kdoamd": {
                chunk_01: [0.1, -0.3, 0.7, ...],
                chunk_02: [0.2, 0.1, -0.5, ...]
                },
            "oasiiainia209a": {
                chunk_01: [0.6, 0.2, -0.1, ...],
                chunk_02: [-0.4, -0.9, 0.7, ...]
                }
        }
    """
    mapped_document_db = {}
    for doc_id, document_chunks in documents.items():
        mapped_embeddings = {}
        for chunk_id, chunk_content in document_chunks.items():
            text = chunk_content.get("text")
            
            if not text or not text.strip():
                # add logging
                print(f"Empty text found for {doc_id}/{chunk_id}")
                continue

            encoded_input = config.tokenizer(
                text,
                padding=True,
                truncation=True,
                return_tensors="pt")
            
            with torch.no_grad():
                embeddings = config.embedding_model(**encoded_input).last_hidden_state.mean(dim=1).squeeze().tolist()

            mapped_embeddings[chunk_id] = embeddings
        mapped_document_db[doc_id] = mapped_embeddings
    print(f"Generated embeddings for {len(mapped_document_db)} documents")
    return mapped_document_db

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