import torch

def map_embeddings(documents, tokenizer, model):
    """
    Converts the texts that were chunked from the documents into vector representations and stores those embeddings for future similarity searches by LLM/RAG

    Args:
        documents: dictionary storing the chunked texts of the various documents, indexed by document_id and chunk_id
        tokenizer: method chosen for tokenizing the chunks to determine current chunk size (convert text to numbers that can be used by model)
        model: pretrained model to output embeddings which capture textual meaning

    Returns:
        A dictionary mapping document_id -> chunk_id -> embedding vectors

    Example:

        documents is passed in (see docstring in parse_documents.py for structure) and something like this is returned:

        mapped_document_db = {
            "oaooi20kdoamd": {
                chunk_01: [0.1, -0.3, 0.7, ...],
                chunk_02: [0.2, 0.1, -0.5, ...]
                },
            "oasiiainia209a": {
                chunk_01: [0.6, 0.2, -0.1, ...],
                chunk_02: [-0.4, -0.9, 0.7, ...]
                }
        }
    """
    mapped_document_db = {}
    for id, document in documents.items():
        mapped_embeddings = {}
        for chunk_id, chunk_content in document.items():
            text = chunk_content.get("text")
            encoded_input = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
            with torch.no_grad():
                embeddings = model(**encoded_input).last_hidden_state.mean(dim=1).squeeze().tolist()
            mapped_embeddings[chunk_id] = embeddings
        mapped_document_db[id] = mapped_embeddings
    return mapped_document_db