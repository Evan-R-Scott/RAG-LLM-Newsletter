import pickle
import numpy as np
from typing import Optional, List, Dict, Tuple
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
            self.data[doc_id] = [chunks]
    
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b)
    
    def retrieve_top_k(self, query_embedding: np.ndarray) -> Optional[List[Tuple[str, 'Chunk']]]:
        similars = []

        for doc_id, document in self.data:
            for chunk_obj in document:
                similarity_score = self.cosine_similarity(query_embedding, chunk_obj.embeddings)
                chunk_obj.set_similarity_score(similarity_score)
                similars.append(doc_id, chunk_obj.id, similarity_score)

        similars.sort(key=lambda x: x[2], reverse=True)

        results = []
        for doc_id, chunk_id, similarity_score in similars[:config.top_k]:
            if similarity_score < 0.6:
                break
            results.append((doc_id, self.data[doc_id][chunk_id]))
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
    

    def save(self) -> None:
        try:
            if self.data:
                save_data = {'data': self.data}
                with open(config.vector_store, 'wb') as f:
                    pickle.dump(save_data, f)
                daily_logger.info(f"Wrote {len(self.data)} documents out to {config.vector_store}")
            else:
                daily_logger.warning(f"Cannot save to {config.vector_store} because VectorStore has no contents.")
        except (OSError, TypeError) as e:
            daily_logger.error(f"Error saving to {config.vector_store}: {e}")

    def load(self) -> None:
        try:
            with open(config.vector_store, 'rb') as f:
                loaded_data = pickle.load(f)
            if isinstance(loaded_data, dict) and 'data' in loaded_data:
                self.data = loaded_data['data']
                runtime_logger.info(f"Loaded {len(self.data)} documents from {config.vector_store}")
        except FileNotFoundError as e:
            runtime_logger.error(f"Error reading VectorStore from {config.vector_store}: {e}")


class Chunk:
    """
    For this use case, a Chunk object could be more accurately named an Article object since I developed the chunking algorithm such that newsletter data was chunked by articles to retain all relevant information and get a better holistic view for the LLM but I left it named Chunk for the sake of RAG terminology.
    """
    def __init__(self, id: str, newsletter: str, title: Optional[str], text: Optional[str], embeddings: Optional[List[int]]):
        self.id=id
        self.newsletter=newsletter,
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

# initialize Singleton for later use
vector_store = VectorStore.get_instance()
