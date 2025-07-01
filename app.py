from flask import Flask, render_template, request, jsonify
from main import answer_question
import uuid
from chat_db import log_to_mysql
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Session-like storage (in-memory for simplicity)
user_data = {
    "user_id": str(uuid.uuid4()),
    "history": []
}

@app.route('/')
def index():
    return render_template('index.html', history=user_data['history'])

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form.get('query', '').strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400

    try:
        answer, sources = answer_question(query, user_id=user_data['user_id'])
        user_data['history'].append({
            "query": query,
            "answer": answer,
            "sources": sources
        })
        return jsonify({"query": query, "answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear():
    user_data['history'] = []
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    app.run(debug=True)