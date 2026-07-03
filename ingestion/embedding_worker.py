import os
from datetime import datetime, timezone
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import numpy as np

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["narrative_app"]
documents_col = db["documents"]

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_documents(batch_size=32):
    query = {"embedding": {"$exists": False}}
    total = documents_col.count_documents(query)
    print(f"Found {total} unembedded documents.")

    if total == 0:
        print("\tNothing to embed.")
        return

    processed = 0
    cursor = documents_col.find(query)

    batch_docs = []
    batch_ids = []

    for doc in cursor:
        title = doc.get("title") or ""
        text = doc.get("text") or ""
        content = f"{title}. {text}".strip()

        batch_docs.append(content)
        batch_ids.append(doc["_id"])

        if len(batch_docs) == batch_size:
            _embed_and_store(batch_docs, batch_ids)
            processed += len(batch_docs)
            print(f"\tEmbedded {processed}/{total}")
            batch_docs = []
            batch_ids = []

    # Handle remaining documents
    if batch_docs:
        _embed_and_store(batch_docs, batch_ids)
        processed += len(batch_docs)
        print(f"\tEmbedded {processed}/{total}")

    print("Embedding complete.")

def _embed_and_store(texts, ids):
    embeddings = model.encode(texts, normalize_embeddings=True)

    for doc_id, embedding in zip(ids, embeddings):
        documents_col.update_one(
            {"_id": doc_id},
            {"$set": {
                "embedding": embedding.tolist(),
                "embedded_at": datetime.now(timezone.utc)
            }}
        )

if __name__ == "__main__":
    embed_documents()