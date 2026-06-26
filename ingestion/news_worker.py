import os
import hashlib
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# 1. Connect to Database
client = MongoClient(os.getenv("MONGO_URI"))
db = client["narrative_app"]
entities_col = db["entities"]
documents_col = db["documents"]

def generate_hash(url: str) -> str:
    """Creates a unique fixed-length string for deduplication."""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

def fetch_and_store_news():
    # Grab our tracking list from Atlas
    entities = list(entities_col.find({}))
    
    for entity in entities:
        ticker = entity["ticker"]
        query = entity["keywords"][0]
        print(f"➔ Fetching news for {ticker}...")
        
        # 2. Make the Network Request
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "pageSize": 10,  # Grab 10 fresh articles per stock
            "apiKey": os.getenv("NEWS_API_KEY")
        }
        
        response = requests.get(url, params=params, headers={"User-Agent": "NarrativeApp"})
        if response.status_code != 200:
            print(f"Error {response.status_code} for {ticker}")
            continue
            
        # 3. Parse the Articles
        articles = response.json().get("articles", [])
        print(f"   Found {len(articles)} articles.")
        
        for art in articles:
            art_url = art.get("url")
            if not art_url:
                continue  # Skip if there's no link
                
            # 4. Map to our Uniform Schema
            document = {
                "entity_id": entity["_id"],  # Connects this article to our stock
                "source": "newsapi",
                "url": art_url,
                "url_hash": generate_hash(art_url),
                "title": art.get("title") or "Untitled",
                "text": art.get("description") or art.get("content") or "",
                "published_at": art.get("publishedAt"), # Kept simple for now
                "ingested_at": datetime.now(timezone.utc)
            }
            
            # 5. Safe Save to DB
            try:
                documents_col.insert_one(document)
            except Exception:
                continue

if __name__ == "__main__":
    fetch_and_store_news()
    print("Ingestion complete!")