from flask import Flask, request, jsonify, send_from_directory
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LYZR_API_KEY = os.getenv("LYZR_API_KEY")
LYZR_USER_ID = os.getenv("LYZR_USER_ID")
LYZR_AGENT_ID = os.getenv("LYZR_AGENT_ID")

LYZR_URL = "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/api/crop-decision", methods=["POST"])
def crop_decision():

    data = request.get_json()

    soil = data.get("soil_moisture")
    temperature = data.get("temperature")
    humidity = data.get("humidity")
    rainfall = data.get("rainfall_probability")

    message = f"""
You are Crop Guard AI.

Analyze these current farm conditions:

Soil moisture: {soil}%
Temperature: {temperature}°C
Humidity: {humidity}%
Rainfall probability: {rainfall}%

Give a simple irrigation recommendation.

Tell:
1. Whether irrigation is needed
2. Recommended action
3. Short reason

Keep the response short and farmer-friendly.
"""

    payload = {
        "user_id": LYZR_USER_ID,
        "agent_id": LYZR_AGENT_ID,
        "session_id": data.get("sessionId", "crop-guard-session"),
        "message": message
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": LYZR_API_KEY
    }

    try:
        response = requests.post(
            LYZR_URL,
            json=payload,
            headers=headers,
            timeout=25
        )

        result = response.json()

        # Try common response fields
        ai_response = (
            result.get("response")
            or result.get("message")
            or result.get("output")
            or result.get("result")
        )

        if isinstance(ai_response, dict):
            ai_response = str(ai_response)

        if not ai_response:
            ai_response = str(result)

        return jsonify({
            "ok": True,
            "recommendation": ai_response
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
