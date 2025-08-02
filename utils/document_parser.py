import os
import json
import uuid
from utils.embedding_handler import prepare_embeddings
from utils.data_io import read_json
from settings import Config, Logger, VectorStore, Chunk

config = Config.get_instance()
daily_logger = Logger.get_daily_logger("data_fetch")
vector_store = VectorStore.get_instance()
vector_store.reset()

def chunk_files(
        directory_path:str,
        ) -> VectorStore: #Dict[str, Dict[str, Dict[str, Any]]]:
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
    #TODO do i need the except here? or no since using read_json?
    if not os.path.exists(directory_path):
        daily_logger.critical(f"Directory not found: {directory_path}")
        raise FileNotFoundError

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        if not os.path.isfile(file_path):
            daily_logger.warning(f"{file_path} is not a valid file")
            continue

        try:
            _, ext = os.path.splitext(filename) 
            doc_id = str(uuid.uuid4())

            if ext.lower() == ".json":
                articles = read_json(file_path)
                chunks = create_chunks_from_json_file(articles)

                if chunks:
                    vector_store.add_chunks(doc_id, chunks)
                    daily_logger.info(f"Added {len(chunks)} chunks to doc_id: {doc_id} in the VectorStore")
                else:
                    daily_logger.warning(f"No valid chunks created from {filename}")
            else:
                daily_logger.warning(f"{filename} is a {ext} extension which is an unsupported document type currently.")
                continue
            
        except (UnicodeDecodeError, IOError) as e:
            daily_logger.warning(f"Could not read {filename}: {e}")
            continue
    return vector_store


def create_chunks_from_json_file(articles):
    chunks = []
    chunk_counter = 1
    for newsletter_name, articles in articles.items():
        for idx, article in enumerate(articles):
            # if article.get('extraction_method') == 'failed':
            #     daily_logger.warning(f"Skipping failed article: {article.get('title', 'Unknown')}")
            #     continue
            
            content = article.get('content', "").strip()
            title = article.get('title', "Unknown Title")

            if not content:
                daily_logger.warning(f"Skipping article with no content: {title}")
                continue
            combined_text = create_combined_text(article)
            chunk_id = f"chunk_{chunk_counter:03d}"

            try:
                embeddings = prepare_embeddings(combined_text)
                chunks.append(Chunk(
                    id=chunk_id,
                    newsletter=newsletter_name,
                    url=article.get('url', ""),
                    title=title,
                    text=combined_text,
                    embeddings = embeddings
                ))
                chunk_counter += 1
            except Exception as e:
                daily_logger.error(f"Failed to create embeddings for article: {title}: {str(e)}")
                continue
    return chunks

def create_combined_text(article):
    title = article.get('title', "")
    url = article.get('url', "")
    content = article.get('content', "")

    combined = []

    if title:
        combined.append(f"Title: {title}")
    if url:
        combined.append(f"Source: {url}")
    if content:
        combined.append(f"Content: {content}")
    return "\n\n".join(combined)
    