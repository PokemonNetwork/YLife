import requests
import time
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
API_URL = "https://yg-life.com/wp-json/wp/v2/posts"
SINGLE_URL = "https://yg-life.com/wp-json/wp/v2/posts/{}"

known_ids = set()
known_forbidden = set()

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def scan_forbidden(start_id):
    found = []
    for pid in range(start_id + 1, start_id + 50):
        if pid in known_ids or pid in known_forbidden:
            continue
        try:
            response = requests.get(SINGLE_URL.format(pid), timeout=10)
            data = response.json()
            if response.status_code == 401 or (isinstance(data, dict) and data.get("code") == "rest_forbidden"):
                known_forbidden.add(pid)
                found.append(pid)
        except:
            pass
    return found

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
                send_message(f"🔔 New YG article is LIVE!\n\n{title}\n{link}")
    except Exception as e:
        print(f"Error: {e}")

print("Loading existing posts...")
response = requests.get(API_URL)
posts = response.json()
for post in posts:
    known_ids.add(post["id"])
latest = max(known_ids)
print(f"Loaded {len(known_ids)} posts. Latest ID: {latest}. Now monitoring...")

send_message("✅ YG Life Monitor started! Scanning for locked articles now...")

# Scan immediately on startup and report findings
print("Scanning for locked articles...")
forbidden_found = scan_forbidden(latest)
if forbidden_found:
    msg = f"🔒 Found {len(forbidden_found)} locked upcoming article(s):\n\n"
    for pid in forbidden_found:
        msg += f"https://yg-life.com/archives/{pid}\n"
    msg += "\nThese exist but are not public yet!"
    send_message(msg)
else:
    send_message("🔍 No locked articles found right now. Will keep scanning every 2 minutes.")

while True:
    check()
    if known_ids:
        latest = max(known_ids)
        forbidden_found = scan_forbidden(latest)
        for pid in forbidden_found:
            link = f"https://yg-life.com/archives/{pid}"
            send_message(f"🔒 LOCKED article found! Coming soon:\n\n{link}\n\nWill notify you when it goes live!")
    time.sleep(120)
