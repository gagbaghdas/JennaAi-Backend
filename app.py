from flask import Flask, request, jsonify, render_template, Response, session
from datetime import timedelta

from dotenv import load_dotenv
from backend.core import GameInsightExtractor
from db.db import db
from flask_cors import CORS
import os
import bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    create_refresh_token,
    get_jwt_identity,
)

from pymongo.errors import DuplicateKeyError


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=10)

jwt = JWTManager(app)

CORS(app)

extractor = GameInsightExtractor()


@app.route("/api/token/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": new_token}), 200


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()

    # Check if email already exists
    user = db.users.find_one({"email": data["email"]})
    if user:
        return jsonify({"success": False, "message": "Email already registered"}), 400

    hashed_password = hash_password(data["password"])

    new_user = {"email": data["email"], "password": hashed_password}

    try:
        result = db.users.insert_one(new_user)
        user_id_str = str(result.inserted_id)
        session["user_id"] = user_id_str
        access_token = create_access_token(identity=user_id_str)
        refresh_token = create_refresh_token(identity=user_id_str)
    except DuplicateKeyError:
        return jsonify({"success": False, "message": "Email already registered"}), 400

    return (
        jsonify(
            {
                "success": True,
                "token": access_token,
                "refresh_token": refresh_token,
                "message": "User registered successfully",
            }
        ),
        201,
    )


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    user = db.users.find_one({"email": data["email"]})

    if not user or not check_password(data["password"], user["password"]):
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    user_id_str = str(user["_id"])
    session["user_id"] = user_id_str

    access_token = create_access_token(identity=user_id_str)
    refresh_token = create_refresh_token(identity=user_id_str)

    return (
        jsonify(
            {
                "success": True,
                "token": access_token,
                "refresh_token": refresh_token,
                "message": "Login successful",
            }
        ),
        200,
    )


@app.route("/ask-jenna-promts", methods=["POST"])
@jwt_required()
def ask_jenna_promts():
    text_snippet = request.json.get("text", "")
    response_list = extractor.get_prompts(text_snippet)
    return jsonify(generated_response=response_list)


@app.route("/get-insights", methods=["POST"])
@jwt_required()
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
@jwt_required()
async def process_conversation():
    message = request.json.get("message", "")

    return Response(process_conversation_text(message), mimetype="text/plain")


def process_conversation_text(message):
    for chunk in extractor.run_llm_chat(message):
        yield chunk


def check_password(password: str, hashed: bytes) -> bool:
    # Compare the provided password against the hashed version
    return bcrypt.checkpw(password.encode("utf-8"), hashed)


def hash_password(password: str) -> bytes:
    # Generate a salt
    salt = bcrypt.gensalt()

    # Hash the password combined with the salt
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    return hashed


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(async_mode="threading")  # or any other port you prefer
