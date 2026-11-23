from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


MODEL_PATH = (
    r"C:\Users\daniel.jennings\OneDrive - Correla Limited"
    r"\Desktop\rag_project\all-MiniLM"
    r"\models--sentence-transformers--all-MiniLM-L6-v2"
    r"\snapshots\1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
)

VECTOR_DB_PATH = "vector_db"

embeddings = HuggingFaceEmbeddings(
    model_name=MODEL_PATH
)


def create_store(chunks):

    # Flat Search
    # vector_db = FAISS.from_documents(chunks, embeddings)

    # HNSW Search
    import faiss
    from langchain_community.vectorstores import FAISS
    from langchain_community.docstore.in_memory import InMemoryDocstore

    dimension = len(embeddings.embed_query("test"))

    index = faiss.IndexHNSWFlat(
        dimension,
        32  # M
    )

    index.hnsw.efSearch = 128

    vector_db = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={}
    )

    vector_db.add_documents(chunks)

    vector_db.save_local(VECTOR_DB_PATH)

    return vector_db


def load_store():
    vector_db = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)

    return vector_db


def search(vector_db, query, k=3):
    return vector_db.similarity_search(query, k=k)