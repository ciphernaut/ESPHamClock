import requests
import json

try:
    # Try format=j1 for JSON
    resp = requests.get("https://wttr.in/World?format=j1", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print("wttr.in/World JSON successful")
        # Print a bit of it
        print(json.dumps(data.get('current_condition', [{}])[0], indent=2))
    else:
        print(f"wttr.in/World JSON failed: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")

try:
    # Try raw text
    resp = requests.get("https://wttr.in/World?format=%C+%t", timeout=10)
    print(f"wttr.in/World text: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
