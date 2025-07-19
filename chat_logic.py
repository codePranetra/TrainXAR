# chat_logic.py

import logging
import openai
from typing import List
from pinecone_utils import retrieve_relevant_chunks
from database import store_message, get_conversation_history, init_db
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
        top_chunks = retrieve_relevant_chunks(user_query, os.getenv("PINECONE_INDEX_NAME"))
        context_text = "\n\n".join(top_chunks)
        db_messages = get_conversation_history(user_id)

        # Flags
        injury_flag = contains_injury_keywords(user_query)
        diet_flag = contains_diet_keywords(user_query)
        workout_flag = contains_workout_keywords(user_query)

        # Modify query if injury is mentioned
        if injury_flag:
            user_query += "\n(Note: I’ve mentioned an injury or medical issue above. Please ask if I’ve consulted a doctor and request reports as per system instructions.)"

        # Construct system prompt
        system_prompt = open("system_prompt_milo.txt", "r").read()

        # Prepare chat messages
        messages = [{"role": "system", "content": system_prompt}]

        if context_text:
            messages.append({"role": "assistant", "content": f"Here’s some helpful context:\n{context_text}"})

        # Add past conversation
        for msg in db_messages:
            messages.append({"role": msg.role, "content": msg.content})

        # Special reminder for injury
        if injury_flag:
            messages.append({
                "role": "assistant",
                "content": "User mentioned an injury or medical issue. As per instructions, ask whether they have consulted a doctor and request any reports. Prioritize safety."
            })

        # Insert logic if user repeats diet/workout request
        if diet_flag:
            for msg in reversed(db_messages):
                if "diet plan" in msg.content.lower() and msg.role == "assistant":
                    user_query += "\n(Note: I've already asked for a diet plan. Please continue or complete it without asking again.)"
                    break

        if workout_flag:
            for msg in reversed(db_messages):
                if "workout plan" in msg.content.lower() and msg.role == "assistant":
                    user_query += "\n(Note: I've already asked for a workout plan. Please continue or complete it without asking again.)"
                    break

        # Append user query
        messages.append({"role": "user", "content": user_query})

        # OpenAI response
        response = openai.ChatCompletion.create(
            model='gpt-4.1-nano',
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )

        answer = response["choices"][0]["message"]["content"]
        return answer

    except Exception as e:
        logging.error(f"Error generating response from OpenAI: {e}")
        return "Sorry, I encountered an issue. Please try again later."
