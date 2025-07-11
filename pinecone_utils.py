import openai
import logging
from pinecone import Pinecone, ServerlessSpec
from config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_ENV,
    EMBED_MODEL,
    TOP_K
)
# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize Pinecone client globally
pc = Pinecone(api_key=PINECONE_API_KEY)
available_indexes = set(pc.list_indexes().names())  # Cache index names


def get_index(index_name: str):
    """
    Retrieve or create a Pinecone index dynamically, caching results for efficiency.
    """
    if index_name not in available_indexes:
        # logging.info(f"Creating new Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV),
        )
        available_indexes.add(index_name)  # Update cached index list

    return pc.Index(index_name)


def get_embedding(text: str, model: str = EMBED_MODEL) -> list:
    """
    Generate an embedding for the given text using OpenAI's embedding model.
    """
    try:
        response = openai.Embedding.create(
            input=[text],
            model=model
        )
        return response["data"][0]["embedding"]
    except Exception as e:
        # logging.error(f"Error getting embedding: {e}")
        return []


def retrieve_relevant_chunks(query: str, index_name: str, top_k: int = TOP_K) -> list:
    """
    Retrieve top_k relevant chunks from the specified Pinecone index.
    """
    query_vector = get_embedding(query)
    if not query_vector:
        return []

    try:
        index = get_index(index_name)  # Dynamically get or create index
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
        # Extract text from metadata
        top_chunks = [match["metadata"]["text"] for match in results["matches"]]
        return top_chunks
    except Exception as e:
        # logging.error(f"Error querying Pinecone: {e}")
        return []
