import feedparser
import time
import os
from newspaper import Article, ArticleException
import requests
from pathlib import Path
from settings import Config, Logger
from utils.data_io import read_json, save_json

config = Config.get_instance()
daily_logger = Logger.get_daily_logger("data_fetch")

def parse_feeds():
    rss_sources = read_json(config.rss_feeds_store)["urls"]

    for newsletter_name, newsletter_url in rss_sources.items():
        output_file = create_file(newsletter_name)
        try:
            articles = parse_rss_feed(newsletter_url)
            os.makedirs(config.document_directory, exist_ok=True)
            save_json(output_file, {newsletter_name: articles})
            time.sleep(3)
        except Exception as e:
            print(f"Error parsing {newsletter_url}: {e}")

def create_file(newsletter):
    output_file = Path(config.document_directory) / f"{newsletter}.json"
    return output_file

def parse_rss_feed(url):
    
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


def extract_article_data(entry):
    article_url = entry.link

    article_data = {
        'title': getattr(entry, 'title', 'No Title'),
        'url': article_url,
        'content': ''
        #'extraction_method': 'failed',
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
            #return rss_fallback_extract(entry, article_data)
        
        article_data.update({
            'content': article.text.strip(),
            'title': article.title if article.title else article_data['title']
            #'extraction_method': 'full_extraction',
        })
        
        daily_logger.debug(f"Extracted article of length {len(article.text)} characters")
        return article_data

    except (requests.exceptions.RequestException, ArticleException) as e:
        daily_logger.warning(f"Failed to download/parse article: {article_url}: {str(e)}")
        #return rss_fallback_extract(entry, article_data)
    except Exception as e:
        daily_logger.warning(f"Failed to extract article data from {article_url}: {str(e)}")
        #return rss_fallback_extract(entry, article_data)
    return None

def extract_arxiv_paper(entry, article_data):
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
                #'extraction_method': 'arxiv_abstract',
            })
            daily_logger.debug(f"Extracted arXiv abstract: {len(abstract)} characters")
            return article_data
    
    # if no abstract
    daily_logger.warning(f"No content available for {entry.link}, avoid article")
    # article_data.update({
    #         'extraction_method': "failed"
    #     })
    #return article_data
    return None

# def rss_fallback_extract(entry, article_data):
#     daily_logger.info(f"Using RSS content as fallback for URL: {entry.link}")
#     content = ""

#     if hasattr(entry, 'content') and entry.content:
#         content = entry.content[0].value
#     elif hasattr(entry, 'description') and entry.description:
#         content = entry.description
#     elif hasattr(entry, 'summary') and entry.summary:
#         content = entry.summary
#     else:
#         daily_logger.warning(f"No content available for {entry.link}, avoid article")
#         article_data.update({
#                 'extraction_method': "failed"
#             })
#         return article_data

#     try:
#         from bs4 import BeautifulSoup
#         soup = BeautifulSoup(content, 'html.parser')
#         text = soup.get_text(separator=' ', strip=True)

#         if len(text.strip()) > 50:
#             article_data.update({
#                 'content': text,
#                 'extraction_method': "description"
#             })
#         else:
#             daily_logger.warning(f"No content available for {entry.link}, avoid article")
#             article_data.update({
#                 'extraction_method': "failed"
#             })
#     except Exception as e:
#         daily_logger.warning(f"Failed to clan RSS content: {str(e)}")
#         article_data.update({
#                 'extraction_method': "failed"
#             })
#     return article_data

if __name__ == "__main__":
    parse_feeds()