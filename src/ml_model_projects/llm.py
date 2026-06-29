import ollama

def ask_llm(question, docs):

    context = "\n".join([d.page_content for d in docs])

    prompt = f"""
    Context:
    {context}

    Question:
    {question}

    Answer using only the context above.
    """

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]