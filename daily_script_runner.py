from settings.app_config import config
from utils.document_parser import chunk_files
from utils.embedding_handler import map_embeddings
from utils.data_io import save_json
from document_fetch.newsletter_data_fetch import parse_feeds

def run():
    parse_feeds()
    documents_data = chunk_files(config.document_directory)
    save_json(config.document_store, documents_data)
    mapped_document_db = map_embeddings(documents_data)
    save_json(config.embedding_store, mapped_document_db)
    
if __name__ == "__main__":
    run()
