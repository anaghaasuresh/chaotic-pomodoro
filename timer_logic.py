"""
timer_logic.py

The "chaos brain" of the Useless Pomodoro Timer.

Core rule of this version: the timer NEVER actually completes. It
always gives up ("abandons") at some point before the requested
duration — even if that duration is 30 seconds. False alarms are
guaranteed to fire along the way too, scaled to fit short timers.

Nothing here talks to a network or a frontend. It's pure logic so it
can be tested in isolation before/after wiring up the Flask routes.
"""

import random


# ---------------------------------------------------------------------------
# 1. Reason detection
# ---------------------------------------------------------------------------

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
# "false_alarms": the scary/urgent-sounding fake alert shown mid-timer
# "reveals": shown a couple seconds later, admitting the false alarm was fake
# "abandon_alarms": shown when the app gives up on the timer entirely,
#   always before the requested duration is reached

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
        "abandon_alarms": [
            "I got bored watching you study. You count the rest.",
            "Timer's dead. Blame me, not your discipline (jk, blame you).",
            "Supervision terminated early. Your exam is still real though.",
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
        "abandon_alarms": [
            "Lost interest at cook-o'clock. You're on timer duty now.",
            "I got bored watching your rice cook. Go check it yourself.",
            "Kitchen supervision ended early. Good luck out there, chef.",
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
        "abandon_alarms": [
            "This meeting simulation is over. I have other things to fake.",
            "I'm clocking out early. You should probably keep working though.",
            "Timer quit before you did. Feels ironic somehow.",
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
        "abandon_alarms": [
            "I got tired watching you get tired. We're done here, early.",
            "Officially bored of your reps. Finish counting yourself.",
            "Timer tapped out before your muscles did. Awkward.",
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
        "abandon_alarms": [
            "Got bored watching you nap. Wake up, or don't, not my problem.",
            "Nap supervision terminated due to boredom. Carry on.",
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
        "abandon_alarms": [
            "Yeah, I'm bored now. You count the rest.",
            "This is now your problem. Bye.",
            "I quit. Figure out the remaining time yourself.",
        ],
    },
}

# Shared "oops" reveal lines mixed in with every category's own reveals,
# so the false-alarm reveal always has a chance to land on this exact vibe.
GENERIC_OOPSIE_REVEALS = [
    "Ooppsie, false alarm! My bad.",
    "Ooppsie! Totally made that one up.",
    "Oops, false alarm. Carry on like nothing happened.",
]

PHONE_ROASTS = [
    "Put. The phone. Down. It's not going anywhere, unlike your focus.",
    "Oh look, someone remembered their phone exists.",
    "Checking your phone mid-session? Bold strategy.",
    "Your focus session and your phone are now in a toxic relationship.",
]


def get_message(category: str, kind: str) -> str:
    """Grab a random line from a category's message bank.

    For 'reveals', mixes in the shared GENERIC_OOPSIE_REVEALS pool so
    the 'ooppsie' style always has a chance to show up regardless of
    category.
    """
    bank = MESSAGE_BANK.get(category, MESSAGE_BANK["generic"])
    if kind == "reveals":
        pool = bank["reveals"] + GENERIC_OOPSIE_REVEALS
    else:
        pool = bank[kind]
    return random.choice(pool)


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
# 4. Abandon point — the timer ALWAYS quits before the requested duration,
#    no matter how short that duration is.
# ---------------------------------------------------------------------------

ABANDON_MIN_RATIO = 0.35   # earliest the app can give up: 35% of the way in
ABANDON_MAX_RATIO = 0.85   # latest the app can give up: 85% of the way in


def compute_abandon_seconds(requested_seconds: int) -> int:
    """
    Decide when the app gives up — always strictly before the requested
    duration, scaled proportionally so short timers (even 30s) still
    abandon partway through instead of running to completion.
    """
    ratio = random.uniform(ABANDON_MIN_RATIO, ABANDON_MAX_RATIO)
    abandon_seconds = int(requested_seconds * ratio)
    # Clamp: at least 1 second in, and always at least 1 second short
    # of the requested duration so it never looks like a real finish.
    abandon_seconds = max(1, min(abandon_seconds, requested_seconds - 1))
    return abandon_seconds


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
      - real_fire_seconds: when the app actually gives up (always
        strictly less than requested_seconds)
      - mode: always "abandoned" in this version
      - category: detected reason category (useful for frontend theming)
      - false_alarms: list of {offset_seconds, message, reveal_delay_seconds, reveal_message}
      - real_alarm: {message} — the "giving up" message
    """
    requested_seconds = normalize_to_seconds(duration, unit)
    category = detect_category(reason)

    abandon_seconds = compute_abandon_seconds(requested_seconds)

    # False alarms are guaranteed (at least 1), scaled down for short
    # timers so they don't get crammed into a tiny window.
    if requested_seconds < 90:
        num_false_alarms = 1
    else:
        num_false_alarms = random.randint(1, 3)

    window_start = max(1, int(abandon_seconds * 0.15))
    window_end = max(window_start + 1, abandon_seconds)

    offsets = sorted(random.sample(
        range(window_start, window_end),
        k=min(num_false_alarms, max(1, window_end - window_start))
    ))

    false_alarms = []
    for offset in offsets:
        # Keep the reveal delay short enough that it lands before the
        # app abandons, so the reveal always actually gets seen.
        remaining_before_abandon = max(1, abandon_seconds - offset)
        reveal_delay = random.randint(1, min(3, remaining_before_abandon))
        false_alarms.append({
            "offset_seconds": offset,
            "message": get_message(category, "false_alarms"),
            "reveal_delay_seconds": reveal_delay,
            "reveal_message": get_message(category, "reveals"),
        })

    real_alarm = {
        "message": get_message(category, "abandon_alarms"),
    }

    return {
        "requested_seconds": requested_seconds,
        "real_fire_seconds": abandon_seconds,
        "mode": "abandoned",
        "category": category,
        "false_alarms": false_alarms,
        "real_alarm": real_alarm,
    }


if __name__ == "__main__":
    import json
    # Sanity check across a range of durations, including very short ones
    for duration, unit, reason in [
        (30, "seconds", "study"),
        (1, "minutes", "cooking rice"),
        (5, "minutes", "gym"),
        (30, "minutes", "work meeting"),
    ]:
        schedule = generate_schedule(duration=duration, unit=unit, reason=reason)
        print(f"--- duration={duration} {unit}, reason={reason!r} ---")
        print(json.dumps(schedule, indent=2))
        assert schedule["real_fire_seconds"] < schedule["requested_seconds"], "abandoned late!"
        assert len(schedule["false_alarms"]) >= 1, "no false alarm!"
    print("\nAll sanity checks passed: always abandons early, always >=1 false alarm.")