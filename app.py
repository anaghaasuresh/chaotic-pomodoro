"""
app.py

Flask routes only. All the chaos logic (message banks, delay math,
false-alarm scheduling) lives in timer_logic.py — this file just
reads requests, calls into it, and returns JSON.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from timer_logic import (
    generate_schedule,
    get_phone_roast,
    DEFAULT_DURATION_MINUTES,
)

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start_timer", methods=["POST"])
def start_timer():
    data = request.get_json(silent=True) or {}

    duration = data.get("duration", DEFAULT_DURATION_MINUTES)
    unit = data.get("unit", "minutes")
    reason = data.get("reason", "")

    schedule = generate_schedule(duration=duration, unit=unit, reason=reason)
    return jsonify(schedule)


@app.route("/api/phone_roast", methods=["GET"])
def phone_roast():
    return jsonify({"comment": get_phone_roast()})


if __name__ == "__main__":
    app.run(debug=True)