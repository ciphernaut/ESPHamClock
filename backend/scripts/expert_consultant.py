import requests
import json
import sys

def consult(prompt, model_id=None):
    url = "http://127.0.0.1:1234/v1/chat/completions"
    
    if not model_id:
        # Default to a large model if available
        models_resp = requests.get("http://127.0.0.1:1234/v1/models")
        models = models_resp.json().get("data", [])
        # Prefer qwen3-coder-30b or similar
        for m in models:
            if "30b" in m["id"] or "32b" in m["id"]:
                model_id = m["id"]
                break
        if not model_id:
            model_id = models[0]["id"]
            
    # print(f"Consulting {model_id}...")
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "You are a senior propagation physics expert and Python optimization consultant. Provide precise mathematical and code advice."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 expert_consultant.py \"your prompt here\" [model_id]")
    else:
        p = sys.argv[1]
        m = sys.argv[2] if len(sys.argv) > 2 else None
        print(consult(p, m))
