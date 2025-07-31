from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from settings import Config, Logger
from utils.answer_retrieval import retrieve_top_k_scores
from utils.data_io import retrieve_text, read_json, save_json
from utils.llm import generate_llm_response

app = FastAPI(title="Evan's Chatbot")
config = Config.get_instance()
logger = Logger.get_runtime_logger("chatbot")

class Message(BaseModel):
    message: str

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def chatbot(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat", response_class=JSONResponse)
def chat_endpoint(query: Message):
    message = query.message
    documents_data = read_json(config.document_store)
    documents_embeddings = read_json(config.embedding_store)

    top_k_similars = retrieve_top_k_scores(message, documents_embeddings)
    
    if len(top_k_similars) == 0:
        text_related = "No newsletter data was found related to your query."
        json_related = ["No newsletter data was found related to your query."]
    else:
        text_related, json_related = retrieve_text(top_k_similars, documents_data)
        text_related = generate_llm_response(text_related)

    return {
        "summary": text_related,
        "related_text": json_related
    }
