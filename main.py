import openai
from pinecone import Pinecone
from config import OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME
from chat_db import log_to_mysql, get_chat_history
from typing import List, Dict  # Only if using Python 3.8 or lower

# Init OpenAI & Pinecone
openai.api_key = OPENAI_API_KEY
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

def get_embedding(text: str):
    response = openai.Embedding.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response["data"][0]["embedding"]

def query_pinecone(query: str, top_k: int = 5):
    query_embedding = get_embedding(query)
    result = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    matches = getattr(result, "matches", result["matches"])
    texts   = [m.metadata["text"] for m in matches]
    sources = [m.metadata.get("doc_name", "web") for m in matches]
    return texts, sources

def answer_question(
    question: str,
    user_id: str,
    system_prompt: str | None = None,    # Use a default system prompt if needed
):
    # 1) Retrieve context from Pinecone
    context_chunks, _ = query_pinecone(question)
    context_text = "\n\n".join(context_chunks)

    # 2) Pull full chat history from your DB.
    #    chat_history should be a list of dicts in the form:
    #    {"role": "user"/"assistant", "content": ...}
    chat_history = get_chat_history(user_id)

    # 3) Build messages, injection system_prompt if provided.
    messages: List[Dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        # Default system prompt if none provided.
        messages.append({"role": "system", "content": (
            "You are Train XAR's friendly QA assistant. "
            "Train XAR is a premier gym provider in Delhi offering:\n"
            "- Personalized training plans led by certified coaches\n"
            "- State-of-the-art equipment & pristine facilities\n"
            "- Group classes (HIIT, yoga, strength) fostering community\n"
            "- Nutrition guidance and progress tracking\n\n"
            "Answer user questions clearly, accurately, and with an encouraging tone. "
            "Use proper formatting with line breaks (\\n) for better readability. "
            "Use bullet points (-) for lists and **bold** for emphasis. "
            "Structure your responses with clear sections and proper spacing. "
            "If you don't know something, admit it; otherwise, cite relevant sources."
        )})

    messages.extend(chat_history)
    messages.append({
        "role": "user",
        "content": f"Context:\n{context_text}\n\nQuestion: {question}"
    })

    # 4) Call OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,
        max_tokens=500,
    )
    answer = response.choices[0].message.content.strip()

    # 5) Log both question & answer
    log_to_mysql(role="user", message=question, sources=["web"], user_id=user_id)
    log_to_mysql(role="assistant", message=answer, sources=["web"], user_id=user_id)

    return answer, ["web"]  