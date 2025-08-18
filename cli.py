from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List
import json

from utils.ollama_client import generate_response_stream
from settings import Config, Logger, VectorStore
from utils.embedding_handler import prepare_embeddings
from utils.data_io import format_chunks

app = FastAPI(title="Evan's Chatbot")
config = Config.get_instance()
runtime_logger = Logger.get_runtime_logger("chatbot")
vector_store = VectorStore.get_instance()
vector_store.load()
runtime_logger.info("Loaded data into vector store")

class Message(BaseModel):
    message: str

class ChatRequest(BaseModel):
    message: str
    articles_list: Optional[List[Dict]] = None

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def chatbot(request: Request):
    runtime_logger.info("Routing user to chat.html")
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/related_articles", response_class=JSONResponse)
def related_articles_endpoint(query: Message):
    message = query.message
    query_embedding = prepare_embeddings(message)
    related_articles = vector_store.retrieve_top_k(query_embedding=query_embedding)
    runtime_logger.info(f"Found {len(related_articles)} articles of relative similarity to user's query: {query}")
    if len(related_articles) == 0:
        articles_list = []
        json_formatted = ["No newsletter data was found related to your query."]
    else:
        articles_list, json_formatted = format_chunks(related_articles)

    return {
        "articles_list": articles_list,  # to feed into LLM
        "related_text": json_formatted    # to display in sidebar
    }

@app.post("/chat")
async def chat_endpoint(body: ChatRequest):
    message = body.message
    articles_list = body.articles_list or []
    runtime_logger.info(f"Beginning stream of: {message}")

    async def event_stream():
        chunk_count = 0
        total_sent = ""
        try:
            async for chunk in generate_response_stream(message, articles_list):
                chunk_count += 1
                total_sent += chunk
                yield chunk
            runtime_logger.info(f"Total chunks sent: {chunk_count}, Total characters: {len(total_sent)}")
        except Exception as e:
            runtime_logger.error(f"Streaming error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/plain",
                             headers={
                                 "Cache-Control": "no-cache",
                                 "Connection": "keep-alive",
                                 })
