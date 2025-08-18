"""   OLD CODE FROM USING OPENAPI FOR SUMMARIZATIONS   """

from openai import OpenAI
from typing import Optional
from settings import Config, Logger

config = Config.get_instance()
runtime_logger = Logger.get_runtime_logger("chatbot")
client = OpenAI(api_key=config.llm["API_KEY"]) # Old version -> Update config.json

def generate_llm_response(query, text_related: list) -> Optional[str]:
    """
    LM generation handler

    Args:
        query: user-typed query into chatbot
        text-related: top articles found related to user's query
    
    Returns:
        LM generated response based on context
    """

    ### OLD CODE FROM USING OPENAPI FOR SUMMARIZATIONS ###

    if text_related:
        articles = [
            f"[Article Title:]{article['Title']}\n[Newsletter where article is from:]{article['Newsletter_From']}\n[Article Content:]{article['Content']}"
            for article in text_related
        ]
        prompt = update_prompt(query, articles)
        content = "You are an expert newsletter analyst and summarizer. Your job is to analyze relevant newsletter articles and provide a comprehensive, actionable summary based on user queries."
    else:
        prompt = f"Answer the following to the best of your ability using recent, relevant data. Provide key insights, important takeaways, and any actionable information. The user's query is: {query}"
        content = "You are an intelligent assistant with access to up-to-date information and a deep understanding of current events and topics. Your job is to provide clear, informative, and helpful answers to user questions, even in the absence of specific newsletter articles."
    
    try:
        # call to OpenAPI
        response = client.chat.completions.create(
            model=config.llm["MODEL"],  # Old version -> Update config.json
            messages=[
                {
                    "role": "system",
                    "content": content
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
        )
        runtime_logger.info("LLM response generated successfully")
        return response.choices[0].message.content
    except Exception as e:
        runtime_logger.error(f"Error generating LLM response: {str(e)}")
        return None

def update_prompt(query, articles):
    """
    Default prompt for LM
    """
    articles_text = "\n\n".join(articles)

    prompt = f"""Based on these newsletter articles, answer the user's question: "{query}"

RELEVANT ARTICLES:
{articles_text}

Please provide a helpful summary that addresses their question. Include:
- Key insights relevant to their query
- Important takeaways from these articles they should know
- Any actionable information

Use proper markdown formatting with ## for headings, **bold** for emphasis, and bullet points for lists."""
    return prompt
