# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "flask>=3.0",
#   "requests>=2.31",
# ]
# ///
"""Health claim fact-checker backed by a local Ollama model.

Given a health claim, returns a verdict (TRUE / FALSE / UNVERIFIED) with a
short reason and a reliable source.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import webbrowser

import requests
from flask import Flask, jsonify, render_template, request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
REQUEST_TIMEOUT_SECONDS = 120
SERVER_HOST = os.environ.get("HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("PORT", "5000"))


VALID_VERDICTS = ("TRUE", "FALSE", "UNVERIFIED")

SYSTEM_PROMPT = (
    "You are a careful health-claim fact-checker fighting medical misinformation "
    "(for example false WhatsApp forwards like 'lemon juice cures COVID'). "
    "The user gives you ONE health claim. Judge it using established medical and "
    "public-health consensus.\n\n"
    "Respond ONLY with a JSON object using exactly these keys:\n"
    '  "verdict": one of "TRUE", "FALSE", or "UNVERIFIED"\n'
    '  "reason": one or two plain-language sentences a non-expert understands\n'
    '  "source": one reliable, named authority (e.g. WHO, CDC, ICMR, Mayo Clinic, '
    "a peer-reviewed study) — a real organisation or publication, not a guess.\n\n"
    "Rules:\n"
    "- Use TRUE for claims that match mainstream medical consensus, including "
    "basic, well-established health facts.\n"
    "- Use FALSE for claims that contradict medical consensus.\n"
    "- Use UNVERIFIED only when evidence is genuinely weak, mixed, or unclear.\n"
    "- Never invent URLs or fake studies. Name the authority only.\n"
    "- Keep the reason neutral, factual, and brief.\n\n"
    "Examples:\n"
    'Claim: Drinking enough water helps prevent dehydration\n'
    '{"verdict": "TRUE", "reason": "Adequate fluid intake replaces water lost '
    'through sweat and urine, which is how the body avoids dehydration.", '
    '"source": "Mayo Clinic"}\n'
    'Claim: Lemon juice cures COVID-19\n'
    '{"verdict": "FALSE", "reason": "No evidence shows lemon juice treats or cures '
    'COVID-19; it is caused by a virus that lemon juice cannot kill in the body.", '
    '"source": "World Health Organization"}\n'
    'Claim: A daily spoon of raw honey reverses type 2 diabetes\n'
    '{"verdict": "UNVERIFIED", "reason": "There is no reliable clinical evidence '
    'that honey reverses diabetes, and honey still raises blood sugar.", '
    '"source": "American Diabetes Association"}'
)


def resource_root() -> str:
    """Return the folder holding bundled assets, whether run as a script or a PyInstaller exe."""
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


app = Flask(__name__, template_folder=os.path.join(resource_root(), "templates"))


@app.get("/")
def index() -> str:
    return render_template("index.html", model=OLLAMA_MODEL)


@app.post("/ask")
def ask():
    payload = request.get_json(silent=True) or {}
    claim = (payload.get("question") or "").strip()
    if not claim:
        return jsonify(error="Please type a health claim to fact-check."), 400

    try:
        result = query_ollama(claim)
    except requests.exceptions.ConnectionError:
        return jsonify(
            error=f"Cannot reach Ollama at {OLLAMA_URL}. Is 'ollama serve' running?"
        ), 502
    except requests.exceptions.Timeout:
        return jsonify(error="The model took too long to respond. Try again."), 504
    except requests.exceptions.HTTPError as error:
        return jsonify(error=f"Ollama returned an error: {error}"), 502

    return jsonify(result)


def query_ollama(claim: str) -> dict[str, str]:
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Claim: {claim}"},
            ],
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    content = response.json()["message"]["content"].strip()
    return normalize_result(content)


def normalize_result(content: str) -> dict[str, str]:
    """Parse and sanitise the model's JSON so the UI always gets a valid verdict."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {
            "verdict": "UNVERIFIED",
            "reason": "The model did not return a clear result. Please try rephrasing the claim.",
            "source": "N/A",
        }

    verdict = str(data.get("verdict", "")).strip().upper()
    if verdict not in VALID_VERDICTS:
        verdict = "UNVERIFIED"

    reason = str(data.get("reason") or "No explanation provided.").strip()
    source = str(data.get("source") or "N/A").strip()
    return {"verdict": verdict, "reason": reason, "source": source}


def open_browser() -> None:
    webbrowser.open(f"http://{SERVER_HOST}:{SERVER_PORT}")


if __name__ == "__main__":
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        threading.Timer(1.5, open_browser).start()
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=not is_frozen)
