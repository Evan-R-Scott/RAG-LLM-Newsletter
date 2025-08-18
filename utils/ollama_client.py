import asyncio
import ollama
from typing import Optional, List, Dict, AsyncGenerator
from settings import Config, Logger

config = Config.get_instance()
runtime_logger = Logger.get_runtime_logger("chatbot")

async def generate_response_stream(query: str, text_related: List[Dict] = None) -> AsyncGenerator[str, None]:
    """
    LLM handler which streams content from Ollama's API

    Args:
        query: user-typed query into chatbot
        text-related: top articles found related to user's query
    
    Returns:
        LLM generated response based on context, sent as tokens
    """
    if text_related:
        articles = [
            f"[Article Title:]{a['Title']}\n[Newsletter where article is from:]{a['Newsletter_From']}\n[Article Content:]{a['Content']}"
            for a in text_related
        ]
        prompt = create_prompt_with_articles(query, articles)
    else:
        prompt = f"{query}"

    runtime_logger.info(f"Streaming prompt to {config.llm['Model']} ({len(prompt)} chars)")

    try:
        client = ollama.Client(host=config.llm["Endpoint"])

        for chunk in client.chat(
            model=config.llm["Model"],
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            options={"temperature": 0.3, "timeout": 120}
        ):
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]

    except Exception as e:
        runtime_logger.error(f"Error streaming LLM response: {str(e)}")
        yield f"[Connection Error: Cannot connect to Ollama service. Error: {str(e)}]"

def create_prompt_with_articles(query: str, articles: List[str]) -> str:
    articles_text = "\n\n".join(articles)
    return f"""The user asks: "{query}"

Here are relevant newsletter articles:
{articles_text}

Please analyze accordingly."""
