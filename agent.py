"""
Car History Content Agent  (Google Gemini edition)
===================================================
A minimal AI agent using Google Gemini (gemini-2.5-flash) to research
car history topics and generate short-form video scripts
(60-90 seconds spoken, ~150-200 words).

API:   Google AI (via google-genai SDK)
Model: gemini-2.5-flash

Usage:
    python -X utf8 agent.py "Ford Mustang evolution"

Environment variables required:
    GEMINI_API_KEY  — get one free at https://aistudio.google.com/apikey
                      or put it in a .env file next to this script

Web search is powered by DuckDuckGo (no API key required).
"""

import os
import sys
import json
from pathlib import Path

# ── Force UTF-8 output so emojis work on Windows cp1252 terminals ─────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Load .env file if present ─────────────────────────────────────────────────
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("❌  'google-genai' package not found. Run:  pip install google-genai")

_DDGS = None
try:
    from ddgs import DDGS as _DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS as _DDGS
    except ImportError:
        pass

if _DDGS is None:
    print(
        "⚠️  No DuckDuckGo search package found. Web search will return stub results.\n"
        "   Install with:  pip install ddgs\n"
    )

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL              = "gemini-3.5-flash"
SCRIPTS_DIR        = Path("scripts")
MAX_SEARCH_RESULTS = 5

SYSTEM_PROMPT = (
    "You are a scriptwriter for short-form car history videos (60-90 seconds spoken, ~150-200 words). "
    "Research using web_search before writing — search at least once, more if you need specific facts or dates. "
    "Use get_car_specs to pull exact engine, horsepower, 0-60, and price figures for a specific model year when the script needs precise numbers. "
    "Use get_car_images after researching to fetch relevant high-quality car photos for visual assets. "
    "Keep tone punchy and factual, no fluff intro. "
    "IMPORTANT: You MUST call save_script to save the finalized script with a clear filename based on the topic."
)

# ── Tool implementations ───────────────────────────────────────────────────────

def web_search(query: str) -> str:
    """Search the web using DuckDuckGo and return formatted top results."""
    print(f"🔍 Searching: {query}")

    if _DDGS is None:
        stub = (
            f"[STUB — no DuckDuckGo package installed]\n"
            f"Query: {query}\n"
            "Install with:  pip install ddgs"
        )
        print("   ⚠️  Returning stub result.")
        return stub

    try:
        results = []
        with _DDGS() as ddgs:
            for r in ddgs.text(query, max_results=MAX_SEARCH_RESULTS):
                title = r.get("title", "No title")
                body  = r.get("body", "")
                href  = r.get("href", "")
                results.append(f"Title: {title}\nURL: {href}\nSnippet: {body}\n")

        if not results:
            return f"No results found for: {query}"

        print(f"   ✅  Got {len(results)} result(s).")
        return "\n---\n".join(results)

    except Exception as exc:
        msg = f"Search error: {exc}"
        print(f"   ❌  {msg}")
        return msg


def save_script(filename: str, content: str) -> str:
    """Save the finalized script to the scripts/ folder as a .txt file."""
    safe_name = filename.strip().replace(" ", "_")
    if not safe_name.endswith(".txt"):
        safe_name += ".txt"

    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = SCRIPTS_DIR / safe_name
    filepath.write_text(content, encoding="utf-8")
    print(f"💾 Saved to {filepath}")
    return f"Script saved successfully to '{filepath}'."


# Realistic stub data keyed by "Make Model Year" or just "Model Year"
_SPECS_DB: dict[str, dict] = {
    # Nissan GT-R
    "nissan gt-r 2009":  {"engine": "3.8L twin-turbo V6 (VR38DETT)", "horsepower": 480,  "0_60_mph": "3.5s", "msrp_usd": 69_850},
    "nissan gt-r 2012":  {"engine": "3.8L twin-turbo V6 (VR38DETT)", "horsepower": 530,  "0_60_mph": "2.9s", "msrp_usd": 89_900},
    "nissan gt-r 2017":  {"engine": "3.8L twin-turbo V6 (VR38DETT)", "horsepower": 565,  "0_60_mph": "2.7s", "msrp_usd": 101_585},
    "nissan gt-r 2020":  {"engine": "3.8L twin-turbo V6 (VR38DETT)", "horsepower": 565,  "0_60_mph": "2.7s", "msrp_usd": 113_540},
    # Mazda MX-5
    "mazda mx-5 1989":  {"engine": "1.6L DOHC inline-4",            "horsepower": 116,  "0_60_mph": "8.6s", "msrp_usd": 13_800},
    "mazda mx-5 2015":  {"engine": "2.0L SKYACTIV-G inline-4",      "horsepower": 155,  "0_60_mph": "5.9s", "msrp_usd": 24_915},
    # Ford Mustang
    "ford mustang 1964": {"engine": "4.7L (289ci) V8",               "horsepower": 271,  "0_60_mph": "7.5s", "msrp_usd": 2_368},
    "ford mustang 2015": {"engine": "5.0L Coyote V8",                "horsepower": 435,  "0_60_mph": "4.3s", "msrp_usd": 32_925},
    # Toyota Corolla
    "toyota corolla 1966": {"engine": "1.1L inline-4 (K engine)",    "horsepower": 60,   "0_60_mph": "18.0s","msrp_usd": 1_733},
    "toyota corolla 2023": {"engine": "2.0L Dynamic Force inline-4", "horsepower": 169,  "0_60_mph": "7.7s", "msrp_usd": 22_050},
}


def get_car_specs(model_year: str) -> str:
    """
    Return a dict of specs (engine, hp, 0-60, price) for a given car model and year.
    model_year should be a string like 'Nissan GT-R 2009' or 'Ford Mustang 1964'.
    Returns a JSON-formatted string.
    """
    key = model_year.strip().lower()
    print(f"📋 Getting specs: {model_year}")

    specs = _SPECS_DB.get(key)

    if specs is None:
        # Fuzzy fallback: find the closest year for a known model
        for db_key, db_specs in _SPECS_DB.items():
            # Match if all words of the model name appear in the key
            words = key.split()
            if len(words) >= 2 and all(w in db_key for w in words[:-1]):  # ignore year word
                specs = dict(db_specs)
                specs["_note"] = f"Exact year not found; showing data for '{db_key}'."
                break

    if specs is None:
        specs = {
            "_note": f"No spec data available for '{model_year}'. Using generic placeholder.",
            "engine": "N/A",
            "horsepower": "N/A",
            "0_60_mph": "N/A",
            "msrp_usd": "N/A",
        }

    result = json.dumps(specs, indent=2)
    print(f"   ✅  Specs returned for '{model_year}'.")
    return result


def get_car_images(query: str) -> str:
    """
    Fetch 3-4 car photos from Unsplash API for the query.
    Returns a JSON string of a list of objects containing 'url', 'photographer', and 'photographer_url'.
    """
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    fallback_images = [
        {
            "url": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1080&q=80",
            "photographer": "Unsplash Car Showcase",
            "photographer_url": "https://unsplash.com/s/photos/car"
        }
    ]

    if not key:
        print("   ⚠️  UNSPLASH_ACCESS_KEY not set. Returning fallback Unsplash image.")
        return json.dumps(fallback_images, indent=2)

    print(f"🖼️  Fetching images from Unsplash for: {query}")
    try:
        import requests
        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {key}"}
        params = {"query": query, "per_page": 4, "orientation": "landscape"}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            error_msg = f"Unsplash API HTTP {resp.status_code}"
            print(f"   ⚠️  {error_msg}. Using fallback image.")
            return json.dumps(fallback_images, indent=2)

        data = resp.json()
        results = data.get("results", [])
        images = []
        for item in results[:4]:
            img_url = item.get("urls", {}).get("regular", "")
            user = item.get("user", {})
            photographer = user.get("name", "Unknown Photographer")
            photographer_url = user.get("links", {}).get("html", "https://unsplash.com")
            if img_url:
                images.append({
                    "url":              img_url,
                    "photographer":     photographer,
                    "photographer_url": photographer_url
                })

        if not images:
            images = fallback_images

        print(f"   ✅  Got {len(images)} image(s) from Unsplash.")
        return json.dumps(images, indent=2)

    except Exception as exc:
        print(f"   ⚠️  Failed to fetch images from Unsplash: {exc}. Using fallback image.")
        return json.dumps(fallback_images, indent=2)


# ── Tool dispatcher ───────────────────────────────────────────────────────────

TOOL_FUNCTIONS = {
    "web_search":     web_search,
    "save_script":    save_script,
    "get_car_specs":  get_car_specs,
    "get_car_images": get_car_images,
}


def execute_tool(name: str, args: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        result = fn(**args)
        return result if isinstance(result, str) else json.dumps(result)
    except Exception as exc:
        return f"Tool '{name}' raised an error: {exc}"


# ── Gemini tool schema (function declarations) ────────────────────────────────

GEMINI_TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="web_search",
            description=(
                "Search the web for information about a topic and return the top results as text. "
                "Use this to gather facts, dates, and details before writing a script."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="The search query string.",
                    )
                },
                required=["query"],
            ),
        ),
        types.FunctionDeclaration(
            name="save_script",
            description=(
                "Save the finalized script to the scripts/ folder as a .txt file. "
                "Use a descriptive snake_case filename based on the topic."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "filename": types.Schema(
                        type=types.Type.STRING,
                        description="Snake_case filename without extension, e.g. 'mazda_mx5_history'.",
                    ),
                    "content": types.Schema(
                        type=types.Type.STRING,
                        description="The full text of the finalized script.",
                    ),
                },
                required=["filename", "content"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_car_specs",
            description=(
                "Return engine, horsepower, 0-60 mph time, and MSRP price for a specific car model and year. "
                "Call this when you need precise technical figures to make the script more factual. "
                "Pass model_year as a string like 'Nissan GT-R 2009' or 'Ford Mustang 1964'."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "model_year": types.Schema(
                        type=types.Type.STRING,
                        description="Car model and year, e.g. 'Nissan GT-R 2009' or 'Mazda MX-5 1989'.",
                    )
                },
                required=["model_year"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_car_images",
            description=(
                "Fetch 3-4 real car photos from Unsplash matching the car or topic. "
                "Call this after research to retrieve visual assets for video production. "
                "Pass query as a clear search string like 'Mazda RX-7' or '1993 Mazda RX-7 FD'."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Search query for car photos, e.g., 'Mazda RX-7' or 'Nissan GT-R'.",
                    )
                },
                required=["query"],
            ),
        ),
    ]
)

GENERATE_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=[GEMINI_TOOLS],
    temperature=0.7,
)


# ── Agent loop ────────────────────────────────────────────────────────────────

def run_agent(topic: str) -> dict:
    """
    Run the full agent loop for the given topic.
    Returns: {"script": str, "wordCount": int, "filename": str}
    Raises ValueError if GEMINI_API_KEY is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not set. "
            "Get a free key at https://aistudio.google.com/apikey and add it to .env."
        )

    client = genai.Client(api_key=api_key)

    print(f"\n{'='*60}")
    print(f"  🚗  Car History Content Agent  (Gemini)")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

    # Build conversation history as a list of Content objects
    contents: list[types.Content] = [
        types.Content(
            role="user",
            parts=[types.Part(text=f"Write a short-form car history video script about: {topic}")]
        )
    ]

    # Captures the save_script call and get_car_images call for the return value
    _saved: dict = {"script": "", "filename": "", "images": []}
    _last_text: list[str] = []

    iteration = 0

    while True:
        iteration += 1
        print(f"── Agent turn {iteration} ─────────────────────────────────────")

        response = None
        for attempt in range(5):
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=GENERATE_CONFIG,
                )
                break
            except Exception as exc:
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    print(f"   ⏳ Hit rate limit (429). Waiting 15s before retry... (Attempt {attempt+1}/5)")
                    import time
                    time.sleep(15)
                else:
                    raise exc

        if response is None:
            print("❌ Failed to get response after retries.")
            break

        # ── Inspect the response candidate ────────────────────────────────────
        candidate = response.candidates[0] if response.candidates else None
        if candidate is None:
            print("⚠️  No candidates returned. Exiting.")
            break

        finish_reason = candidate.finish_reason
        print(f"   finish_reason: {finish_reason}")

        # Separate function_call parts from text parts
        all_parts  = candidate.content.parts if candidate.content else []
        fc_parts   = [p for p in all_parts if p.function_call]
        text_parts = [p.text for p in all_parts if p.text]

        # Print raw function_call objects so you can see genuine Gemini tool-calling
        if fc_parts:
            print(f"\n   🔧 Raw function_call part(s) from Gemini:")
            for p in fc_parts:
                fc = p.function_call
                print(f"      name : {fc.name}")
                print(f"      args : {dict(fc.args)}")

        # Collect model text output safely using response.text or text_parts
        turn_text = ""
        if hasattr(response, "text") and response.text:
            turn_text = response.text.strip()
        elif text_parts:
            turn_text = "\n".join(text_parts).strip()

        if turn_text:
            print(f"\n🤖 Gemini:\n{turn_text}\n")
            _last_text.append(turn_text)

        # ── No function calls → model is done ─────────────────────────────────
        if not fc_parts:
            print("\n✅  Agent finished. Final response printed above.")
            break

        # ── Execute each function call ─────────────────────────────────────────
        # Append candidate.content directly for the model turn
        contents.append(candidate.content)

        # Build one user Content containing all function_response parts
        response_parts = []
        for p in fc_parts:
            fc      = p.function_call
            fn_name = fc.name
            fn_args = dict(fc.args)

            if fn_name == "save_script":
                print("✍️  Drafting script complete — saving now...")
                # Capture content + filename for the return value
                _saved["script"]   = fn_args.get("content", "")
                _saved["filename"] = fn_args.get("filename", "")
            elif fn_name == "get_car_specs":
                print(f"📋 Fetching specs: {fn_args.get('model_year', '?')}")
            elif fn_name == "get_car_images":
                print(f"🖼️  Fetching images: {fn_args.get('query', '?')}")

            result_str = execute_tool(fn_name, fn_args)

            if fn_name == "get_car_images":
                try:
                    parsed_imgs = json.loads(result_str)
                    if isinstance(parsed_imgs, list):
                        _saved["images"] = parsed_imgs
                except Exception:
                    pass

            response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fn_name,
                        response={"result": result_str},
                    )
                )
            )

        # Send all function results back in a single user turn
        contents.append(
            types.Content(role="user", parts=response_parts)
        )

    print(f"\n{'='*60}")
    print("  Run complete.")
    print(f"{'='*60}\n")

    script = _saved["script"]
    if not script:
        script = "\n\n".join(_last_text).strip()
    if not script:
        script = (
            f"The history of {topic} is a story of automotive passion, engineering innovation, and iconic design. "
            f"From its debut to its modern legacy, the {topic} remains an legendary milestone in car history."
        )

    filename = _saved["filename"] or topic.strip().lower().replace(" ", "_")
    images   = _saved.get("images", [])

    return {
        "script":    script,
        "wordCount": len(script.split()),
        "filename":  filename,
        "images":    images,
    }


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -X utf8 agent.py \"<topic>\"")
        print('Example: python -X utf8 agent.py "Ford Mustang evolution"')
        sys.exit(1)

    try:
        result = run_agent(" ".join(sys.argv[1:]))
        print(f"Script word count : {result['wordCount']}")
        print(f"Saved as          : {result['filename']}.txt")
    except ValueError as e:
        sys.exit(f"❌  {e}")
