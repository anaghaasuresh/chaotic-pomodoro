from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# --- Sarcastic comment banks ---
EARLY_COMMENTS = [
    "Wow, done already? Bold of you to assume you deserve a break.",
    "That was fast. Suspiciously fast. Are you even trying?",
    "Early alert! Your productivity has been... questioned.",
    "Cutting it short, huh? The grind called, it's disappointed.",
]

LATE_COMMENTS = [
    "Relax, nothing bad happens if you study extra.",
    "Oh, you're STILL going? Overachiever detected. Gross.",
    "The timer forgot about you. Honestly, so did we.",
    "Bonus time! Unpaid, unasked for, and non-negotiable.",
]

ONTIME_COMMENTS = [
    "Wait, it actually worked? Don't get used to it.",
    "On time. Suspicious. We'll do better next time.",
]

PHONE_ROASTS = [
    "Put. The phone. Down. It's not going anywhere, unlike your focus.",
    "Oh look, someone remembered their phone exists.",
    "Checking your phone mid-session? Bold strategy.",
    "Your focus session and your phone are now in a toxic relationship.",
]

def get_chaos_delay(requested_minutes, activity):
    """
    Decide the REAL delay (in seconds) for the alert, distorted from
    what the user requested. Different activities get different chaos
    tendencies just for flavor.
    """
    requested_seconds = requested_minutes * 60

    # Chaos mode: early, late, or (rarely) honest
    roll = random.random()

    if activity.lower() in ["study", "work"]:
        # These get punished more — long delays are funnier
        if roll < 0.15:
            multiplier = random.uniform(0.4, 0.8)   # early
        elif roll < 0.85:
            multiplier = random.uniform(1.3, 2.5)   # late, sometimes very late
        else:
            multiplier = 1.0                         # on time (rare mercy)
    else:
        # Cooking/exercise/other — still chaotic but slightly less cruel
        if roll < 0.3:
            multiplier = random.uniform(0.5, 0.9)
        elif roll < 0.8:
            multiplier = random.uniform(1.1, 1.8)
        else:
            multiplier = 1.0

    real_seconds = max(5, int(requested_seconds * multiplier))
    return real_seconds, multiplier


def get_comment(multiplier):
    if multiplier < 0.95:
        return random.choice(EARLY_COMMENTS)
    elif multiplier > 1.05:
        return random.choice(LATE_COMMENTS)
    else:
        return random.choice(ONTIME_COMMENTS)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start_timer", methods=["POST"])
def start_timer():
    data = request.get_json()
    requested_minutes = data.get("minutes", 25)
    activity = data.get("activity", "study")

    real_seconds, multiplier = get_chaos_delay(requested_minutes, activity)
    comment = get_comment(multiplier)

    return jsonify({
        "requested_minutes": requested_minutes,
        "real_seconds": real_seconds,
        "comment": comment
    })


@app.route("/api/phone_roast", methods=["GET"])
def phone_roast():
    return jsonify({"comment": random.choice(PHONE_ROASTS)})


if __name__ == "__main__":
    app.run(debug=True)