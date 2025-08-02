import os
from settings import Config, Logger, VectorStore
from utils.document_parser import chunk_files
from document_fetch.newsletter_data_fetch import parse_feeds

config = Config.get_instance()
logger = Logger.get_daily_logger("data_fetch")

def run():
    parse_feeds()
    vector_store = chunk_files(config.document_directory)
    # write out to a .pkl file for later use at runtime by chatbot
    os.makedirs('data_store', exist_ok=True)
    vector_store.save()
    
if __name__ == "__main__":
    run()
