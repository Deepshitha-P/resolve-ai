import urllib.request
import json
import os

api_key = os.environ.get("GEMINI_API_KEY", "")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        print("Success! Available models:")
        for model in data.get('models', []):
            name = model.get('name', '')
            if 'gemini' in name.lower():
                print(f"  - {name}")
except Exception as e:
    print(f"Error calling API: {e}")
