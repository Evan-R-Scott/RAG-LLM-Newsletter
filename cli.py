from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from settings import Config, Logger, VectorStore
from utils.llm import generate_llm_response
from utils.embedding_handler import prepare_embeddings

app = FastAPI(title="Evan's Chatbot")
config = Config.get_instance()
runtime_logger = Logger.get_runtime_logger("chatbot")
vector_store = VectorStore.get_instance()
vector_store.load()

class Message(BaseModel):
    message: str

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def chatbot(request: Request):
    runtime_logger.info("Routing user to chat.html")
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat", response_class=JSONResponse)
def chat_endpoint(query: Message):
    message = query.message
    runtime_logger.info(f"Query submitted at /chat endpoint: {message}")
    query_embedding = prepare_embeddings(message)

    related_chunk_objs = vector_store.retrieve_top_k(query_embedding=query_embedding)

    if len(related_chunk_objs) == 0:
        runtime_logger.info(f"There was no article with content related to the user's query: {query}")
        text_related = "No newsletter data was found related to your query."
        json_formatted = ["No newsletter data was found related to your query."]
    else:
        runtime_logger.info(f"Found {len(text_related)} articles of relative similarity to user's query: {query}")
        text_related, json_formatted = format(related_chunk_objs)
        text_related = generate_llm_response(text_related)

    return {
        "summary": text_related,
        "related_text": json_formatted
    }
