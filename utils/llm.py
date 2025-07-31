from settings import Config, Logger

config = Config.get_instance()
logger = Logger.get_runtime_logger("chatbot")

def generate_llm_response(text_related:str):
    return text_related