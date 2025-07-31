from typing import Optional, List

class VectorStore:
    """Singleton"""
    _instance: Optional['VectorStore'] = None
    _initialized: bool = False

    def __init__(self): # self.data = Dict[str, List['Chunk']]
        if not VectorStore._initialized:
            self.data = {}
            VectorStore._initialized = True
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def add_chunks(self, doc_id: str, chunks: List['Chunk']):
        self.data[doc_id] = [chunks]
    
    def retrieve_top_k_text(self, top_k: int = 5):
        pass

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        cls._instance = None
        cls._initialized = False


class Chunk:
    def __init__(self, id: str, text: Optional[str], embeddings: Optional[List[int]]):
        self.id = id
        self.text = text
        self.embeddings = embeddings
        self.similarity_score: Optional[float] = None

    def set_text(self, text: str):
        self.text = text
    
    def set_embedding(self, embeddings: List[int]):
        self.embeddings = embeddings

    def set_similarity_score(self, score):
        self.similarity_score = score

# initialize Singleton for later use
vector_store = VectorStore.get_instance()
