import feedparser
import time
from newspaper import Article, ArticleException
from typing import List, Dict, Any
import requests
from settings import Config, Logger
from utils.data_io import read_json


config = Config.get_instance()
daily_logger = Logger.get_daily_logger("data_fetch")

def parse_feeds() -> Dict[str, List[Dict[str, Any]]]:
    """
    Reads in relavant content from the newsletters/RSS feeds and stores into data structure for further preprocessing

    Returns:
        Dictionary storing relavant article content indexed by newsletter
    """
    rss_sources = read_json(config.rss_feeds_store)["urls"]
    all_articles = {}

    for newsletter_name, newsletter_url in rss_sources.items():
        try:
            articles = parse_rss_feed(newsletter_url)
            if articles:
                all_articles[newsletter_name] = articles
            else:
                daily_logger.warning(f"No articles parsed for {newsletter_name}")
            time.sleep(3)
        except Exception as e:
            daily_logger.error(f"Error parsing {newsletter_url}: {e}")
    return all_articles

def parse_rss_feed(url: str) -> List[Dict[str, Any]]:
    """
    Extracts article urls from the newsletter RSS feeds and passes
    downstream for further extraction

    Args:
        url: url of the newsletter RSS feed which stores the urls of the posted articles
    
    Returns:
        List of the articles' content built out from that newsletter

    """
    articles = []
    
    try:
        feed = feedparser.parse(url)

        if hasattr(feed, "status"):
            if feed.status != 200:
                daily_logger.error(f"RSS feed returned status {feed.status} for {url}")
                return articles
        if not hasattr(feed, "entries") or len(feed.entries) == 0:
            daily_logger.warning(f"No entries found for RSS feed: {url}")
            return articles
        
        missing_links = 0
        for entry in feed.entries:
            if not hasattr(entry, "link"):
                missing_links += 1
                continue
            
            article_content = extract_article_data(entry)
            if article_content:
                articles.append(article_content)
        if missing_links > 0:
            daily_logger.warning(f"{missing_links} entries are missing links for {url}")
            
    except Exception as e:
        daily_logger.error(f"Failed to parse RSS feed {url}: {str(e)}")
        return articles

    daily_logger.info(f"Extracted {len(articles)} articles from {url}")
    return articles


def extract_article_data(entry: Any) -> Dict[str, Any]:
    """
    Builds data for an article [entry] based on the scraped content from the pulled url

    Args:
        entry: individual article object from the newsletter RSS feed with fields like url

    Returns:
        Dictionary storing fields about the article for future processing
    """
    article_url = entry.link

    article_data = {
        'title': getattr(entry, 'title', 'No Title'),
        'url': article_url,
        'content': ''
    }

    if 'arxiv.org' in article_url:
        return extract_arxiv_paper(entry, article_data)

    try:
        article = Article(article_url)
        article.download()
        article.parse()

        if len(article.text.strip()) < 50: # article too short -> likely failed
            daily_logger.info("Article text < 100 characters")
            return None
        
        article_data.update({
            'content': article.text.strip(),
            'title': article.title if article.title else article_data['title']
        })
        
        daily_logger.debug(f"Extracted article of length {len(article.text)} characters")
        return article_data

    except (requests.exceptions.RequestException, ArticleException) as e:
        daily_logger.warning(f"Failed to download/parse article: {article_url}: {str(e)}")
    except Exception as e:
        daily_logger.warning(f"Failed to extract article data from {article_url}: {str(e)}")
    return None

def extract_arxiv_paper(entry: Any, article_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for ArXiv newsletter articles since their RSS feeds are formatted differently with abstract summaries rather than full article pulls. Builds data for an ArXiv article [entry] based on the scraped content.

    Args:
        entry: individual article object from the newsletter RSS feed
        article_data: default object store for article content

    Returns:
        Dictionary storing fields about the article for future processing
    """
    abstract = getattr(entry, 'summary', '')

    if abstract:
        abstract = ' '.join(abstract.split())

        for pattern in ["new Abstract:", "replace Abstract:", "replace-cross Abstract:", "cross Abstract:"]:
            split_point = abstract.find(pattern)
            if split_point != -1:
                abstract = abstract[split_point + len(pattern):].strip()
                break
        
        if len(abstract.strip()) > 50:
            article_data.update({
                'content': f"{abstract}"
            })
            daily_logger.debug(f"Extracted arXiv abstract: {len(abstract)} characters")
            return article_data
    
    # if no abstract
    daily_logger.warning(f"No content available for {entry.link}, avoid article")
    return None
