import json
from dataclasses import dataclass
from typing import List
from transformers import AutoTokenizer, AutoModel

@dataclass
class Config:
    document_directory: str
    tokenizer: str
    embedding_model: str
    top_k: int
    chunk_size: int
    supported_extensions: List[str]
    para_separator: str
    separator: str

    @classmethod
    def from_json(cls, config_path: str = 'config.json'):
        with open(config_path, 'r') as f:
            data = json.load(f)
        return cls(**data)

config = Config.from_json()

config.tokenizer = AutoTokenizer.from_pretrained(config.tokenizer)
config.embedding_model = AutoModel.from_pretrained(config.embedding_model)
config.embedding_model.eval()


# add logger