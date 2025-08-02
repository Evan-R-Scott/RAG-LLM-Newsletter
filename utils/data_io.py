import json
from typing import Any, Dict, List, Tuple
from settings import Config, Logger

config = Config.get_instance()
runtime_logger = Logger.get_runtime_logger("chatbot")

def save_json(path: str, data: Any) -> None:
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
    except (OSError, TypeError) as e:
        runtime_logger.error(f"Error saving JSON to {path}: {e}")
        raise

def read_json(path: str) -> Any:
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        runtime_logger.error(f"Error reading JSON from {path}: {e}")
        raise


def format_chunks(
        chunk_objs #:List[Tuple[str, 'Chunk']]
        ): # -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Dict[str, Any]]]]]:
    articles_text = []
    json_formatted = {}
    for chunk in chunk_objs:
        if chunk.text and chunk.text.strip():
            articles_text.append({
                "Title": chunk.title,
                "Newsletter_From": chunk.newsletter,
                "Content": chunk.text
            })
            if chunk.newsletter in json_formatted:
                json_formatted[chunk.newsletter].append({
                    "article_title": chunk.title,
                    "url": chunk.url,
                    "similarity_score": chunk.similarity_score
                })
            else:
                json_formatted[chunk.newsletter] = [{
                    "article_title": chunk.title,
                    "similarity_score": chunk.similarity_score
                }]
    return articles_text, json_formatted
