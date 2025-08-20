import os
import logging
import json
from flask import jsonify, request
from chat_logic import get_answer
from database import store_message, get_user_message
import openai

def generate_diet_suggestion(data):
    """
    Generate diet plan suggestions based on user input
    Expected input: calories, diet_type, meals_per_day, etc.
    """
    try:
        # Extract form data
        calories = data.get("calories", "")
        diet_type = data.get("diet_type", "veg")  # veg, non-veg, vegan, keto, eggetarian
        meals_per_day = data.get("meals_per_day", "3")
        user_id = data.get("user_id", "frontend_user")
        
        # Create a structured prompt for diet plan generation
        diet_prompt = f"""
        Generate a detailed 7-day diet plan with the following specifications:
        
        - Daily calorie target: {calories} calories
        - Diet type: {diet_type}
        - Meals per day: {meals_per_day}
        
        Please provide a structured response in JSON format with the following structure:
        {{
            "daily_calories": {calories},
            "macronutrients": {{
                "protein": "X grams (X%)",
                "carbohydrates": "X grams (X%)", 
                "fats": "X grams (X%)"
            }},
            "micronutrients_focus": ["Iron", "Vitamin B12"],
            "weekly_plan": [
                {{
                    "day": "Day 1",
                    "meals": [
                        {{
                            "meal_type": "Breakfast",
                            "meal_name": "Oatmeal with fruits",
                            "food_items": ["Oats", "Banana", "Honey"],
                            "portions": ["1 cup", "1 medium", "1 tsp"],
                            "calories": 300
                        }},
                        // ... more meals
                    ]
                }}
                // ... more days
            ]
        }}
        
        Important notes:
        - If diet_type is 'vegetarian', do NOT include eggs
        - If diet_type is 'eggetarian', include eggs but no meat
        - Ensure total daily calories match the target
        - Provide 2-3 meal options per slot
        - Include portion sizes in familiar units
        """
        
        # Store the request
        store_message(user_id=user_id, role="user", content=f"Diet request: {calories} calories, {diet_type} diet", source="api")
        
        # Get AI response
        ai_response = get_answer(diet_prompt, user_id)
        
        # Store the response
        store_message(user_id=user_id, role="assistant", content=ai_response, source="api")
        
        # Try to parse as JSON if possible, otherwise return as text
        try:
            import json
            # Extract JSON from the response if it's wrapped in markdown
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
                parsed_response = json.loads(json_str)
            else:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    parsed_response = json.loads(json_match.group())
                else:
                    parsed_response = {"text_response": ai_response}
        except:
            parsed_response = {"text_response": ai_response}
        
        return jsonify({
            "success": True,
            "message": "Diet plan generated successfully",
            "data": parsed_response
        }), 200
        
    except Exception as e:
        logging.error(f"Error generating diet suggestion: {e}")
        return jsonify({
            "success": False,
            "message": "Error generating diet plan",
            "error": str(e)
        }), 500

def generate_meal_suggestions(data):
    """
    Generate meal suggestions in the exact format expected by the frontend
    Returns data structure matching dietFormData
    """
    try:
        # Extract input parameters
        calories = data.get("calories_per_day", 2000)
        protein = data.get("protein", "150g")
        carbs = data.get("carbs", "200g") 
        fats = data.get("fats", "65g")
        dietary_restrictions = data.get("dietary_restrictions", [])
        user_id = data.get("user_id", "frontend_user")
        
        # Create a structured prompt for meal plan generation
        meal_prompt = f"""
        You are a nutrition expert. Generate a COMPACT 7-day meal plan in the exact JSON format specified below.
        
        Requirements:
        - Daily calories: {calories}
        - Protein: {protein}
        - Carbs: {carbs}
        - Fats: {fats}
        - Dietary restrictions: {dietary_restrictions}
        
        IMPORTANT: Respond ONLY with the JSON object, no other text or conversation.
        Keep meal names short and ingredients minimal (2-3 items max).
        
        Return ONLY a valid JSON object with this exact structure:
        {{
            "calories_per_day": {calories},
            "macronutrients": {{
                "protein": "{protein}",
                "carbs": "{carbs}",
                "fats": "{fats}"
            }},
            "dietary_restrictions": {dietary_restrictions},
            "duration_weeks": 1,
            "monday_meals": {{
                "breakfast": {{
                    "name": "Meal name",
                    "calories": 400,
                    "ingredients": ["ingredient1", "ingredient2"],
                    "macros": {{
                        "protein": "25g",
                        "carbs": "45g",
                        "fats": "15g"
                    }}
                }},
                "lunch": {{
                    "name": "Meal name",
                    "calories": 500,
                    "ingredients": ["ingredient1", "ingredient2"],
                    "macros": {{
                        "protein": "35g",
                        "carbs": "55g",
                        "fats": "20g"
                    }}
                }},
                "dinner": {{
                    "name": "Meal name",
                    "calories": 450,
                    "ingredients": ["ingredient1", "ingredient2"],
                    "macros": {{
                        "protein": "30g",
                        "carbs": "40g",
                        "fats": "20g"
                    }}
                }},
                "snacks": [
                    {{
                        "name": "Snack name",
                        "calories": 150,
                        "protein": "10g",
                        "fats": "8g"
                    }}
                ]
            }},
            "tuesday_meals": {{...}},
            "wednesday_meals": {{...}},
            "thursday_meals": {{...}},
            "friday_meals": {{...}},
            "saturday_meals": {{...}},
            "sunday_meals": {{...}}
        }}
        
        Guidelines:
        - Ensure total daily calories match {calories}
        - Respect dietary restrictions: {dietary_restrictions}
        - Provide realistic, healthy meal options
        - Include 1-2 snacks per day (keep it minimal)
        - Use short meal names and minimal ingredients (2-3 max)
        - Ensure macros add up appropriately
        - Make meals varied but keep descriptions brief
        
        CRITICAL: Do not include any conversational text, greetings, or explanations. Return ONLY the JSON object.
        Keep the response compact and under 2000 characters.
        """
        
        # Store the request
        store_message(user_id=user_id, role="user", content=f"Meal suggestion request: {calories} calories", source="api")
        
        # Get AI response directly from OpenAI
        try:
            import openai
            from config import OPENAI_API_KEY
            
            openai.api_key = OPENAI_API_KEY
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a nutrition expert. Generate meal plans in JSON format only. Do not include any conversational text or greetings."
                    },
                    {
                        "role": "user",
                        "content": meal_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
        except Exception as openai_error:
            logging.error(f"OpenAI API error: {openai_error}")
            # Fallback to chat logic
            ai_response = get_answer(meal_prompt, user_id)
        
        # Store the response
        store_message(user_id=user_id, role="assistant", content=ai_response, source="api")
        
        # Parse the JSON response
        try:
            # Extract JSON from the response if it's wrapped in markdown
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                if json_end == -1:
                    # If no closing ```, take everything after ```json
                    json_str = ai_response[json_start:].strip()
                else:
                    json_str = ai_response[json_start:json_end].strip()
                parsed_response = json.loads(json_str)
            elif "```" in ai_response:
                # Handle other code blocks
                json_start = ai_response.find("```") + 3
                json_end = ai_response.find("```", json_start)
                if json_end == -1:
                    # If no closing ```, take everything after ```
                    json_str = ai_response[json_start:].strip()
                else:
                    json_str = ai_response[json_start:json_end].strip()
                parsed_response = json.loads(json_str)
            else:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    parsed_response = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
                    
        except Exception as parse_error:
            logging.error(f"Error parsing JSON response: {parse_error}")
            # Try to fix common JSON issues
            try:
                # Remove any trailing text after the JSON
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    # Try to fix common issues
                    json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                    # Try to complete truncated JSON
                    if json_str.count('{') > json_str.count('}'):
                        # Add missing closing braces
                        missing_braces = json_str.count('{') - json_str.count('}')
                        json_str += '}' * missing_braces
                    parsed_response = json.loads(json_str)
                else:
                    raise ValueError("Could not extract valid JSON")
            except Exception as fix_error:
                # Return a simplified response if parsing fails
                return jsonify({
                    "success": True,
                    "message": "Meal plan generated successfully (simplified)",
                    "data": {
                        "calories_per_day": calories,
                        "macronutrients": {
                            "protein": protein,
                            "carbs": carbs,
                            "fats": fats
                        },
                        "dietary_restrictions": dietary_restrictions,
                        "duration_weeks": 1,
                        "monday_meals": {
                            "breakfast": {
                                "name": "Oatmeal with Berries",
                                "calories": 300,
                                "ingredients": ["oats", "berries"],
                                "macros": {"protein": "10g", "carbs": "50g", "fats": "5g"}
                            },
                            "lunch": {
                                "name": "Chicken Salad",
                                "calories": 400,
                                "ingredients": ["chicken", "lettuce"],
                                "macros": {"protein": "30g", "carbs": "20g", "fats": "15g"}
                            },
                            "dinner": {
                                "name": "Salmon with Rice",
                                "calories": 500,
                                "ingredients": ["salmon", "rice"],
                                "macros": {"protein": "35g", "carbs": "40g", "fats": "20g"}
                            },
                            "snacks": [
                                {"name": "Apple", "calories": 100, "protein": "1g"}
                            ]
                        },
                        "tuesday_meals": None,
                        "wednesday_meals": None,
                        "thursday_meals": None,
                        "friday_meals": None,
                        "saturday_meals": None,
                        "sunday_meals": None
                    }
                }), 200
        
        return jsonify({
            "success": True,
            "message": "Meal plan generated successfully",
            "data": parsed_response
        }), 200
        
    except Exception as e:
        logging.error(f"Error generating meal suggestions: {e}")
        return jsonify({
            "success": False,
            "message": "Error generating meal plan",
            "error": str(e)
        }), 500

def get_diet_form_fields():
    """
    Return the structure of diet form fields for frontend integration
    """
    form_structure = {
        "fields": [
            {
                "name": "calories",
                "label": "Daily Calorie Target",
                "type": "number",
                "placeholder": "e.g., 2000",
                "required": True
            },
            {
                "name": "diet_type",
                "label": "Diet Type",
                "type": "select",
                "options": [
                    {"value": "veg", "label": "Vegetarian"},
                    {"value": "non-veg", "label": "Non-Vegetarian"},
                    {"value": "vegan", "label": "Vegan"},
                    {"value": "keto", "label": "Keto"},
                    {"value": "eggetarian", "label": "Eggetarian"}
                ],
                "required": True
            },
            {
                "name": "meals_per_day",
                "label": "Meals per Day",
                "type": "select",
                "options": [
                    {"value": "3", "label": "3 meals"},
                    {"value": "4", "label": "4 meals"},
                    {"value": "5", "label": "5 meals"},
                    {"value": "6", "label": "6 meals"}
                ],
                "required": True
            },
            {
                "name": "height",
                "label": "Height (cm)",
                "type": "number",
                "placeholder": "e.g., 170",
                "required": False
            },
            {
                "name": "weight",
                "label": "Weight (kg)",
                "type": "number",
                "placeholder": "e.g., 70",
                "required": False
            },
            {
                "name": "age",
                "label": "Age",
                "type": "number",
                "placeholder": "e.g., 25",
                "required": False
            },
            {
                "name": "goal",
                "label": "Goal",
                "type": "select",
                "options": [
                    {"value": "weight_loss", "label": "Weight Loss"},
                    {"value": "muscle_gain", "label": "Muscle Gain"},
                    {"value": "maintenance", "label": "Maintenance"},
                    {"value": "general_health", "label": "General Health"}
                ],
                "required": False
            }
        ],
        "api_endpoint": "/api/diet-suggestion",
        "method": "POST"
    }
    
    return jsonify({
        "success": True,
        "data": form_structure
    }), 200 