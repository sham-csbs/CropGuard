from flask import Flask, request, jsonify, send_from_directory
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="../frontend", static_url_path="")

LYZR_API_KEY = os.getenv("LYZR_API_KEY")
LYZR_USER_ID = os.getenv("LYZR_USER_ID")
LYZR_AGENT_ID = os.getenv("LYZR_AGENT_ID")

LYZR_URL = "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"

# Store latest ESP32 sensor data
latest_sensor_data = {
    "soil_moisture": 0,
    "temperature": 0,
    "humidity": 0
}


@app.route("/")
def home():
    return send_from_directory("../frontend", "index.html")


# ESP32 → Flask
@app.route("/api/sensor-data", methods=["POST"])
def sensor_data():

    data = request.get_json()

    latest_sensor_data["soil_moisture"] = data.get("soil_moisture", 0)
    latest_sensor_data["temperature"] = data.get("temperature", 0)
    latest_sensor_data["humidity"] = data.get("humidity", 0)

    print("ESP32 DATA:", latest_sensor_data)

    return jsonify({
        "ok": True,
        "message": "Sensor data received",
        "data": latest_sensor_data
    })


# Dashboard → Flask
@app.route("/api/sensor-data", methods=["GET"])
def get_sensor_data():

    return jsonify({
        "ok": True,
        "data": latest_sensor_data
    })


# Dashboard → Flask → Lyzr
@app.route("/api/crop-decision", methods=["POST"])
def crop_decision():

    data = request.get_json()

    soil = data.get(
        "soil_moisture",
        latest_sensor_data["soil_moisture"]
    )

    temperature = data.get(
        "temperature",
        latest_sensor_data["temperature"]
    )

    humidity = data.get(
        "humidity",
        latest_sensor_data["humidity"]
    )

    rainfall = data.get("rainfall_probability", 0)

    message = f"""
You are Crop Guard AI.

Current farm conditions:

Soil moisture: {soil}%
Temperature: {temperature}°C
Humidity: {humidity}%
Rainfall probability: {rainfall}%

Give a short farmer-friendly irrigation recommendation.

Tell:
1. Whether irrigation is needed
2. What action should be taken
3. The reason
"""

    payload = {
        "user_id": LYZR_USER_ID,
        "agent_id": LYZR_AGENT_ID,
        "session_id": "crop-guard-session",
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

        print("LYZR RESPONSE:", result)

        answer = (
            result.get("response")
            or result.get("message")
            or result.get("output")
            or result.get("result")
        )

        if not answer:
            answer = str(result)

        return jsonify({
            "ok": True,
            "recommendation": answer
        })

    except Exception as e:

        print("LYZR ERROR:", e)

        return jsonify({
            "ok": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
