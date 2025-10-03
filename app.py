import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyC_Y6vS46ILkzbjcrUZe39woI8BhWzxGRU")
genai.configure(api_key=API_KEY)

# --- LOAD DATA FROM outfits.json ---
try:
    with open("outfits.json", "r") as f:
        OUTFITS = json.load(f).get("outfits", [])
except FileNotFoundError:
    print("🔴 outfits.json not found. Exiting.")
    exit()

# --- ROUTES ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/recommend", methods=["POST"])
def recommend():
    if not request.json:
        return jsonify({"error": "No JSON body"}), 400

    data = request.json
    event = data.get("event", "casual")
    gender = data.get("gender", "male")
    budget = data.get("budget", "mid-range")
    style = data.get("style", "classic")

    try:
        # --- AI Prompt ---
        prompt = f"""
        Act as a top Indian fashion stylist. Create a unique outfit suggestion.
        Event: {event}
        Gender: {gender}
        Budget: {budget}
        Style: {style}

        Return ONLY valid JSON with keys:
        - look_title: short creative name
        - description: 2-3 engaging sentences
        - clothing_keywords: list of 2-4 keywords
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "")

        try:
            ai_recommendation = json.loads(cleaned)
        except json.JSONDecodeError:
            ai_recommendation = {
                "look_title": "Default Outfit",
                "description": "A stylish fallback look.",
                "clothing_keywords": []
            }

        # --- Match items from outfits.json ---
        matched = None
        for outfit in OUTFITS:
            if (outfit["gender"].lower() == gender.lower() and
                event.lower() in outfit["event"].lower() and
                budget.lower() in outfit["budget"].lower() and
                style.lower() in outfit.get("style", "").lower()):
                matched = outfit
                break

        if matched:
            ai_recommendation["links"] = matched.get("links", [])
        else:
            ai_recommendation["links"] = []

        return jsonify(ai_recommendation)

    except Exception as e:
        print(f"❗️ Server Error: {e}")
        return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
