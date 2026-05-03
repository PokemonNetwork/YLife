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
    for pid in range(start_id + 1, start_id + 31):
        if pid in known_ids or pid in known_forbidden:
            continue
        try:
            response = requests.get(SINGLE_URL.format(pid), timeout=10)
            data = response.json()
            if response.status_code == 401 or (isinstance(data, dict) and data.get("code") == "rest_forbidden"):
                known_forbidden.add(pid)
                link = f"https://yg-life.com/archives/{pid}"
                send_message(f"🔒 LOCKED article found! Coming soon:\n\n{link}")
                print(f"Found locked article: {pid}")
        except:
            pass

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
                    send_message(f"✅ Previously locked article is now LIVE:\n{link}")
    except Exception as e:
        print(f"Error: {e}")

def get_scan_start():
    # Always scan from latest known ID
    # But also re-check known_forbidden ones in case they went live
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
print(f"Loaded {len(known_ids)} posts. Latest ID: {latest}. Now monitoring...")

send_message("✅ YG Life Monitor started! Scanning for locked articles now...")

print("Scanning for locked articles on startup...")
scan_forbidden(latest)
print("Startup scan complete. Now monitoring every 2 minutes...")
send_message("🔍 Startup scan complete. Monitoring every 2 minutes.")

while True:
    check()
    start = get_scan_start()
    scan_forbidden(start)
    time.sleep(120)
