import os
import hashlib
import feedparser
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["narrative_app"]
entities_col = db["entities"]
documents_col = db["documents"]

def generate_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

def build_rss_url(keywords: list) -> str:
    query = "+".join(keywords[0].split())
    return f"https://news.google.com/rss/search?q={query}+stock&hl=en-US&gl=US&ceid=US:en"

def fetch_rss_for_entity(entity: dict) -> int:
    ticker = entity["ticker"]
    rss_url = build_rss_url(entity["keywords"])
    
    print(f"➔ Fetching RSS for {ticker}...")
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print(f"   No entries found for {ticker}")
        return 0

    saved = 0
    for entry in feed.entries:
        url = entry.get("link")
        if not url:
            continue

        # Parse published date
        published = None
        if entry.get("published_parsed"):
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        else:
            published = datetime.now(timezone.utc)

        # RSS gives cleaner, fuller summaries than NewsAPI free tier
        summary = entry.get("summary") or ""
        title = entry.get("title") or "Untitled"

        document = {
            "entity_id": entity["_id"],
            "source": "google_rss",
            "url": url,
            "url_hash": generate_hash(url),
            "title": title,
            "text": summary,
            "published_at": published,
            "ingested_at": datetime.now(timezone.utc)
        }

        try:
            documents_col.insert_one(document)
            saved += 1
        except DuplicateKeyError:
            continue
        except Exception as e:
            print(f"   Error saving: {e}")
            continue

    print(f"   Saved {saved} new articles for {ticker}")
    return saved

def fetch_all_entities():
    entities = list(entities_col.find({}))
    total = 0
    for entity in entities:
        total += fetch_rss_for_entity(entity)
    print(f"\nRSS ingestion complete. Total new documents: {total}")

if __name__ == "__main__":
    fetch_all_entities()