import json
from typing import Optional
from transformers import AutoTokenizer, AutoModel

""" cls refers to the class itself bc of decorator whereas self refers to the instance"""
class Config:
    """Singleton storing hyperparameters used in preprocessing and at runtime for a centralized settings store"""
    _instance: Optional['Config'] = None
    _initialized: bool = False

    def __init__(self):
        if not Config._initialized:
            with open('settings/config.json', 'r') as f:
                data = json.load(f)
            
            for key, value in data.items():
                setattr(self, key, value)

            self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer)
            self.embedding_model = AutoModel.from_pretrained(self.embedding_model)
            self.embedding_model.eval()
            Config._initialized = True

    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
