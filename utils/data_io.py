import json
from typing import Any, Dict, List, Tuple
from settings import Config, Logger, Chunk

config = Config.get_instance()
runtime_logger = Logger.get_runtime_logger("chatbot")

def read_json(path: str) -> Any:
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        runtime_logger.error(f"Error reading JSON from {path}: {e}")
        raise


def format_chunks(
        chunk_objs: List['Chunk']
        ) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Format content for LLM summarization and JSON ouput to interface

    Args:
        chunk_objs: List of <= top_k chunks/articles similar to user query
    
    Returns:
        (List of articles formatted, JSON-formatted summary content for sidebar)
    """
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
                    "url": chunk.url,
                    "similarity_score": chunk.similarity_score
                }]
    return articles_text, json_formatted
