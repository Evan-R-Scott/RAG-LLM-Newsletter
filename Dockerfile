#FROM python:3.12-slim
FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m pip install --upgrade pip

# cache transformer model im using for embeddings so they persist between container starts
ENV HF_HOME=/app/.cache/huggingface

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# pre-download the models
RUN python -c "\
from transformers import AutoTokenizer, AutoModel; \
AutoTokenizer.from_pretrained('BAAI/bge-small-en-v1.5'); \
AutoModel.from_pretrained('BAAI/bge-small-en-v1.5'); \
"

COPY . .

EXPOSE 8000