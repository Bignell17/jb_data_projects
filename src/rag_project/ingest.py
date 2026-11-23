import json

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_chunk(jsonl_path):
    if not jsonl_path.lower().endswith(".jsonl"):
        raise ValueError("Only .jsonl files are supported")

    documents = []

    with open(jsonl_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {e}"
                ) from e

            # Validate required fields
            required_fields = [
                "approval_id",
                "review_id",
                "input",
                "output",
                "category",
                "subject_area"
            ]

            missing_fields = [
                field for field in required_fields
                if field not in data
            ]

            if missing_fields:
                raise ValueError(
                    f"Missing fields on line {line_number}: "
                    f"{missing_fields}"
                )

            # Combine question and answer into searchable content
            content = (
                f"Conversation Context:\n{data['input']}\n\n"
                f"Response:\n{data['output']}"
            )

            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "approval_id": data["approval_id"],
                        "review_id": data["review_id"],
                        "category": data["category"],
                        "subject_area": data["subject_area"],
                        "source": jsonl_path,
                        "line": line_number
                    }
                )
            )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)

    return chunks


if __name__ == "__main__":
    from vector_store import create_store

    print("Loading JSONL...")
    chunks = load_and_chunk("documents/approved.jsonl")

    print(f"Loaded {len(chunks)} chunks")

    print("Creating vector store...")
    create_store(chunks)

    print("Vector store created successfully!")



