from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    Response,
)

from dotenv import load_dotenv
from backend.core import GameInsightExtractor

load_dotenv()
app = Flask(__name__)
extractor = GameInsightExtractor()


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
