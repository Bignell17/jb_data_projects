from ingest import load_and_chunk
from vector_store import create_store, search
from ml_model_projects.ai.rag.llm import ask_llm
import os
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()
print("Loading document...")
chunks = load_and_chunk("documents/manual.pdf")

print("Creating vector store...")
create_store(chunks)

print("RAG system ready!")

while True:
    question = input("\nAsk a question (or type 'exit'): ")

    if question.lower() == "exit":
        break

    docs = search(question)

    answer = ask_llm(question, docs)

    print("\nAnswer:\n", answer)
