"""
AI flexibility layer — talks to a LOCAL Ollama model (free, runs on your machine).

STRICT RULE: this module NEVER invents a PI value, category, or fee. It only does two things:
  1. suggest_sector()  — messy user input -> best-guess real sector name from the database
                          (the actual answer still comes from pipeline.py's deterministic search)
  2. phrase_result()    — takes the CODE's already-computed result dict and writes a sentence
                          around it. It is given the numbers as fixed facts, not asked to recall them.

If Ollama isn't running, both functions fail gracefully and the app falls back to the
plain deterministic output — the AI layer is optional polish, never a dependency.
"""
import json

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


def _call_ollama(prompt: str, timeout: float = 25.0):
    if not _REQUESTS_AVAILABLE:
        return None
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception:
        return None  # Ollama not running / not installed / timed out — caller handles fallback


def suggest_sector(user_query: str, known_sector_names: list[str] = None) -> str | None:
    """Ask the model to turn a messy query into a short, clean industry/sector phrase
    (e.g. 'my bekery shop thing' -> 'bakery'). We do NOT ask the model to pick from a
    giant list — that's slow and brittle for a small local model. Instead this short
    phrase is handed back to the EXISTING, already-tested deterministic search — so the
    model's job is just "clean up the wording," and the real matching/accuracy still
    comes entirely from pipeline.py, not from the model."""
    prompt = f"""A user searching a business classification tool typed: "{user_query}"

This might be a typo, slang, or a roundabout description. Reply with ONLY a short
(1-4 word) plain description of the actual business/industry type they likely mean.
No explanation, no punctuation, just the short phrase. If it's unclear, reply: NONE
"""
    result = _call_ollama(prompt, timeout=25.0)
    if not result:
        return None
    result = result.strip().strip('."\'')
    if not result or result.upper() == "NONE" or len(result) > 60:
        return None
    return result


def phrase_result(result_dict: dict) -> str | None:
    """Turn an already-computed result into a plain-English sentence. The model is given
    the final numbers as facts to describe, not asked to produce them."""
    prompt = f"""Write ONE short, plain-English sentence summarizing this CPCB classification
result for a business owner. Do not add, change, or guess any numbers beyond what's given.
Do not mention anything not present in this data.

Data: {json.dumps(result_dict)}
"""
    return _call_ollama(prompt, timeout=6.0)
