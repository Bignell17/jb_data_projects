from vector_store import load_store, search
from llm import ask_llm
from time import time

print("Loading vector store...")
vector_db = load_store()

print("RAG system ready!")

while True:

    question = input("\nAsk a question (or type 'exit'): ")

    start_time = time()

    if question.lower() == "exit":
        break

    docs = search(
        vector_db,
        question,
        k=3
    )

    answer = ask_llm(question, docs)

    question_time = time() - start_time

    print("\nAnswer:\n", answer)
    print(f"\nRetrieved {len(docs)} documents:")

    for i, doc in enumerate(docs, start=1):

        print(
            f"{i}. "
            f"review_id={doc.metadata.get('review_id')} "
            f"category={doc.metadata.get('category')} "
            f"subject={doc.metadata.get('subject_area')}"
        )

    print(f"Time taken to answer: {question_time}")
