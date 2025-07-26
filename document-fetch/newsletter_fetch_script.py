import feedparser
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from pathlib import Path
from settings.app_config import config

def parse_feeds():
    with open(config.rss_feeds_store, 'r') as f:
        rss_sources = json.load(f)["urls"]

    for url in rss_sources:
        output_file = create_file(url)
        try:
            articles = parse_feed(url)
            with open(output_file, 'w', encoding="utf-8") as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error parsing {url}: {e}")
    
def parse_feed(url):

    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries:
        title = entry.get("title", "").strip()
        #link = entry.get("link", "").strip()
        #published = entry.get("pubDate", "").strip()

        description = ""
        if "content" in entry and entry.content:
            description_html = entry.content[0].value

            relevant_paragraphs = extract_first_few_paragraphs(description_html)
            description = "\n\n".join(relevant_paragraphs)

        else:
            description = clean_description(entry.get("description", "").strip())

        if not title or not description:
            continue

        combined_text = f"{title}\n\n{description}"
        articles.append({
            "title": title,
            "description": description,
            "combined_text": combined_text
        })
    return articles

def clean_description(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.text

def create_file(url):
    domain = urlparse(url).netloc.split('.')[-2] + "_newsletter"
    output_file = Path(config.document_directory) / f"{domain}.json"
    return output_file

def extract_first_few_paragraphs(html, num_paragraphs=3):
    soup = BeautifulSoup(html, 'html.parser')
    
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
    
    filtered_paragraphs = []
    for p in paragraphs:
        lower = p.lower()
        if "welcome to import ai" in lower or "subscribe" in lower or "feedback from readers" in lower:
            continue
        filtered_paragraphs.append(p)

    return filtered_paragraphs[:num_paragraphs]

if __name__ == "__main__":
    parse_feeds()