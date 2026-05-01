import requests
import time
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
API_URL = "https://yg-life.com/wp-json/wp/v2/posts"

known_ids = set()

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def check():
    global known_ids
    try:
        response = requests.get(API_URL, timeout=10)
        posts = response.json()
        for post in posts:
            pid = post["id"]
            if pid not in known_ids:
                known_ids.add(pid)
                title = post["title"]["rendered"]
                link = f"https://yg-life.com/archives/{pid}"
                send_message(f"🔔 New YG article detected!\n\n{title}\n{link}")
    except Exception as e:
        print(f"Error: {e}")

print("Loading existing posts...")
response = requests.get(API_URL)
posts = response.json()
for post in posts:
    known_ids.add(post["id"])
print(f"Loaded {len(known_ids)} posts. Now monitoring...")

while True:
    check()
    time.sleep(120)
