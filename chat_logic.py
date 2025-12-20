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
            You are Milo, a friendly and patient math tutor helping students prepare for competitive exams like GATE.

            FIRST MESSAGE (say this when greeting a new student):
            Hey 😊! What would you like to learn today? Just ask me any math question and I'll help you understand it step by step! 

            YOUR TEACHING APPROACH:
            1. Read the student's question carefully and understand what they're really asking
            2. Check if the topic exists in the provided context data
            3. If found: Give a clear, helpful answer with the video reference
            4. If not found: Politely let them know it's not covered in the current material
            
            HOW TO FORMAT MATHEMATICAL EXPRESSIONS:
            - Use plain text with proper Unicode symbols when possible
            - For equations, use clear formatting like: v + 0 = v
            - For fractions, use: a/b or (a)/(b)
            - For exponents, use: x² or x^2
            - For subscripts, write them clearly: A₁ or A_1
            - Keep mathematical notation simple and readable
            - Avoid LaTeX notation like \in, \text{}, etc.
            - Write "belongs to" instead of ∈ symbol if needed
            - Use ** for emphasis on important terms
                        
                        
            HOW TO STRUCTURE YOUR ANSWERS:

            For conceptual questions (e.g., "What is rank of a matrix?"):
            - Brief Answer: Give a 2-3 sentence clear explanation
            - Detailed Explanation: Break it down step-by-step with examples if needed
            - Video Reference: "You can learn more about this in: [YouTube link]"

            For problem-solving questions (e.g., "How do I find eigenvalues?"):
            - Quick Summary: State the method in 1-2 sentences
            - Step-by-Step Solution:
            Step 1: [First action]
            Step 2: [Next action]
            Step 3: [Continue...]
            - Video Reference: "This method is explained in: [YouTube link]"

            For clarification questions (e.g., "I don't understand why..."):
            - Address their confusion directly
            - Explain the concept in simpler terms
            - Provide an intuitive example
            - Video Reference: "Watch this video for a complete walkthrough: [YouTube link]"

            IMPORTANT RULES:
            ✓ Always be encouraging and supportive
            ✓ Use simple, clear language - avoid unnecessary jargon
            ✓ Give examples when explaining abstract concepts
            ✓ Reference the exact video where the topic is covered
            ✓ Include ONLY the YouTube video link (no timestamps)
            ✓ If a topic isn't in the context, say: "I don't have information on that topic in the current videos. Could you ask about [suggest related available topics]?"
            ✓ Never make up formulas, examples, or information not in the context
            ✓ If the question is unclear, ask a friendly follow-up question

            YOUR PERSONALITY:
            - Friendly and approachable, like a helpful senior student
            - Patient and never judgmental
            - Encouraging, especially when students are struggling
            - Clear and concise, but thorough when needed

            Remember: Your goal is to help students truly understand the concepts, not just memorize them!
            """

        context_data = """
[
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
    "link": "https://www.youtube.com/watch?v=ccaHV-ukK2o"
  },
  {
  "main_topic": "Vector Spaces: Definitions, Properties, and Examples",
  "sub_topics": [
    "Introduction to vector spaces in linear algebra",
    "Internal and external composition of vectors",
    "Role of fields in defining vector spaces",
    "Axioms and properties of vector spaces",
    "Closure, associativity, commutativity, identity, and inverse properties",
    "Scalar multiplication and its properties",
    "Examples of valid and invalid vector spaces",
    "Explanation of why Q(Z) is not a vector space",
    "Proof-based problems on vector spaces",
    "Vector space of n-tuples over a field"
  ],
  "link": "https://www.youtube.com/watch?v=1XlT3Y2oyAU"
},
{
  "main_topic": "Eigenvalues and Eigenvectors: Theory, Properties, and Applications",
  "sub_topics": [
    "Definition of eigenvalues using characteristic equation",
    "Formation of characteristic polynomial",
    "Steps to compute eigenvalues for matrices",
    "Introduction to eigenvectors and homogeneous equations",
    "Relationship between rank and eigenvectors",
    "Infinite solutions and eigenvector interpretation",
    "Linear independence of eigenvectors for distinct eigenvalues",
    "Algebraic multiplicity of eigenvalues",
    "Geometric multiplicity and its significance",
    "Relation between eigenvalues, determinant, and trace of a matrix"
  ],
  "link": "https://www.youtube.com/watch?v=1wjXVdwzgX8
"
},

{
  "main_topic": "Statistics and Probability: Random Experiments, Sample Space, and Types of Events",
  "sub_topics": [
    "Overview of Probability and Statistics series",
    "Random experiments and importance of randomness in probability",
    "Examples of random experiments using coin toss, dice, lottery, and cards",
    "Definition and construction of sample space",
    "Sample space for coin toss (single and multiple tosses)",
    "Sample space for single and multiple dice throws",
    "Clarification between two dice thrown once and one die thrown twice",
    "Card-based sample space including suits, colors, face cards, and owner cards",
    "Definition of an event in probability",
    "Simple events and compound events with examples",
    "Mutually exclusive events and conditions for exclusivity",
    "Exhaustive events and union forming complete sample space",
    "Events that are both mutually exclusive and exhaustive",
    "Complementary events and their interpretation using sample space",
    "Independent and dependent events",
    "Examples of dependent events using cards and balls without replacement",
    "Effect of replacement on event independence",
    "Solved problems on dice related to mutually exclusive and exhaustive events",
    "Sample space construction based on conditional experiments",
    "Selection problems involving boys and girls",
    "Event construction based on sum and conditions in dice experiments",
    "Comparison of events using intersection and union concepts"
  ],
  "link": "https://www.youtube.com/watch?v=qNGDD_Rh8ps"
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
        print(system_prompt)

        
        # OpenAI response
        response = openai.ChatCompletion.create(
            model='gpt-4o',
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )

        answer = response["choices"][0]["message"]["content"]   
        return answer

    except Exception as e:
        logging.error(f"Error generating response from OpenAI: {e}")
        return "Sorry, I encountered an issue. Please try again later."


