# 🚗 Car History Content Agent

A minimal AI agent powered by **Google Gemini** that:
1. Researches car history topics using **DuckDuckGo** (no API key needed)
2. Writes punchy 60–90 second video scripts (~150–200 words)
3. Saves them to the `scripts/` folder automatically

---

## Setup

### 1. Install dependencies
```bash
pip install google-genai ddgs
```

### 2. Get a FREE Gemini API key

**https://aistudio.google.com/apikey** → Sign in with Google → *Create API Key*

It's completely free (generous rate limits on Gemini 2.5 Flash).

### 3. Set the API key

**Windows PowerShell (temporary — current session only):**
```powershell
$env:GEMINI_API_KEY = "AIzaSy..."
python agent.py "Ford Mustang evolution"
```

**Windows PowerShell (permanent — survives restarts):**
```powershell
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "AIzaSy...", "User")
```

**Or create a `.env` file** in the same folder as `agent.py`:
```
GEMINI_API_KEY=AIzaSy...
```

---

## Usage

```bash
python agent.py "Toyota Corolla evolution"
python agent.py "Ford Mustang evolution"
python agent.py "Porsche 911 history"
python agent.py "Honda Civic vs Corolla rivalry"
```

---

## What you'll see

```
============================================================
  🚗  Car History Content Agent  (Gemini)
  Topic: Toyota Corolla evolution
============================================================

── Agent turn 1 ─────────────────────────────────────
   finish_reason: FunctionCall
🔍 Searching: Toyota Corolla history milestones
   ✅  Got 5 result(s).

── Agent turn 2 ─────────────────────────────────────
   finish_reason: FunctionCall
✍️  Drafting script complete — saving now...
💾 Saved to scripts/toyota_corolla_evolution.txt

── Agent turn 3 ─────────────────────────────────────
   finish_reason: STOP
🤖 Gemini: Script saved!
✅  Agent finished.
============================================================
  Run complete.
============================================================
```

---

## Output

Scripts are saved to `scripts/<topic>.txt` in the same folder.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: google.genai` | `pip install google-genai` |
| `ModuleNotFoundError: ddgs` | `pip install ddgs` |
| `❌ GEMINI_API_KEY not set` | Set the env var or create `.env` file |
| Rate limit / quota error | Wait 60 seconds and retry (free tier limit) |
