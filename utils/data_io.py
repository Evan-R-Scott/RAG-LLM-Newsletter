import json
from typing import Any, Dict, List, Tuple

def save_json(path: str, data: Any) -> None:
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
    except (IOError, TypeError) as e:
        print(f"Error saving JSON to {path}: {e}")
        raise

def read_json(path: str) -> Any:
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON from {path}: {e}")
        raise


def retrieve_text(
        top_results: List[Tuple[str, str, float]],
        document_data: Dict[str, Dict[str, Dict[str, Any]]]
        )-> List[str]:
    content = []
    for match in top_results:
        doc_id, chunk_id, _ = match
        try:
            related_text = document_data[doc_id][chunk_id]["text"]
            content.append(related_text)
        except (KeyError) as e:
            print(f"Could not find text for {doc_id}/{chunk_id}: {e}")
            continue
    return content