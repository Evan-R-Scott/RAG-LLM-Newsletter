from settings import Config, Logger
from utils.document_parser import chunk_files
from document_fetch.newsletter_data_fetch import parse_feeds

config = Config.get_instance()
logger = Logger.get_daily_logger("data_fetch")

def run():
    # saving these is actually unnecessary extra storage but done for debugging/expansion purposes 
    parse_feeds()
    chunk_files(config.document_directory)
    # save_json(config.document_store, documents_data)
    # documents_embeddings = map_embeddings(documents_data)
    # save_json(config.embedding_store, documents_embeddings)

    # TODO: store these as fields of some class here and inside some data structure so can import and use at runtime for chatbot? instead of having to read each out every time a query is processed
    
if __name__ == "__main__":
    run()
