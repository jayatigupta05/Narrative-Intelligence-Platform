import os
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

client = MongoClient(os.getenv('MONGO_URI'))
db = client['narrative_app']
documents_col = db['documents']

