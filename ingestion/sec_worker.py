import os
import hashlib
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# 1. Database Setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["narrative_app"]
entities_col = db["entities"]
documents_col = db["documents"]

def generate_hash(url: str) -> str:
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

def fetch_and_store_sec():
    entities = list(entities_col.find({}))
    
    headers = {
        "User-Agent": "NarrativeIntelligencePlatform/1.0 (jayati1550@gmail.com)" 
    }
    
    for entity in entities:
        ticker = entity["ticker"]
        print(f"➔ Querying SEC EDGAR for {ticker} (Form 8-K)...")
        
        # 2. SEC's Official Public Search Index Endpoint
        url = "https://efts.sec.gov/LATEST/search-index"
        
        payload = {
            "q": ticker,
            "forms": ["8-K"]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                print(f"SEC Request failed for {ticker}: Code {response.status_code}")
                continue
                
            hits = response.json().get("hits", {}).get("hits", [])
            print(f"   Found {len(hits)} recent corporate filings.")
            
            for hit in hits:
                source_data = hit.get("_source", {})
                
                # Build a direct link to the filing landing page
                adsh = source_data.get("adsh")
                file_name = source_data.get("file_num")
                doc_url = f"https://www.sec.gov/edgar/browse/?CIK={ticker}"
                
                if not adsh:
                    continue
                    
                # 3. Formulate our uniform structure document
                document = {
                    "entity_id": entity["_id"],
                    "source": "sec_edgar",
                    "url": doc_url,
                    "url_hash": generate_hash(adsh + ticker),
                    "title": f"SEC Form 8-K Material Disclosure - {ticker}",
                    "text": source_data.get("display_names") or source_data.get("items") or "Corporate Material Event Amendment",
                    "published_at": source_data.get("file_date"), 
                    "ingested_at": datetime.now(timezone.utc)
                }
                
                # 4. Safe entry insert
                try:
                    documents_col.insert_one(document)
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error communicating with SEC server for {ticker}: {e}")

if __name__ == "__main__":
    fetch_and_store_sec()
    print("🏁 SEC Filings Ingestion Run Complete!")