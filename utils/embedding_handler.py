import torch
import numpy as np
from typing import List
from settings import Config, Logger

config = Config.get_instance()
daily_logger = Logger.get_daily_logger("data_fetch")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
has_gpu = torch.cuda.is_available()

def prepare_embeddings(text: str) -> np.ndarray:
    """
    Compute embeddings for a single text.
    """
    inputs = config.tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )

    if has_gpu:
        inputs = {k: v.to(device) for k, v in inputs.items()}
        model = config.embedding_model.to(device)
    else:
        model = config.embedding_model

    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
        embeddings = torch.nn.functional.normalize(embeddings.unsqueeze(0), p=2, dim=1).squeeze()
        embeddings = embeddings.cpu().numpy()

    return embeddings

def prepare_embeddings_gpu(texts: List[str]) -> List[np.ndarray]:
    """
    Compute embeddings for a list of texts via GPU
    """
    if not texts:
        return []

    if has_gpu:
        model = config.embedding_model.to(device)
        tokenizer = config.tokenizer
        all_embeddings = []

        for i in range(0, len(texts), config.batch_size):
            batch_texts = texts[i:i+config.batch_size]

            inputs = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )

            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                all_embeddings.extend(embeddings.cpu().numpy())

        return all_embeddings

    else:
        daily_logger.info("GPU not available, using CPU sequential processing")
        return [prepare_embeddings(text) for text in texts]
