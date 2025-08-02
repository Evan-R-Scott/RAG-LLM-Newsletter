from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from settings import Config, Logger, VectorStore
from utils.llm import generate_llm_response
from utils.embedding_handler import prepare_embeddings
from utils.data_io import format_chunks

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

    # chunk objecs of highest similarity to query (up to top_k articles)
    related_articles = vector_store.retrieve_top_k(query_embedding=query_embedding)

    if len(related_articles) == 0:
        runtime_logger.info(f"There were no articles with content relevant to the user's query: {query}")
        articles_list = "No newsletter data was found related to your query."
        json_formatted = ["No newsletter data was found related to your query."]
    else:
        runtime_logger.info(f"Found {len(related_articles)} articles of relative similarity to user's query: {query}")
        articles_list, json_formatted = format_chunks(related_articles)
        articles_list = generate_llm_response(message, articles_list)
    return {
        "summary": articles_list,
        "related_text": json_formatted
    }
