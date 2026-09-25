from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

LYZR_API_KEY = os.getenv("LYZR_API_KEY")
LYZR_USER_ID = os.getenv("LYZR_USER_ID")
LYZR_AGENT_ID = os.getenv("LYZR_AGENT_ID")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LYZR_URL = "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"

# =========================================================
# LATEST SENSOR DATA
# =========================================================

latest_sensor_data = {
    "soil_moisture": 0,
    "temperature": 0,
    "humidity": 0,
    "motion": False,
    "pump": False,
    "servo": False,
    "buzzer": False
}

# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "ok": True,
        "service": "Crop Guard Backend",
        "status": "online"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "status": "healthy"
    })


# =========================================================
# TELEGRAM
# =========================================================

def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not configured.")
        return False

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        print("Telegram response:", response.status_code)

        return response.ok

    except Exception as e:

        print("Telegram error:", e)

        return False


# =========================================================
# ESP32 → FLASK
# =========================================================

@app.route("/api/sensor-data", methods=["POST"])
def sensor_data():

    data = request.get_json(silent=True) or {}

    latest_sensor_data["soil_moisture"] = float(
        data.get("soil_moisture", 0)
    )

    latest_sensor_data["temperature"] = float(
        data.get("temperature", 0)
    )

    latest_sensor_data["humidity"] = float(
        data.get("humidity", 0)
    )

    latest_sensor_data["motion"] = bool(
        data.get("motion", False)
    )

    latest_sensor_data["pump"] = bool(
        data.get("pump", False)
    )

    latest_sensor_data["servo"] = bool(
        data.get("servo", False)
    )

    latest_sensor_data["buzzer"] = bool(
        data.get("buzzer", False)
    )

    print("\n========== ESP32 DATA ==========")
    print(latest_sensor_data)
    print("================================")

    # -----------------------------------------------------
    # FARMER ALERTS
    # -----------------------------------------------------

    soil = latest_sensor_data["soil_moisture"]
    motion = latest_sensor_data["motion"]

    if soil <= 30:

        send_telegram(
            "🚨 CROP GUARD ALERT\n\n"
            f"Soil moisture is critically low: {soil:.0f}%\n"
            "Emergency irrigation may be required."
        )

    elif soil <= 50:

        send_telegram(
            "🌱 CROP GUARD ALERT\n\n"
            f"Soil moisture: {soil:.0f}%\n"
            "Please monitor the field and prepare for irrigation."
        )

    if motion:

        send_telegram(
            "🚨 CROP PROTECTION ALERT\n\n"
            "Movement detected near the field perimeter.\n"
            "Buzzer and servo protection activated."
        )

    return jsonify({
        "ok": True,
        "message": "Sensor data received",
        "data": latest_sensor_data
    })


# =========================================================
# DASHBOARD → FLASK
# =========================================================

@app.route("/api/sensor-data", methods=["GET"])
def get_sensor_data():

    return jsonify({
        "ok": True,
        "data": latest_sensor_data
    })


# =========================================================
# DASHBOARD → FLASK → LYZR AI
# =========================================================

@app.route("/api/crop-decision", methods=["POST"])
def crop_decision():

    data = request.get_json(silent=True) or {}

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

    rainfall = data.get(
        "rainfall_probability",
        0
    )

    motion = data.get(
        "motion",
        latest_sensor_data["motion"]
    )

    message = f"""
You are Crop Guard AI.

Analyze the following real-time farm conditions.

Soil moisture: {soil}%
Temperature: {temperature}°C
Humidity: {humidity}%
Rainfall probability: {rainfall}%
PIR movement detected: {motion}

Give a short farmer-friendly recommendation.

Your response must contain:

1. Irrigation status
2. Recommended action
3. Reason
4. Weather consideration
5. Crop protection status if movement is detected

Important irrigation logic:

- Above 60%: soil is sufficiently moist.
- 50–60%: notify farmer and recommend monitoring/manual irrigation.
- 30–50%: continue monitoring.
- 20–30%: critical dryness.
- At critical dryness, irrigation can be activated if suitable rain is NOT expected.
- If rain is expected soon, recommend waiting instead of unnecessary irrigation.

Do not claim that threshold rules themselves are machine learning.
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

    if not LYZR_API_KEY:
        return jsonify({
            "ok": False,
            "message": "LYZR_API_KEY is not configured."
        }), 500

    try:

        response = requests.post(
            LYZR_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        print("Lyzr status:", response.status_code)

        result = response.json()

        print("LYZR RESPONSE:")
        print(result)

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


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=False
    )
