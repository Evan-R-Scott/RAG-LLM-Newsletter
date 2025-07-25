import os
import re
import uuid
from typing import Any, Dict, List
from config import config

def chunk_files(
        directory_path:str,
        ) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Breaks down the text stored in document files into chunks for efficient storing and parsing for later LLM/RAG use

    Args:
        directory_path: directory storing the files the LLM will eventually use for RAG

    Returns:
        A dictionary representing the documents broken down into chunks and stored with a document_id and chunk_id where multiple chunks will share the same document_id but each chunk has a unique chunk_id
    
    
    Example:

        document1.txt: blahahhahah random words...end of doc.
        document2.txt: more random words... end of doc.

        the directory where these are stored is passed and something like this is returned:

        documents = {
            "oaooi20kdoamd": {
                chunk_01: {
                    "text": "blahahhahah random words",
                    "metadata": {
                        "filename": "document1
                    }
                },
                chunk_02: {
                    "text": "end of doc.",
                    "metadata": {
                        "filename": "document1
                    }
                }
            },
            "oasiiainia209a": {
                chunk_01: {
                    "text": "more random words",
                    "metadata": {
                        "filename": "document2
                    }
                },
                chunk_02: {
                    "text": "end of doc.",
                    "metadata": {
                        "filename": "document2
                    }
                }
            }
        }


    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    if config.chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    
    documents = {}

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        if not os.path.isfile(file_path):
            continue

        _, ext = os.path.splitext(filename)
        if ext.lower() not in config.supported_extensions:
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text= file.read().strip()
        except (UnicodeDecodeError, IOError) as e:
            # add logging
            print(f"Could not read {filename}: {e}")
            continue
            
        if not text: # skip empty files
            continue

        sku = os.path.splitext(filename)[0]     
        doc_id = str(uuid.uuid4())

        chunks = create_chunks_from_file(text, sku)
        if chunks:
            documents[doc_id] = chunks
    return documents

def create_chunks_from_file(text: str, sku: str) -> Dict[str, Dict[str, Any]]:
    chunks = {}
    paragraphs = re.split(config.para_separator, text)
    chunk_counter = 1

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
        paragraph_chunks = chunk_paragraph(paragraph)

        for chunk_text in paragraph_chunks:
            #chunk_id = str(uuid.uuid4())
            chunk_id = f"chunk_{chunk_counter:03d}"
            chunks[chunk_id] = {
                "text": chunk_text.strip(), 
                "metadata": {
                    "filename": sku 
                    }
            }
            chunk_counter += 1
                    
    return chunks
    
def chunk_paragraph(paragraph: str) -> List[str]:
    words = paragraph.split(config.separator)
    current_chunk_words = []
    chunks = []   

    for word in words:
        if current_chunk_words:
            test_chunk = config.separator.join(current_chunk_words) + config.separator + word
        else:
            test_chunk = word
        test_tokens = config.tokenizer.tokenize(test_chunk)

        if len(test_tokens) <= config.chunk_size:
            current_chunk_words.append(word)
        else:
            if current_chunk_words:
                chunks.append(config.separator.join(current_chunk_words))
            current_chunk_words = [word]
    
    if current_chunk_words:
        chunks.append(config.separator.join(current_chunk_words))
    
    return chunks