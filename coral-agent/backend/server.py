"""
Flask API Server for First Mate Agent
Run: python server.py
Serves the frontend and handles API calls.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import fetch_github_data, ask_agent, demo_with_mock_data, SYSTEM_PROMPT
from anthropic import Anthropic

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

client = Anthropic()

# In-memory session storage (for demo purposes)
sessions = {}

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/fetch', methods=['POST'])
def fetch_data():
    """Fetch GitHub data via Coral SQL."""
    body = request.json
    mode = body.get('mode', 'demo')
    
    if mode == 'demo':
        data = demo_with_mock_data()
        session_id = 'demo'
    else:
        github_username = body.get('github_username', '')
        repo_owner = body.get('repo_owner', '')
        repo = body.get('repo', '')
        
        if not all([github_username, repo_owner, repo]):
            return jsonify({"error": "Missing required fields"}), 400
        
        data = fetch_github_data(github_username, repo_owner, repo)
        session_id = f"{repo_owner}/{repo}"
    
    # Store in session
    sessions[session_id] = {
        "data": data,
        "conversation": []
    }
    
    # Get initial summary
    conversation = []
    initial_reply = ask_agent(
        data,
        "What should I focus on today? Give me a complete summary with top priorities.",
        conversation
    )
    
    sessions[session_id]["conversation"] = conversation
    
    # Build summary of what was fetched
    fetched_summary = []
    for key, result in data.items():
        if result["success"]:
            try:
                items = json.loads(result["data"])
                fetched_summary.append(f"{key}: {len(items)} items")
            except:
                fetched_summary.append(f"{key}: fetched")
        else:
            fetched_summary.append(f"{key}: error - {result.get('error', 'unknown')}")
    
    return jsonify({
        "session_id": session_id,
        "fetched": fetched_summary,
        "summary": initial_reply
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle follow-up questions."""
    body = request.json
    session_id = body.get('session_id', 'demo')
    message = body.get('message', '')
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found. Please fetch data first."}), 404
    
    reply = ask_agent(session["data"], message, session["conversation"])
    
    return jsonify({"reply": reply})

@app.route('/api/raw', methods=['POST'])
def get_raw_data():
    """Get raw SQL data for display."""
    body = request.json
    session_id = body.get('session_id', 'demo')
    
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    raw = {}
    for key, result in session["data"].items():
        if result["success"] and result["data"]:
            try:
                raw[key] = json.loads(result["data"])
            except:
                raw[key] = result["data"]
        else:
            raw[key] = {"error": result.get("error", "No data")}
    
    return jsonify(raw)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🏴‍☠️  First Mate Server starting on http://localhost:{port}\n")
    app.run(debug=True, port=port)
