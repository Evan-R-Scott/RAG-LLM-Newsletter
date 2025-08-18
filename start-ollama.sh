#!/bin/bash

rm -f /ollama/data/model_ready

export OLLAMA_MODELS=/root/.ollama/models

ollama serve &
sleep 5

while ! ollama list >/dev/null 2>&1; do
    echo "Waiting for ollama to start"
    sleep 2
done

if ! ollama list | grep -q "qwen2.5:7b"; then
    echo "Downloading qwen2.5:7b model"
    ollama pull qwen2.5:7b
fi

if ! ollama list | grep -q "local_llm"; then
    echo "Creating local_llm..."
    ollama create local_llm -f /Modelfile
    echo "Custom local llm created successfully"
fi
echo "Ollama server ready"

echo "Warming up local_llm so its loaded into memory for runtime..."
ollama run local_llm "Hello" > /dev/null 2>&1

sleep 5

touch /ollama/data/model_ready

wait