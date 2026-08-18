import urllib.request
import json
import urllib.error

import os

url = 'https://openrouter.ai/api/v1/chat/completions'
data = json.dumps({
    'model': 'google/gemini-2.0-flash-exp:free',
    'messages': [{'role': 'user', 'content': 'hi'}]
}).encode('utf-8')
headers = {
    'Authorization': f'Bearer {os.environ.get("LLM_API_KEY", "")}',
    'Content-Type': 'application/json',
    'HTTP-Referer': 'https://test.com'
}
req = urllib.request.Request(url, data=data, headers=headers)

try:
    response = urllib.request.urlopen(req)
    print("Success:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('Error code:', e.code)
    print('Error body:', e.read().decode('utf-8'))
