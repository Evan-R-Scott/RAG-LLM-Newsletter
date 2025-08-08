import joblib
import numpy as np
from typing import Optional, List, Dict
import os
from settings import Config, Logger

config = Config.get_instance()
daily_logger = Logger.get_daily_logger("data_fetch")
runtime_logger = Logger.get_runtime_logger("chatbot")

class VectorStore:
    """
    Singleton
    A store for Chunk objects which simulates the capabilities of a typical Vector DB
    """
    _instance: Optional['VectorStore'] = None
    _initialized: bool = False

    def __init__(self):
        if not VectorStore._initialized:
            self.data: Optional[Dict[str, List['Chunk']]] = {}
            VectorStore._initialized = True
    
    def __new__(cls) -> 'VectorStore':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def add_chunks(self, doc_id: str, chunks: List['Chunk']) -> None:
        if doc_id in self.data:
            self.data[doc_id].extend(chunks)
        else:
            self.data[doc_id] = chunks
    
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b)
    
    def retrieve_top_k(self, query_embedding: np.ndarray) -> Optional[List['Chunk']]:
        """
        Performs cosine similarity to retrieve the top_k articles that are most relavant to the user's query
        """
        similars = []
        for doc_id, document in self.data.items():
            for chunk in document:
                similarity_score = self.cosine_similarity(query_embedding, chunk.embeddings)
                chunk.set_similarity_score(similarity_score)
                similars.append((doc_id, chunk, similarity_score))

        # sort in descending order to access most similar articles first
        similars.sort(key=lambda x: x[2], reverse=True)

        results = []
        for doc_id, chunk, similarity_score in similars[:config.top_k]:
            if similarity_score < 0.3:
                break
            results.append(chunk)
        return results

    @classmethod
    def get_instance(cls) -> 'VectorStore':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        cls._instance = None
        cls._initialized = False
    

    def save(self) -> None: # Run at end of preprocessing when building the VectorStore
        try:
            if self.data:
                joblib.dump(self.data, config.vector_store, compress=3)
                daily_logger.info(f"Wrote {len(self.data)} documents out to {config.vector_store}")
                file_size = os.path.getsize(config.vector_store)
                daily_logger.info(f"VectorStore is {file_size} bytes")
            else:
                daily_logger.warning(f"Cannot save to {config.vector_store} because VectorStore has no contents.")
        except (OSError, TypeError) as e:
            daily_logger.error(f"Error saving to {config.vector_store}: {e}")

    def load(self) -> None: # Run at container startup to load VectorStore in for use at runtime
        try:
            self.data = joblib.load(config.vector_store)
            runtime_logger.info(f"Loaded {len(self.data)} documents from {config.vector_store}")
        except FileNotFoundError as e:
            runtime_logger.error(f"Error reading VectorStore from {config.vector_store}: {e}")


class Chunk:
    """
    For this use case, a Chunk object could be more accurately named an Article object since I developed the chunking algorithm such that newsletter data was chunked by articles to retain all relevant information and get a better holistic view for the LLM but I left it named Chunk for the sake of RAG terminology.
    """
    def __init__(self, id: str, newsletter: str, url: str, title: Optional[str], text: Optional[str], embeddings: Optional[List[int]]):
        self.id=id
        self.newsletter=newsletter
        self.url = url
        self.title=title
        self.text=text
        self.embeddings=embeddings
        self.similarity_score: Optional[float]=None
    
    def set_newsletter(self, newsletter: str) -> None:
        self.newsletter=newsletter

    def set_title(self, title:str) -> None:
        self.title=title

    def set_text(self, text: str) -> None:
        self.text=text
    
    def set_embedding(self, embeddings: List[int]) -> None:
        self.embeddings=embeddings

    def set_similarity_score(self, score: float) -> None:
        self.similarity_score=score
