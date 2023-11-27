from flask import Flask, request, jsonify, render_template, Response, session, url_for
from datetime import timedelta
from flask_jwt_extended import decode_token

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
from bson import ObjectId


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
        access_token = create_access_token(identity=user_id_str)
        refresh_token = create_refresh_token(identity=user_id_str)
    except DuplicateKeyError:
        return jsonify({"success": False, "message": "Email already registered"}), 400

    return (
        jsonify(
            {
                "success": True,
                "access_token": access_token,
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
        return jsonify({"success": False, "message": "Invalid email or password"}), 403

    user_id_str = str(user["_id"])

    access_token = create_access_token(identity=user_id_str)
    refresh_token = create_refresh_token(identity=user_id_str)

    return (
        jsonify(
            {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "message": "Login successful",
            }
        ),
        200,
    )


@app.route("/api/ask-jenna-promts", methods=["POST"])
@jwt_required()
def ask_jenna_promts():
    text_snippet = request.json.get("text", "")
    response_list = extractor.get_prompts(text_snippet)
    return jsonify(generated_response=response_list)


@app.route("/api/create_project", methods=["POST"])
@jwt_required()
def create_project():
    project_name = request.form.get("project_name")
    brief = request.form.get("brief")
    template_id = request.form.get("template_id")
    brief_file = request.files.get("briefFile")
    template_file = request.files.get("templateFile")

    # Validate required fields
    if (
        not project_name
        or not (brief or brief_file)
        or not (template_id or template_file)
    ):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    user_id = get_jwt_identity() 

    # Prepare document to be inserted into MongoDB
    new_project = {
        "user_id": user_id,
        "project_name": project_name,
        "brief": brief,
        "template_id": template_id,
        "brief_file_path": f"uploads/{brief_file.filename}" if brief_file else None,
        "template_file_path": f"uploads/{template_file.filename}"
        if template_file
        else None,
    }

    try:
        # Insert the new project document into MongoDB
        result = db.projects.insert_one(new_project)
        project_id_str = str(result.inserted_id)

         # Determine the directories
        brief_dir = f"user_projects/{user_id}/{project_id_str}/brief"
        template_dir = f"user_projects/{user_id}/{project_id_str}/template"

        # Create directories if they don't exist
        os.makedirs(brief_dir, exist_ok=True)
        os.makedirs(template_dir, exist_ok=True)

        # Save files to the directories
        if brief_file:
            brief_file.save(os.path.join(brief_dir, brief_file.filename))
        if template_file:
            template_file.save(os.path.join(template_dir, template_file.filename))
    except Exception as e:
        # Handle any exceptions that occur
        return jsonify({"success": False, "message": str(e)}), 500

    return (
        jsonify(
            {
                "success": True,
                "project_id": project_id_str,
                "message": "Project created successfully",
            }
        ),
        201,
    )

@app.route("/api/get_projects", methods=["GET"])
@jwt_required()
def get_projects():
    user_id = get_jwt_identity()

    projects_cursor = db.projects.find({"user_id": user_id})
    
    # Convert the projects to a list and then to JSON
    projects_list = list(projects_cursor)
    for project in projects_list:
        project["_id"] = str(project["_id"])

    return jsonify(projects_list), 200

@app.route("/api/delete_project/<project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    user_id = get_jwt_identity()

    try:
        # Delete the project if it belongs to the logged-in user
        result = db.projects.delete_one({"_id": ObjectId(project_id), "user_id": user_id})

        if result.deleted_count == 0:
            return jsonify({"success": False, "message": "Project not found or unauthorized"}), 404

        return jsonify({"success": True, "message": "Project deleted successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/get_project/<project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    user_id = get_jwt_identity()

    try:
        project = db.projects.find_one({"_id": ObjectId(project_id), "user_id": user_id})

        if not project:
            return jsonify({"success": False, "message": "Project not found"}), 404

        # Convert the project ID to a string for JSON serialization
        project["_id"] = str(project["_id"])

        # Optionally, format or modify the response data as needed
        return jsonify(project), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/update_project/<project_id>", methods=["PUT"])
@jwt_required()
def update_project(project_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    try:
        result = db.projects.update_one(
            {"_id": ObjectId(project_id), "user_id": user_id},
            {"$set": {
                "project_name": data["project_name"],
                "brief": data["brief"],
                "template_id": data["template_id"]
                # Add other fields as necessary
            }}
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Project not found or unauthorized"}), 404

        return jsonify({"success": True, "message": "Project updated successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/templates", methods=["GET"])
def get_templates():
    try:
        templates_cursor = db.templates.find({})
        templates_list = list(templates_cursor)

        for template in templates_list:
            template["_id"] = str(template["_id"])
            template["image"] = request.url_root + url_for('static', filename=template["image"]).lstrip('/')

        return jsonify(templates_list), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500



@app.route("/api/get-insights", methods=["POST"])
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


@app.route("/api/process-conversation", methods=["POST"])
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


if __name__ == "__main__":
    app.run(async_mode="threading")  # or any other port you prefer
