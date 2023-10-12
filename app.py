from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    Response,
    session
)

from dotenv import load_dotenv
from backend.core import GameInsightExtractor
from db import db
from db.models.user_model import User

load_dotenv()
app = Flask(__name__)
extractor = GameInsightExtractor()

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()

    # Check if email already exists
    user = User.query.filter_by(email=data['email']).first()
    if user:
        return jsonify({"success": False, "message": "Email already registered"}), 400

    # Create new user and set password
    new_user = User(email=data['email'])
    new_user.set_password(data['password'])
    
    # Add user to database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"success": True, "message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    # Store user ID in session for user authentication
    session['user_id'] = user.id

    return jsonify({"success": True, "message": "Login successful"}), 200

@app.route("/ask-jenna-promts", methods=["POST"])
def ask_jenna_promts():
    text_snippet = request.json.get("text", "")
    response_list = extractor.get_prompts(text_snippet)
    return jsonify(generated_response=response_list)


@app.route("/get-insights", methods=["POST"])
def get_insights():
    text_snippet = request.json.get("text", "")
    insight_data = request.json.get("insightData", "")
    if len(text_snippet) == 0:
        return {}
    generated_insight = extractor.get_marketing_insight(text_snippet, insight_data)
    if len(generated_insight) > 0:
        return jsonify(generated_insight=generated_insight)
    return {}


@app.route("/process-conversation", methods=["POST"])
async def process_conversation():
    message = request.json.get("message", "")

    return Response(process_conversation_text(message), mimetype="text/plain")


def process_conversation_text(message):
    for chunk in extractor.run_llm_chat(message):
        yield chunk


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(async_mode="threading")  # or any other port you prefer
