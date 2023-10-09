from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from backend.core import GameInsightExtractor
from ingestion import get_summary
import re

load_dotenv()
app = Flask(__name__)
extractor = GameInsightExtractor()


@app.route("/ask-jenna-promts", methods=["POST"])
def ask_jenna_promts():
    text_snippet = request.json.get("text", "")
    response_list = extractor.get_prompts(text_snippet)
    return jsonify(generated_response=response_list)


@app.route("/ask-jenna-ideas", methods=["POST"])
def ask_jenna_ideas():
    text_snippet = request.json.get("text", "")
    generated_response = extractor.get_ideas(text_snippet)
    if len(generated_response) > 0:
        return jsonify(strategy=generated_response)
    return {}


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
def process_conversation():
    message = request.json.get("message", "")
    response_message = process_conversation_text(message)
    return jsonify(response_message=response_message)


def process_conversation_text(message):
    response_message = extractor.run_llm_chat(message)
    print(response_message)
    return response_message


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()  # or any other port you prefer
