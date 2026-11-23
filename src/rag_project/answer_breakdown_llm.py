import ollama
import json


MODEL_NAME = "llama3.2:latest"


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

            documents.append(
                {
                    "question": data["input"],
                    "answer": data["output"],
                    "category": data["category"],
                    "subject_area": data["subject_area"],
                    "source": jsonl_path,
                    "line": line_number
                }
            )

    return documents



def ask_llm(doc):

    context_parts = []

    prompt = f"""
Query Decomposition Rules

Generate a Subject Area before all subquestions.

Base it on the question, category, and subject fields.
Provide high-level context for the generated Q&A set.

Generate multiple focused subquestions where possible.

Split complex content into smaller question-answer pairs.
Each question should cover only one topic.

Generate a separate Q&A pair for every:

Acronym definition.
Process, workflow, or procedure.
Individual fact, concept, requirement, or explanation.

Use only information found in the source question and answer fields.

Do not use external knowledge.
Do not use information from other fields except when creating the Subject Area.

Never infer, assume, extrapolate, or invent information.

If an answer is not explicitly present, do not create a question for it.

Make all questions and answers self-contained.

Replace vague references such as "he", "she", "they", "it", "this", or "that" with explicit identifiers when available.
Ensure each Q&A can be understood independently.

Preserve the meaning of the source content.

Rephrase only when required for clarity.
Do not add interpretations or new information.

Preserve the exact input schema and property names when generating output.

Prioritize generated content in this order:

Subject Area
Acronym definitions
Processes/workflows
Facts, concepts, and requirements
Additional meaningful subquestions

Include all acronym definitions at the end of the output.

Include every acronym found in the source.
Include it even if the acronym already appeared in a generated Q&A pair.
Required Output Format:
`
Subject Area: 'subject area'

Q: 'Subquestion'
A: 'Answer'

Q: 'Subquestion'
A: 'Answer'

Acronym: 'Definition'
Acronym: 'Definition'
Acronym: 'Definition'
`

Acronym Handling Rules
Every acronym with an explicit definition must:
- Generate its own Q&A pair.
- Appear again in the final acronym list.
Never assume the meaning of an acronym, it must be explicitly stated.

Example:
`
Subject Area: 'Retrieval-Augmented Generation?'

Q: 'What does RAG stand for?'
A: 'Retrieval-Augmented Generation.'

Q: 'How does Retrieval-Augmented Generation work?'
A: 'Retrieval-Augmented Generation retrieves relevant information and provides it as context before generating a response.'

Acronym: 'RAG = Retrieval-Augmented Generation'
`

Validation Checklist

Before returning the output:

✅ Subject Area exists.
✅ Each Q&A covers one topic only.
✅ Every acronym has a dedicated Q&A pair.
✅ Every acronym appears in the final acronym list.
✅ Every process has a dedicated Q&A pair.
✅ No unsupported information has been added.
✅ No vague pronouns remain where a specific identifier is available.
✅ Output follows the exact required format.

Question and Answer:
{doc}
"""

    # print(prompt)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature":0,
            "seed":42
        }
    )

    return response["message"]["content"]


def normalize_answers(docs):
    answers = []

    for doc in docs:

        answers.append(ask_llm(doc=doc))

    return answers


documents = load_and_chunk("documents/approved.jsonl")
answer = ask_llm(documents[0])

print(answer)


