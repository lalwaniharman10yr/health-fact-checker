# 🔎 Health Fact-Checker

A simple AI tool that fights fake health messages (like the ones that spread on
WhatsApp — *"lemon juice cures COVID"*). Type a health **claim** and it tells you
whether it is **TRUE**, **FALSE**, or **UNVERIFIED**, with a short reason and a
reliable source.

It runs **100% on your own computer** using a local AI model (via
[Ollama](https://ollama.com)) — no internet needed to answer, no cost, and your
questions stay private.

## What it looks like

- A text box where you paste a health claim
- A **Check** button
- A colour-coded verdict: 🟢 TRUE · 🔴 FALSE · 🟡 UNVERIFIED
- A plain-language **reason** and a named **source** (WHO, CDC, Mayo Clinic, …)

## The problem it solves

Fake health messages spread fast on WhatsApp in India, especially in tier-2
cities, and people believe them. This tool lets anyone quickly check a claim
before trusting or forwarding it.

## How it works

```
Your health claim  →  Web page (browser)  →  Flask app (app.py)  →  Local AI model (Ollama)
                                                                   ↓
                   Verdict + Reason + Source  ←───────────────────┘
```

## Run it yourself

**1. Install [Ollama](https://ollama.com/download)** and pull the model:

```bash
ollama pull llama3.2:3b
```

**2. Start the app** (needs [uv](https://docs.astral.sh/uv/) or Python 3.11+):

```bash
uv run app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Project files

| File | What it does |
|------|--------------|
| `app.py` | The backend — sends your claim to the local AI and returns the verdict |
| `templates/index.html` | The web page (text box, button, verdict display) |

## Settings (optional)

You can change these with environment variables:

| Variable | Default | Meaning |
|----------|---------|---------|
| `OLLAMA_MODEL` | `llama3.2:3b` | Which AI model to use |
| `OLLAMA_URL` | `http://localhost:11434` | Where Ollama is running |
| `PORT` | `5000` | Web page port |

## ⚠️ Disclaimer

This tool gives **general information only** and is **not** a substitute for
professional medical advice. For emergencies, contact your local emergency
services.
