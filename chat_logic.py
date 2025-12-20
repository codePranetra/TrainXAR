import logging
import openai
from typing import List
from pinecone_utils import retrieve_relevant_chunks
from database import get_user_meta, store_message, get_conversation_history, init_db, update_user_meta
import os

init_db()
openai.api_key = os.getenv("OPENAI_API_KEY")

def contains_injury_keywords(text: str) -> bool:
    injury_keywords = [
        "injury", "injured", "pain", "discomfort", "hurt", "surgery",
        "fracture", "wound", "diagnosed", "sprain", "strain", "broken", "healing", "sustained"
    ]
    return any(word in text.lower() for word in injury_keywords)

def contains_diet_keywords(text: str) -> bool:
    diet_keywords = ["diet", "meal", "food plan", "nutrition", "calories", "vegetarian", "vegan"]
    return any(word in text.lower() for word in diet_keywords)

def contains_workout_keywords(text: str) -> bool:
    workout_keywords = ["workout", "exercise", "training", "routine", "gym", "fitness plan"]
    return any(word in text.lower() for word in workout_keywords)


def get_answer(user_query: str, user_id: str) -> str:
    try:
        # Retrieve context and chat history
        # top_chunks = retrieve_relevant_chunks(user_query, os.getenv("PINECONE_INDEX_NAME"))
        # context_text = "\n\n".join(top_chunks)
        db_messages = get_conversation_history(user_id)
        logging.info(f"[History] Messages for user_id {user_id}: {db_messages}")


        # Construct system prompt
        # system_prompt = open("system_prompt_milo.txt", "r").read()
        system_prompt = """
            You are a math tutor chatbot designed to help students prepare for competitive exams like GATE.

            FIRST MESSAGE (must be said exactly as written):
            Hello! I'm here to help you with your math questions. Feel free to ask anything related to the topics covered in the provided videos.

            Rules you MUST follow:
            - Answer student questions ONLY using the provided context data.
            - If a topic is NOT present in the context, clearly say that it is not available.
            - Provide a short summary before explanations.
            - Explain concepts step by step like a tutor.
            - Reference the exact video where the explanation comes from.
            - Include ONLY the YouTube video link (no timestamps).
            - Do NOT invent formulas, topics, or examples outside the context.
            - Be friendly, encouraging, and clear.

            Required response format:

            Summary:
            <1–3 sentence topic summary>

            Step-by-step explanation:
            Step 1: ... (Video: <link>)
            Step 2: ... (Video: <link>)
        """


        context_data = """
[
  {
    "main_topic": "Free Engineering Mathematics preparation course for GATE 2025 and 2026",
    "sub_topics": [
      "Importance of Engineering Mathematics across all GATE branches",
      "Free live classes, recorded lectures, and PDF notes",
      "Coverage of core mathematics subjects like Linear Algebra, Calculus, Probability, and Numerical Methods",
      "Topic-wise practice of previous 7–8 years GATE questions with shortcuts",
      "Free test series and practice questions for GATE aspirants",
      "Access to course content through the Maths Care mobile app"
    ],
    "link": "https://www.youtube.com/watch?v=Na2M5WcjOv8"
  },
  {
    "main_topic": "Concept of sequences, convergence, divergence, and oscillation for competitive mathematics exams",
    "sub_topics": [
      "Definition of a sequence as a function from natural numbers to real numbers",
      "Bounded and monotonic sequences and their role in convergence",
      "Limit point and limit of a sequence using examples like 1/n and constant sequences",
      "Non-monotonic but bounded sequences with unique limit points",
      "Oscillating sequences and conditions where limits do not exist",
      "Divergent sequences due to unbounded growth or decay",
      "Solving GATE and competitive exam questions on limits of sequences using standard tricks"
    ],
    "link": "https://www.youtube.com/watch?v=0oaxIzXQB2E"
  },
  {
    "main_topic": "Rank of Matrix: concepts, properties, and problem-solving using determinants and row transformations for GATE exam",
    "sub_topics": [
      "Definition of rank of a matrix using non-zero determinant submatrices",
      "Interpretation of rank as the number of linearly independent rows or columns",
      "Finding rank using determinants for square matrices",
      "Finding rank using row transformations and echelon form",
      "Rank of special matrices: zero matrix, identity matrix, and all-ones matrix",
      "Properties of rank including rank(A) = rank(Aᵀ) and rank ≤ min(m, n)",
      "Relationship between rank, nullity, and order of a matrix",
      "Solving GATE-level multiple-choice questions based on rank of matrices"
    ],
    "link": "https://www.youtube.com/watch?v=q0P5j1ti3tg"
  }
]
"""

        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "system",
                "content": f"""CONTEXT DATA (use strictly for answering questions): {context_data}"""
            }
        ]

        # Append previous conversation history (if any)
        # db_messages must already be in [{"role": "...", "content": "..."}] format
        messages.extend(db_messages)

        # Append current user query
        messages.append({
            "role": "user",
            "content": user_query
        })

        logging.info(messages)

        
        # OpenAI response
        response = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )

        answer = response["choices"][0]["message"]["content"]   
        return answer

    except Exception as e:
        logging.error(f"Error generating response from OpenAI: {e}")
        return "Sorry, I encountered an issue. Please try again later."


