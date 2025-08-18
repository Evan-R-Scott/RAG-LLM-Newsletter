import os
import asyncio
import time
from settings import Config, Logger
from document_fetch.newsletter_data_fetch import parse_feeds

READY_FILE = '/app/data_store/vector_store_ready'
config = Config.get_instance()
logger = Logger.get_daily_logger("data_fetch")

def run() -> None:
    """
    Entrypoint to retrieval for the pipeline
    """
    try:
        logger.info("Starting data fetch process")
        vector_store = asyncio.run(parse_feeds())
        
        os.makedirs('/app/data_store', exist_ok=True)
        vector_store.save()
        
        # Creates readiness flag which signals to 'web' service/container to startup
        with open(READY_FILE, 'w') as f:
            f.write('ready')
        logger.info(f"Readiness flag created at {READY_FILE}")
    except Exception as e:
        logger.info(f"Data fetch process failed: {str(e)}")
        raise
    
if __name__ == "__main__":
    run()
