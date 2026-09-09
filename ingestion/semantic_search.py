import os
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

client = MongoClient(os.getenv('MONGO_URI'))
db = client['narrative_app']
documents_col = db['documents']

def semantic_search(query):
    query_vector = model.encode(query).tolist()
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": 5
            }
        },{
            "$project": {
                "_id": 0,
                "title": 1,
                "source": 1,
                "published_at": 1,
                "text": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    results = documents_col.aggregate(pipeline)
    return list(results)

if __name__ == "__main__":
    # test_query = "Why are tesla stock prices dropping?"
    # test_query = "What are the latest advancements in AI technology?"
    test_query = "Why is Apple stock price not constant?"
    
    print(f"Searching for: '{test_query}'\n")
    
    search_results = semantic_search(test_query)
    
    for idx, doc in enumerate(search_results, 1):
        print(f"--- Result {idx} (Score: {doc.get('score'):.4f}) ---")
        print(f"Title: {doc.get('title')}")
        print(f"Source: {doc.get('source')} | Published: {doc.get('published_at')}")
        print(f"Snippet: {doc.get('text')[:150]}...\n")