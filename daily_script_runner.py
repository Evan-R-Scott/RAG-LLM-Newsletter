import os
from settings import Config, Logger
from utils.document_parser import chunk_articles
from document_fetch.newsletter_data_fetch import parse_feeds

READY_FILE = '/app/data_store/vector_store_ready'
config = Config.get_instance()
logger = Logger.get_daily_logger("data_fetch")

def run() -> None:
    """
    Entrypoint to retrieval for the pipeline
    """
    logger.info("Starting data fetch process")
    all_articles = parse_feeds()
    logger.info(f"Parsed {len(all_articles) if all_articles else 0} newsletters total")
    
    logger.info("Creating vector store")
    vector_store = chunk_articles(all_articles)
    
    os.makedirs('/app/data_store', exist_ok=True)
    
    vector_store.save()
    logger.info("Saved vector store")
    
    # Creates readiness flag which signals to 'web' service/container to startup
    with open(READY_FILE, 'w') as f:
        f.write('ready')
    logger.info(f"Readiness flag created at {READY_FILE}")
    
if __name__ == "__main__":
    run()
