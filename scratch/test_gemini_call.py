import urllib.request
import urllib.error
import json
import os

api_key = os.environ.get("GEMINI_API_KEY", "")

models_to_test = [
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite"
]

for model in models_to_test:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "Hello, write a 3 word response."}]}]}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"Success with {model}!")
            print("  Response:", data["candidates"][0]["content"]["parts"][0]["text"].strip())
            break
    except urllib.error.HTTPError as e:
        print(f"HTTPError with {model}: {e.code} - {e.reason}")
        try:
            print("  Details:", e.read().decode("utf-8").strip())
        except Exception:
            pass
    except Exception as e:
        print(f"Error with {model}:", e)
