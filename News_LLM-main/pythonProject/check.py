import requests

API_KEY = "AIzaSyBDhlBbx_mDP6OKlXYjnoIkOx0HFQeaRCI"
url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

response = requests.get(url)
if response.status_code == 200:
    models = response.json().get("models", [])
    print("✅ Available models:")
    for model in models:
        print(f"- {model['name']}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
