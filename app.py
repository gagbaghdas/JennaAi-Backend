from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from backend.core import get_prompts, get_ideas, get_best_insight
from ingestion import get_summary
import re

load_dotenv()
app = Flask(__name__)


@app.route("/ask-jenna-promts", methods=["POST"])
def ask_jenna_promts():
    text_snippet = request.json.get("text", "")
    response_list = get_prompts(text_snippet)
    return jsonify(generated_response=response_list)


@app.route("/ask-jenna-ideas", methods=["POST"])
def ask_jenna_ideas():
    text_snippet = request.json.get("text", "")
    generated_response = get_ideas(text_snippet)
    if len(generated_response) > 0:
        return jsonify(strategy=generated_response)
    return {}


@app.route("/get-insights", methods=["POST"])
def get_insights():
    text_snippet = request.json.get("text", "")
    insight_data = request.json.get("insightData", "")
    if len(text_snippet) == 0:
        return {}
    generated_insight = get_best_insight(text_snippet, insight_data)
    if len(generated_insight) > 0:
        return jsonify(generated_insight=generated_insight)
    return {}


@app.route("/process-conversation", methods=["POST"])
def process_conversation():
    conversation = request.json.get("conversation", "")
    # Process the conversation and generate a response
    response_message = process_conversation_text(conversation)
    return jsonify(response_message=response_message)


def process_conversation_text(conversation_text):
    # Implement your processing logic here
    response_message = "Jenna's response to the entire conversation."
    return response_message


@app.route("/")
def index():
    summary = get_summary()
    print(summary)
    return render_template("index.html", summary=summary)


if __name__ == "__main__":
    app.run(host="192.168.0.131", port=5000)  # or any other port you prefer
