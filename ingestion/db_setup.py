import os
# import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI")
                        # , tlsCAFile=certifi.where()
                    )
print("Connected")

db = client["narrative_app"]

entities_collection = db["entities"]
documents_collection = db["documents"]
print("Collections ready")

if "url_hash_1" not in documents_collection.index_information():
    documents_collection.create_index("url_hash", unique=True)
    print("Created unique index")

initial_entities = [
    {
        "ticker": "TSLA",
        "name": "Tesla, Inc.",
        "keywords": ["Tesla", "Elon Musk", "Cybertruck", "EV"]
    },  
    {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "keywords": ["Apple", "iPhone", "MacBook", "Tim Cook", "iOS"]
    },
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "keywords": ["NVIDIA", "Jensen Huang", "GPU", "Blackwell", "AI chip"]
    }
]

if entities_collection.count_documents({}) == 0:
    entities_collection.insert_many(initial_entities)
    print("Seeded initial entities")
else:
    for entity in initial_entities:
        if entities_collection.find_one({"ticker": entity['ticker']}) == None:
            entities_collection.insert_one(entity)
            print("Entered", entity['ticker'])
    
print("Database initialized, indexes created, and entities seeded successfully!")