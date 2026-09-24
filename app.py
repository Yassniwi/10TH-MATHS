import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import MODEL_NAME, SYSTEM_PROMPT, WELCOME_MESSAGE

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing. Add it to the .env file.")

client = genai.Client(api_key=api_key)

generation_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    temperature=0.4,
    max_output_tokens=1024,
)

MAX_HISTORY = 20
MAX_MESSAGE_LENGTH = 1000


def build_contents(history, message):
    """Convert the chat history from the browser into Gemini's format."""
    contents = []
    for item in history[-MAX_HISTORY:]:
        role = "user" if item.get("role") == "user" else "model"
        text = str(item.get("text", "")).strip()
        if text:
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=text)])
            )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=message)])
    )
    return contents


@app.route("/")
def home():
    return render_template("index.html", welcome=WELCOME_MESSAGE)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please type a message."}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": "Message is too long."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, message),
            config=generation_config,
        )
        reply = (response.text or "").strip() or "Sorry, I could not generate an answer."
        return jsonify({"reply": reply})
    except Exception as error:
        app.logger.error("Gemini API error: %s", error)
        return jsonify({"error": "Something went wrong. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
