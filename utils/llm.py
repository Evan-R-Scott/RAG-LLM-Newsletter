from settings import Config, Logger

config = Config.get_instance()
runtime_logger = Logger.get_runtime_logger("chatbot")

def generate_llm_response(query, text_related:str):
    articles = [f"[Article Tite:]{article['Title']}\n[Newsletter where article is from:]{article['Newsletter_From']}\n[Article Content:]{article['Content']}" 
                for article in text_related]
    prompt = update_prompt(query, articles)
    runtime_logger.critical(prompt)
    return prompt
    # res = []
    # for article in text_related:
    #     title = article["Title"]
    #     newsletter = article["Newsletter_From"]
    #     content = article["Content"]
    #     res.append(f"{title}<br>{newsletter}<br>{content}")
    # return "<br><br>".join(res)

def update_prompt(query, articles):
   
    prompt = f"""You are an expert newsletter analyst and summarizer. Your job is to analyze relevant newsletter articles and provide a comprehensive, actionable summary based on the user's specific query.

USER QUERY: "{query}"

RELEVANT NEWSLETTER ARTICLES:
{articles}

INSTRUCTIONS:
1. **Direct Answer First**: Start with a clear, direct answer to the user's question
2. **Key Insights**: Extract and synthesize the most important insights from across all articles
3. **Source Attribution**: Reference which newsletters/sources support each key point
4. **Actionable Takeaways**: Provide 3-5 specific, actionable insights the user can act on
5. **Contradictions**: Note any conflicting viewpoints between sources
6. **Context**: Explain why this topic matters now and its broader implications

FORMAT YOUR RESPONSE AS:
## Direct Answer
[2-3 sentence direct answer to the query]

## Key Insights
[3-5 bullet points of synthesized insights with source attribution]

## Actionable Takeaways
[3-5 specific actions or recommendations]

## Different Perspectives
[Any conflicting viewpoints or nuances between sources]

## Why This Matters
[Broader context and implications]

IMPORTANT GUIDELINES:
- Focus on insights that directly address the user's query
- Don't just summarize each article separately - synthesize across sources
- Be concise but comprehensive
- Highlight time-sensitive information
- If articles don't fully answer the query, acknowledge limitations
"""
    return prompt