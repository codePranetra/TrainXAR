import logging
from flask import Flask, request, render_template_string, send_file, request,jsonify
from controllers import chatController
from database import  init_db
from flask_cors import CORS
import requests
from io import BytesIO

init_db()

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
    

@app.route("/", methods=["GET"])
def webbot():
    return chatController.webbot()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.form.to_dict()
    return chatController.getResponse(data)

@app.route("/get-messages", methods=["GET"])
def get_messages():
    data = request.args
    return chatController.getMessages(data)

if __name__ == "__main__":
    
    # app.run(debug=True)  
    app.run(host='0.0.0.0', port=5000, debug=True)
