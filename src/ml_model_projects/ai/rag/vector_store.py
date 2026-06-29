from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vector_db = None

def create_store(chunks):
    global vector_db
    vector_db = FAISS.from_documents(chunks, embeddings)
    return vector_db


def search(query, k=3):
    return vector_db.similarity_search(query, k=k)
