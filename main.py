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
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
        print(f"Message sent: {r.status_code}")
    except Exception as e:
        print(f"Message failed: {e}")

def scan_forbidden(start_id):
    print(f"Scanning from {start_id+1} to {start_id+31}...")
    for pid in range(start_id + 1, start_id + 31):
        if pid in known_ids or pid in known_forbidden:
            print(f"Skipping {pid} - already known")
            continue
        try:
            print(f"Checking {pid}...")
            response = requests.get(SINGLE_URL.format(pid), timeout=3)
            data = response.json()
            code = data.get("code", "")
            print(f"ID {pid}: status={response.status_code} code={code}")
            if response.status_code == 401 or code == "rest_forbidden":
                known_forbidden.add(pid)
                link = f"https://yg-life.com/archives/{pid}"
                send_message(f"🔒 LOCKED article found! Coming soon:\n\n{link}")
        except Exception as e:
            print(f"Error checking {pid}: {e}")

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
                if pid in known_forbidden:
                    known_forbidden.remove(pid)
    except Exception as e:
        print(f"Check error: {e}")

def get_scan_start():
    all_known = known_ids | known_forbidden
    if all_known:
        return max(all_known)
    return max(known_ids)

print("Loading existing posts...")
response = requests.get(API_URL)
posts = response.json()
for post in posts:
    known_ids.add(post["id"])
latest = max(known_ids)
print(f"Loaded {len(known_ids)} posts. Latest ID: {latest}")

send_message("✅ YG Life Monitor started! Scanning for locked articles...")
print("Startup scan beginning...")
scan_forbidden(latest)
print("Startup scan done!")
send_message("🔍 Startup scan complete. Monitoring every 2 minutes.")

while True:
    check()
    start = get_scan_start()
    scan_forbidden(start)
    time.sleep(120)
