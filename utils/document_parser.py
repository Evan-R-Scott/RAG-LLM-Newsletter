from typing import Dict, List, Any
from utils.embedding_handler import prepare_embeddings
from settings import Config, Logger, VectorStore, Chunk

config = Config.get_instance()
daily_logger = Logger.get_daily_logger("data_fetch")
vector_store = VectorStore.get_instance()
vector_store.reset()


def chunk_articles(articles:  Dict[str, List[Dict[str, Any]]]) -> VectorStore:
    """
    Stores article content including embeddings into chunks then into a custom VectorStore for efficient storage and retrieval at runtime with chatbot

    Args:
        articles: Dictionary storing relavant article content indexed by newsletter

    Returns:
        A vectorStore object containing chunks which store article content
    
    Example:

        vector_store.data = {
            "newsletter1_name": [
                chunk -> {
                    "id": "chunk_001",
                    "text": "blahahhahah...",
                    "embedding": [0.1, 0.8, ...],
                    ...
                },
                chunk -> {
                    "id": "chunk_002",
                    "text": "article 2 blah blah...",
                    "embedding": [-0.4, 0.6, ...],
                    ...
                }
            ],
            "newsletter2_name": [
                chunk -> {
                    "id": "chunk_003",
                    "text": "another article boom...",
                    "embedding": [0.7, 0.3, ...],
                    ...
                }
            ]
        }
    """
    chunk_counter = 1

    for newsletter_name, article_list in articles.items():
        chunks = []
        for article in article_list:
            title = article.get('title', "Unknown Title")
            content = article.get('content', "").strip()

            if not content:
                daily_logger.warning(f"Skipping article with no content: {title}")
                continue

            combined_text = create_combined_text(article)
            chunk_id = f"chunk_{chunk_counter:03d}"

            try:
                embedding = prepare_embeddings(combined_text)
                chunk = Chunk(
                    id=chunk_id,
                    newsletter=newsletter_name,
                    url=article.get('url', ""),
                    title=title,
                    text=combined_text,
                    embeddings=embedding
                )
                chunks.append(chunk)
                chunk_counter += 1
            except Exception as e:
                daily_logger.error(f"Failed to create embedding for article '{title}': {str(e)}")
                continue
        daily_logger.info(f"Stored {len(chunks)} articles from {newsletter_name} to vector store")
        vector_store.add_chunks(newsletter_name, chunks)
    return vector_store


def create_combined_text(article: Dict[str, Any]) -> str:
    """
    Combines content from the article store into a format summarizable by LLM at runtime

    Args:
        article: dictionary storing fields about the article
    
    Returns:
        formatted string containing article content
    """
    parts = []
    if article.get('title'):
        parts.append(f"Title: {article['title']}")
    if article.get('url'):
        parts.append(f"Source: {article['url']}")
    if article.get('content'):
        parts.append(f"Content: {article['content']}")
    return "\n\n".join(parts)
