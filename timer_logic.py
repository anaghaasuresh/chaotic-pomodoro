"""
timer_logic.py

The "chaos brain" of the Useless Pomodoro Timer.

Responsibility: given a duration + unit + reason, produce a full
"schedule" up front — a real (distorted) fire time, a few false alarms
along the way, and the sarcastic messages to go with each. Also holds
the phone-roast message bank so all the "personality" of the app lives
in one place instead of being scattered across routes.

Nothing here talks to a network or a frontend. It's pure logic so it
can be tested in isolation before/after wiring up the Flask routes.
"""

import random


# ---------------------------------------------------------------------------
# 1. Reason detection
# ---------------------------------------------------------------------------
# The user just types a reason ("study", "cook rice", "gym later") instead
# of picking from a dropdown. We match keywords to figure out which flavor
# of chaos to serve. Falls back to "generic" if nothing matches.

REASON_KEYWORDS = {
    "study": ["study", "studying", "exam", "homework", "assignment", "revise", "revision"],
    "cooking": ["cook", "cooking", "rice", "food", "kitchen", "bake", "baking", "boil"],
    "work": ["work", "working", "office", "meeting", "deadline", "project", "code", "coding"],
    "exercise": ["gym", "workout", "exercise", "run", "running", "yoga", "stretch"],
    "sleep": ["nap", "sleep", "sleeping", "rest"],
}


def detect_category(reason: str) -> str:
    """Map a free-text reason to one of our joke categories."""
    reason_lower = (reason or "").lower()
    for category, keywords in REASON_KEYWORDS.items():
        if any(keyword in reason_lower for keyword in keywords):
            return category
    return "generic"


# ---------------------------------------------------------------------------
# 2. Message banks
# ---------------------------------------------------------------------------
# Per-category banks drive the FALSE alarms (the fake mid-timer scares) and
# the LATE real-alarm message (the normal case, since the timer is late
# almost all the time). EARLY and ON-TIME are rare enough that they don't
# need per-category flavor — a shared bank covers them, same as your
# original app.py had.

MESSAGE_BANK = {
    "study": {
        "false_alarms": [
            "🚨 POP QUIZ! Just kidding... or am I?",
            "Your brain has officially left the chat.",
            "Alert: you've been staring at the same line for 10 minutes.",
        ],
        "reveals": [
            "Ooh, false alarm. My bad. Keep studying I guess.",
            "Relax, that wasn't real. Unlike your upcoming exam.",
        ],
        "late_alarms": [
            "Time's up! Well, technically it was up a while ago.",
            "Congrats, you 'studied'. Results may vary.",
        ],
    },
    "cooking": {
        "false_alarms": [
            "🔥 Ooh, your rice has been overcooked!!",
            "Something's burning. Probably. Maybe. Check it.",
            "The smoke alarm called, it wants a word.",
        ],
        "reveals": [
            "Kidding! It's fine. Probably.",
            "False alarm, chef. Your food is (likely) safe.",
        ],
        "late_alarms": [
            "Okay THIS time it's real. Go check your food.",
            "Timer's actually done. Hope dinner survived the wait.",
        ],
    },
    "work": {
        "false_alarms": [
            "Your manager is typing...",
            "New meeting invite: 'Quick Sync' (2 hours).",
            "Slack notification: someone said 'per my last message'.",
        ],
        "reveals": [
            "Relax, nobody's typing anything. Back to it.",
            "False alarm. No meeting. You're safe. For now.",
        ],
        "late_alarms": [
            "Break time! Eventually. Now, technically.",
            "Timer's done. Whether your work is done is a separate issue.",
        ],
    },
    "exercise": {
        "false_alarms": [
            "Your legs just filed a formal complaint.",
            "Warning: gains may not be loading as expected.",
            "Is that a cramp or just regret?",
        ],
        "reveals": [
            "Kidding. You're built different (allegedly).",
            "False alarm. Keep going, champ.",
        ],
        "late_alarms": [
            "Alright, actually done now. Go hydrate.",
            "Timer's really over this time. Stretch or regret it.",
        ],
    },
    "sleep": {
        "false_alarms": [
            "Rise and shine! ...oh wait, too early. Go back to sleep.",
            "Is that your alarm or just a dream about an alarm?",
        ],
        "reveals": [
            "False alarm. Keep sleeping, you earned it.",
            "Relax, still nap time.",
        ],
        "late_alarms": [
            "Okay, for real now, wake up.",
            "Nap's actually over. Yes, actually.",
        ],
    },
    "generic": {
        "false_alarms": [
            "🚨 Something happened. Probably.",
            "This is definitely a real alarm. Trust me.",
            "Beep beep. Or is it?",
        ],
        "reveals": [
            "Ooh, false alarm. My bad.",
            "Relax, that one didn't count.",
        ],
        "late_alarms": [
            "Okay, this one's real. We promise. Mostly.",
            "Timer's done. Only slightly later than you asked for.",
        ],
    },
}

# Shared across all categories — early/on-time are rare "easter egg" cases,
# so they get flavor-neutral lines rather than a full bank per category.
EARLY_COMMENTS = [
    "Wow, done already? Bold of you to assume you deserve a break.",
    "That was fast. Suspiciously fast. Are you even trying?",
    "Early alert! Your productivity has been... questioned.",
    "Cutting it short, huh? The grind called, it's disappointed.",
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


def get_message(category: str, kind: str) -> str:
    """Grab a random line from a category's message bank."""
    bank = MESSAGE_BANK.get(category, MESSAGE_BANK["generic"])
    return random.choice(bank[kind])


def get_phone_roast() -> str:
    return random.choice(PHONE_ROASTS)


# ---------------------------------------------------------------------------
# 3. Duration normalization
# ---------------------------------------------------------------------------

DEFAULT_DURATION_MINUTES = 25


def normalize_to_seconds(duration: float, unit: str) -> int:
    """Convert a user-given duration + unit into whole seconds."""
    unit = (unit or "minutes").lower()
    if unit in ("second", "seconds", "sec", "s"):
        return max(1, int(duration))
    return max(1, int(duration * 60))


# ---------------------------------------------------------------------------
# 4. Real fire time — mostly late, rarely early (easter egg), almost never
#    exactly on time
# ---------------------------------------------------------------------------

EARLY_EASTER_EGG_PROBABILITY = 0.08   # ~8% of the time, fires early instead
ONTIME_MERCY_PROBABILITY = 0.03       # ~3% of the time, fires bang on time

MIN_LATE_EXTRA_RATIO = 0.15
MAX_LATE_EXTRA_RATIO = 0.90

MIN_EARLY_MULTIPLIER = 0.40
MAX_EARLY_MULTIPLIER = 0.85


def compute_real_fire_seconds(requested_seconds: int):
    """
    Decide when the timer ACTUALLY goes off.

    Returns (real_fire_seconds, mode) where mode is one of
    "early", "ontime", or "late" — used to pick the right comment bank.
    """
    roll = random.random()

    if roll < EARLY_EASTER_EGG_PROBABILITY:
        multiplier = random.uniform(MIN_EARLY_MULTIPLIER, MAX_EARLY_MULTIPLIER)
        return max(3, int(requested_seconds * multiplier)), "early"

    if roll < EARLY_EASTER_EGG_PROBABILITY + ONTIME_MERCY_PROBABILITY:
        return requested_seconds, "ontime"

    extra_ratio = random.uniform(MIN_LATE_EXTRA_RATIO, MAX_LATE_EXTRA_RATIO)
    extra_seconds = max(3, int(requested_seconds * extra_ratio))
    return requested_seconds + extra_seconds, "late"


def get_real_alarm_message(category: str, mode: str) -> str:
    if mode == "early":
        return random.choice(EARLY_COMMENTS)
    if mode == "ontime":
        return random.choice(ONTIME_COMMENTS)
    return get_message(category, "late_alarms")


# ---------------------------------------------------------------------------
# 5. Schedule generation — the actual chaos, assembled
# ---------------------------------------------------------------------------

def generate_schedule(duration: float = DEFAULT_DURATION_MINUTES,
                       unit: str = "minutes",
                       reason: str = "") -> dict:
    """
    Build the full chaotic schedule for one timer run.

    Returns a dict with:
      - requested_seconds: what the user actually asked for
      - real_fire_seconds: when the timer will ACTUALLY go off
      - mode: "early" | "ontime" | "late"
      - category: detected reason category (useful for frontend theming)
      - false_alarms: list of {offset_seconds, message, reveal_delay_seconds, reveal_message}
      - real_alarm: {message}
    """
    requested_seconds = normalize_to_seconds(duration, unit)
    category = detect_category(reason)

    real_fire_seconds, mode = compute_real_fire_seconds(requested_seconds)

    # False alarms are scattered before the real fire time regardless of
    # early/ontime/late mode — the window just shrinks if the real fire
    # time itself is short.
    num_false_alarms = random.randint(1, 3)
    window_start = max(2, int(real_fire_seconds * 0.05))
    window_end = max(window_start + 1, int(real_fire_seconds * 0.95))

    offsets = sorted(random.sample(
        range(window_start, window_end),
        k=min(num_false_alarms, max(1, window_end - window_start))
    ))

    false_alarms = []
    for offset in offsets:
        false_alarms.append({
            "offset_seconds": offset,
            "message": get_message(category, "false_alarms"),
            "reveal_delay_seconds": random.randint(2, 3),
            "reveal_message": get_message(category, "reveals"),
        })

    real_alarm = {
        "message": get_real_alarm_message(category, mode),
    }

    return {
        "requested_seconds": requested_seconds,
        "real_fire_seconds": real_fire_seconds,
        "mode": mode,
        "category": category,
        "false_alarms": false_alarms,
        "real_alarm": real_alarm,
    }


if __name__ == "__main__":
    import json
    # Run a few times to see early/ontime/late variety
    for _ in range(5):
        schedule = generate_schedule(duration=30, unit="minutes", reason="study for exam")
        print(json.dumps(schedule, indent=2))
        print("---")