import logging
# from flask import Flask, request, render_template_string, send_file, request,jsonify
from flask import Flask, request, jsonify

from controllers import chatController
from controllers import dietController
from database import  init_db
from flask_cors import CORS
import requests
from io import BytesIO

init_db()

# Initialize Flask App
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
    },
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }
})

# Set up logging
logging.basicConfig(level=logging.INFO)

# Remove the duplicate CORS headers - they're already handled by the CORS library
# @app.after_request
# def after_request(response):
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
#     response.headers.add('Access-Control-Allow-Credentials', 'true')
#     return response
    

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

# Diet Plan API Endpoints for Frontend Integration
@app.route("/api/diet-suggestion", methods=["POST"])
def diet_suggestion():
    data = request.get_json() or request.form.to_dict()
    return dietController.generate_diet_suggestion(data)

@app.route("/api/meal-suggestions", methods=["POST", "OPTIONS"])
def meal_suggestions():
    if request.method == "OPTIONS":
        return app.make_default_options_response()
    
    data = request.get_json() or request.form.to_dict()
    return dietController.generate_meal_suggestions(data)

@app.route("/api/diet-form-fields", methods=["GET"])
def diet_form_fields():
    return dietController.get_diet_form_fields()

@app.route("/api/test", methods=["GET", "POST", "OPTIONS"])
def test_endpoint():
    if request.method == "OPTIONS":
        return app.make_default_options_response()
    
    return jsonify({
        "success": True,
        "message": "Test endpoint working",
        "method": request.method,
        "headers": dict(request.headers)
    })

if __name__ == "__main__":
    
    # app.run(debug=True)  
    app.run(host='0.0.0.0', port=5000, debug=True)

