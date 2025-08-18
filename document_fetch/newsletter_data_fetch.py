import feedparser
import asyncio
import aiohttp
import uuid
import torch
import time
from bs4 import BeautifulSoup
from readability import Document
from typing import List, Dict, Any, Optional, Set
from settings import Config, Logger, Chunk, VectorStore
from utils.data_io import read_json
from utils.embedding_handler import prepare_embeddings, prepare_embeddings_gpu


config = Config.get_instance()
daily_logger = Logger.get_daily_logger("data_fetch")
vector_store = VectorStore.get_instance()
articles_skipped = {"too_long": 0, "duplicates": 0}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
has_gpu = torch.cuda.is_available()
daily_logger.info(f"Using device: {device}")

async def parse_feeds() -> VectorStore:
    """
    Reads in relevant content from the newsletters/RSS feeds and stores into data structure for further preprocessing

    Returns:
        Dictionary storing relavant article content indexed by newsletter
    """
    vector_store.reset()
    rss_sources = read_json(config.rss_feeds_store)["urls"]

    # template header to avoid request blocks
    headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
    titles_seen = set()
    
    extracting_start = time.perf_counter()
    conn = aiohttp.TCPConnector(limit_per_host=10)
    async with aiohttp.ClientSession(headers=headers, connector=conn) as session:
        tasks = [extract_newsletter_content(session, newsletter_name, newsletter_url, titles_seen) for newsletter_name, newsletter_url in rss_sources.items()]
        
        articles_by_newsletter = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles = {}
    articles_processed = 0
    newsletter_names = list(rss_sources.keys()) 
    for i, articles in enumerate(articles_by_newsletter):
        newsletter_name = newsletter_names[i]

        if isinstance(articles, Exception):
            daily_logger.error(f"Error extracting {newsletter_name}: {articles}")
        elif articles:
            all_articles[newsletter_name] = articles
            articles_processed += len(articles)
        else:
            daily_logger.warning(f"No articles extracted for {newsletter_name}")

    extract_end = time.perf_counter() - extracting_start
    daily_logger.info(f"Extraction of newsletter content complete: {articles_processed} articles extracted in {extract_end:.2f}s")

    chunking_start = time.perf_counter()
    if has_gpu:
        daily_logger.info("Using GPU-accelerated processing")
        chunks_processed = await chunk_articles_gpu(all_articles)
    else:
        daily_logger.info("Processing embeddings sequentially [Cuda not found]")
        chunks_processed = await chunk_articles_sequential(all_articles)
    
    chunk_end = time.perf_counter() - chunking_start
    daily_logger.info(f"Chunking/Embedding complete: {chunks_processed} chunks created in {chunk_end:.2f}s")
    daily_logger.info(f"Total processing time: {extract_end + chunk_end:.2f}s. Skipped {articles_skipped['too_long']} articles (too long) and {articles_skipped['duplicates']} duplicates")

    return vector_store

async def extract_newsletter_content(
        session: aiohttp.ClientSession,
        newsletter_name: str,
        newsletter_url: str,
        titles_seen: Set[str]
    ) -> List[Dict[str, Any]]:

    try:
        loop = asyncio.get_running_loop()
        feed = await asyncio.wait_for(
            loop.run_in_executor(None, feedparser.parse, newsletter_url),
            timeout=30
        )

        if not validate_parse(feed, newsletter_url):
            return []
        
        semaphore = set_semaphore(len(feed.entries), newsletter_url)

        tasks = [extract_article_content(semaphore, entry, session, newsletter_name, titles_seen) for entry in feed.entries if hasattr(entry, "link")]
     
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        fails = 0
        for result in results:
            if isinstance(result, Exception):
                fails += 1
                daily_logger.debug(f"Failed to process entry: {result}")
            elif result:
                articles.append(result)
        if fails > 0:
            daily_logger.warning(f"Failed to process {fails} entries from {newsletter_name}")
            
        return articles

    except Exception as e:
        daily_logger.error(f"Failed to parse RSS feed {newsletter_name}: {str(e)}")
        return []

def validate_parse(feed: feedparser.FeedParserDict, url: str) -> bool:
    if hasattr(feed, "status") and feed.status != 200:
        daily_logger.error(f"RSS feed returned status {feed.status} for {url}")
        return False

    if not hasattr(feed, "entries") or len(feed.entries) == 0:
        daily_logger.warning(f"No entries found for RSS feed: {url}")
        return False
    return True

def set_semaphore(num_entries: int, url: str) -> asyncio.Semaphore:
    if 'arxiv.org' in url:
        # arXiv provides abstracts in RSS feeds so faster to process
        concurrent_tasks = min(100, num_entries)
    else:
        concurrent_tasks = min(20, num_entries)
    return asyncio.Semaphore(concurrent_tasks)

async def extract_article_content(
        semaphore: asyncio.Semaphore,
        entry: Any,
        session: aiohttp.ClientSession,
        newsletter_name: str,
        titles_seen: Set[str]
    ) -> Optional[Dict[str, Any]]:
    async with semaphore:
        try:
            article_url = entry.link
            title = getattr(entry, 'title', 'No Title')

            clean_title = ' '.join(title.lower().split())
            if clean_title in titles_seen:
                articles_skipped["duplicates"] += 1
                return None
            titles_seen.add(clean_title)

            if 'arxiv.org' in article_url:
                content = extract_arxiv_paper(entry)
            else:
                content = await extract_content_norm(session, article_url)

            if not content:
                titles_seen.discard(clean_title)
                return None
            
            if len(content) > config.max_content_length:
                articles_skipped["too_long"] += 1
                titles_seen.discard(clean_title)
                return None
            
            return {
                'title': title,
                'url': article_url,
                'content': content,
                'newsletter': newsletter_name
            }
            
        except Exception as e:
            daily_logger.warning(f"Failed to extract {getattr(entry, 'link', 'unknown')}: {str(e)}")
            if 'clean_title' in locals():
                titles_seen.discard(clean_title)
            return None

async def extract_content_norm(session: aiohttp.ClientSession, article_url: str
                               ) -> Optional[str]:
    try:
        async with session.get(article_url, timeout=45) as resp:
            if resp.status != 200:
                daily_logger.warning(f"Failed to fetch {article_url}, status={resp.status}")
                return None
            html = await resp.text()
    except asyncio.TimeoutError:
        daily_logger.warning(f"Timeout fetching article: {article_url}")
        return None

    try:
        # extract main readable content
        doc = Document(html)
        summary_html = doc.summary()
        soup = BeautifulSoup(summary_html, "html.parser")
        content_text = " ".join([p.get_text() for p in soup.find_all("p")]).strip()

        if len(content_text) < 50:
            daily_logger.info(f"Article too short: {article_url}")
            return None

        return content_text
    except Exception as e:
        daily_logger.warning(f"Failed to parse {article_url}: {str(e)}")
        return None

def extract_arxiv_paper(entry: Any) -> Optional[str]:
    """
    Handler for ArXiv newsletter articles since their RSS feeds are formatted differently with abstract summaries rather than full article pulls. Builds data for an ArXiv article [entry] based on the scraped content.

    Args:
        entry: individual article object from the newsletter RSS feed

    Returns:
        Dictionary storing fields about the article for future processing
    """
    abstract = getattr(entry, 'summary', '')

    if not abstract:
        return None

    abstract = ' '.join(abstract.split())

    for pattern in ["new Abstract:", "replace Abstract:", "replace-cross Abstract:", "cross Abstract:"]:
        split_point = abstract.find(pattern)
        if split_point != -1:
            abstract = abstract[split_point + len(pattern):].strip()
            break
    
    if len(abstract.strip()) < 50:
        return None
    
    return abstract

def create_chunk(article: Dict[str, Any], newsletter_name: str) -> Optional[Chunk]:
    """ Builds out Chunk object for sequential processing path """
    try:
        title = article["title"]
        url = article["url"]
        content = article["content"]    

        combined_text = f"Title: {title}\n\nSource: {url}\n\nContent: {content}"

        embedding = prepare_embeddings(combined_text)
        chunk = Chunk(
            id=str(uuid.uuid4()),
            newsletter=newsletter_name,
            url=url,
            title=title,
            text=combined_text,
            embeddings=embedding)

        return chunk
    except Exception as e:
        daily_logger.warning(f"Failed to create chunk for {article.get('url', 'unknown')}: {str(e)}")
        return None
    
async def chunk_articles_gpu(all_articles: Dict[str, List[Dict[str, Any]]]) -> int:
    """ GPU/CUDA available so does batch processing """
    articles_combined = []
    for newsletter_name, articles in all_articles.items():
        for article in articles:
            articles_combined.append((article, newsletter_name))

    if not articles_combined:
        return 0

    texts = []
    all_metadata = []

    for article, newsletter_name in articles_combined:
        try:
            title = article["title"]
            url = article["url"]
            content = article["content"]    
            combined_text = f"Title: {title}\n\nSource: {url}\n\nContent: {content}"
            
            texts.append(combined_text)
            all_metadata.append({
                "newsletter": newsletter_name,
                "url": url,
                "title": title,
                "text": combined_text
            })
        except Exception as e:
            daily_logger.warning(f"Failed to prepare article: {str(e)}")
            continue

    if not texts:
        return 0
    
    daily_logger.info(f"Starting GPU embedding for {len(texts)} articles")

    try:
        embeddings_batch = await asyncio.to_thread(prepare_embeddings_gpu, texts)

        chunks_by_newsletter = {}
        chunks_processed = 0

        for embedding, metadata in zip(embeddings_batch, all_metadata):
            try:
                newsletter_name=metadata["newsletter"]
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    newsletter=newsletter_name,
                    url=metadata["url"],
                    title=metadata["title"],
                    text=metadata["text"],
                    embeddings=embedding
                )

                if newsletter_name not in chunks_by_newsletter:
                    chunks_by_newsletter[newsletter_name] = []
                chunks_by_newsletter[newsletter_name].append(chunk)
                chunks_processed += 1
            except Exception as e:
                daily_logger.warning(f"Failed to create chunk: {str(e)}")
        
        for newsletter_name, chunks in chunks_by_newsletter.items():
            vector_store.add_chunks(newsletter_name, chunks)
        return chunks_processed
    except Exception as e:
        daily_logger.error(f"Multiprocessing chunking failed: {str(e)}")
        return 0

async def chunk_articles_sequential(all_articles: Dict[str, List[Dict[str, Any]]]) -> int:
    """
    Sequential processing - (CPU fallback bc GPU/CUDA wasn't found)
    """
    try:
        chunks_processed = 0
        chunk_tasks = []

        for newsletter_name, articles in all_articles.items():
            for article in articles:
                task = asyncio.create_task(asyncio.to_thread(create_chunk, article, newsletter_name))
                chunk_tasks.append(task)
        chunks = await asyncio.gather(*chunk_tasks, return_exceptions=True)

        chunks_by_newsletter = {}

        for chunk in chunks:
            if isinstance(chunk, Exception):
                daily_logger.debug(f"Failed to create chunk: {chunk}")
            elif chunk:
                newsletter_name = chunk.newsletter
                if newsletter_name not in chunks_by_newsletter:
                    chunks_by_newsletter[newsletter_name] = []
                chunks_by_newsletter[newsletter_name].append(chunk)
                chunks_processed += 1

        for newsletter_name, chunks in chunks_by_newsletter.items():
            vector_store.add_chunks(newsletter_name, chunks)
            daily_logger.info(f"Stored {len(chunks)} articles from {newsletter_name} to vector store")

        return chunks_processed
    except Exception as e:
        daily_logger.error(f"Failed to embed/build chunks sequentially: {str(e)}")
        return chunks_processed
