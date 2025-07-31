import json
from typing import Any, Dict, List, Tuple
from settings import Config, Logger, Chunk

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


def format(
        chunk_objs:List[Tuple[str, 'Chunk']]
        ) -> Tuple[List[str], Dict[str, List[Dict[str, Dict[str, Any]]]]]:
    articles_text = []
    json_formatted = {}
    for doc_id, chunk in chunk_objs:
        if chunk.text and chunk.text.strip():
            articles_text.append(chunk.text)
            if doc_id in json_formatted:
                json_formatted[doc_id].append({
                    chunk.id: {
                        "newsletter_from": chunk.newsletter,
                        "article_title": chunk.title,
                        "similarity_score": chunk.similarity_score
                    }
                })
            else:
                json_formatted[doc_id] = [{
                    chunk.id: {
                        "newsletter_from": chunk.newsletter,
                        "article_title": chunk.title,
                        "similarity_score": chunk.similarity_score
                    }
                }]
    runtime_logger.info(f"Formatted {len(chunk_objs)} article chunks for serving to llm and user")
    return articles_text, json_formatted

# def retrieve_text(
#         top_results: List[Tuple[str, str, float]],
#         document_data: Dict[str, Dict[str, Dict[str, Any]]]
#         )-> List[str]:
#     content = []
#     json_format = {}
#     for match in top_results:
#         doc_id, chunk_id, score = match
#         try:
#             related_text = document_data[doc_id][chunk_id]["text"]
#             if related_text and related_text.strip():
#                 content.append(related_text)
#                 if doc_id in json_format:
#                     json_format[doc_id].append({
#                         chunk_id: {
#                             "cosine similarity score": score,
#                             "article": related_text
#                         }})
#                 else:
#                     json_format[doc_id] = [{
#                         chunk_id: {
#                             "cosine similarity score": score,
#                             "article": related_text
#                         }
#                     }]
#         except (KeyError) as e:
#             print(f"Could not find text for {doc_id}/{chunk_id}: {e}")
#             continue

#     return "".join(content), json_format