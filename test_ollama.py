"""
Standalone Ollama connectivity test — run this BEFORE testing the full app.
Usage: python3 test_ollama.py
"""
import time

try:
    import requests
except ImportError:
    print("❌ 'requests' package not installed. Run: pip install requests --break-system-packages")
    exit(1)

URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

print(f"Testing connection to Ollama at {URL} using model '{MODEL}'...")
print("(First call can take 10-30 seconds while the model loads into memory — this is normal.)")

start = time.time()
try:
    resp = requests.post(
        URL,
        json={"model": MODEL, "prompt": "Reply with exactly one word: OK", "stream": False},
        timeout=60,
    )
    elapsed = time.time() - start
    resp.raise_for_status()
    data = resp.json()
    print(f"\n✅ SUCCESS in {elapsed:.1f}s")
    print(f"Model replied: {data.get('response', '').strip()!r}")
except requests.exceptions.ConnectionError:
    print(f"\n❌ CONNECTION FAILED after {time.time()-start:.1f}s")
    print("Ollama isn't reachable on port 11434. Run 'ollama ps' in another terminal to check")
    print("if it's running. If empty, run 'ollama run llama3.2' once to wake it up, then retry.")
except requests.exceptions.Timeout:
    print(f"\n❌ TIMED OUT after {time.time()-start:.1f}s")
    print("Ollama is reachable but didn't respond in time. Your machine may be slow to load")
    print("the model on CPU. Try running 'ollama run llama3.2' manually first to pre-load it,")
    print("then run this test again — it should be fast on the second call.")
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
