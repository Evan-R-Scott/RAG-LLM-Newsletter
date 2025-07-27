from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from settings.app_config import config
from utils.document_parser import chunk_files
from utils.embedding_handler import map_embeddings
from utils.answer_retrieval import retrieve_top_k_scores
from utils.data_io import retrieve_text
from utils.llm import generate_llm_response

app = FastAPI(title="Evan's Chatbot")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def chatbot(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

class Message(BaseModel):
    message: str

@app.post("/chat", response_class=JSONResponse)
def chat_endpoint(query: Message):
    message = query.message
    documents_data = chunk_files(config.document_directory)
    documents_embeddings = map_embeddings(documents_data)
    top_k_similars = retrieve_top_k_scores(message, documents_embeddings)
    text_related, json_related = retrieve_text(top_k_similars, documents_data)

    llm_summary = generate_llm_response(text_related)

    return {
        "summary": llm_summary,
        "related_text": json_related
    }
