import os
from flask import jsonify
import logging
from flask import render_template
from chat_logic import get_answer
from database import store_message, get_user_message

def getResponse(data):  
    user_message = data.get("message", "")
    user_id = data.get("user_id", "")
    bot_id = data.get("bot_id", "")
    
    store_message(user_id=user_id, role="user", content=user_message, source="web")
    bot_response = get_answer(user_message, user_id)
    store_message(user_id=user_id, role="assistant", content=bot_response, source="web")

    return jsonify({
        "message": "Message sent successfully",
        "reply": bot_response
    }), 200
    
    
def getMessages(data):
    logging.info(f"message: {data}")
    user_id = data.get("user_id", "")

    messages =  get_user_message(user_id)
    return jsonify({"message":"messages fetch successfully","data": messages}), 200

def webbot():
   return render_template("webbot.html", base_url=os.getenv("base_url"))
    

