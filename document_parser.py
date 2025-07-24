import os
import re
import uuid

def chunk_files(directory_path,tokenizer, chunk_size, para_separator="\n\n", separator=" "):
    """
    Breaks down the text stored in document files into chunks for efficient storing and parsing for later LLM/RAG use

    Args:
        directory_path: directory storing the files the LLM will eventually use for RAG
        tokenizer: method chosen for tokenizing the chunks to determine current chunk size
        chunk_size: size each chunk will be, determines the max size that objects stored in the vector db will be
        para_separator: token chosen to split file into paragraphs
        separator: token chosen to split the paragraph into smaller individual tokens

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
    documents, chunks = {}, {}

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        base = os.path.basename(file_path)
        sku = os.path.splitext(base)[0]
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            doc_id = str(uuid.uuid4())

            paragraphs = re.split(para_separator, text)

            for paragraph in paragraphs:
                words = paragraph.split(separator)
                current_chunk_str = ""
                chunk_texts = []
                for word in words:
                    if current_chunk_str:
                        new_chunk = current_chunk_str + separator + word
                    else:
                        new_chunk = current_chunk_str + word
                    if len(tokenizer.tokenize(new_chunk)) <= chunk_size:
                        current_chunk_str = new_chunk
                    else:
                        if current_chunk_str:
                            chunk_texts.append(current_chunk_str)
                        current_chunk_str = word
                
                if current_chunk_str:
                    chunk_texts.append(current_chunk_str)
                
                for chunk_text in chunk_texts:
                    chunk_id = str(uuid.uuid4())
                    chunks[chunk_id] = {
                        "text": chunk_text, 
                        "metadata": {
                            "filename": sku }}
            
        documents[doc_id] = chunks
    return documents