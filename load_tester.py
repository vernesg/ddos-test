import requests
import threading
import time
import random
import csv
from datetime import datetime

# ========== CONFIGURATION ==========
TARGET_URL = "https://your-site.com/api"  # <-- Change this to your target
HTTP_METHOD = "POST"  # GET or POST
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android; Mobile)",
    "Authorization": "Bearer YOUR_TOKEN_HERE",  # Optional
}
POST_DATA = {"key": "value"}  # JSON/form data for POST
USE_JSON = True  # Set to False for form-encoded data
THREADS = 10
REQUESTS_PER_THREAD = 20
DELAY = 0  # Delay (sec) between each request per thread
PROXY_FILE = "proxies.txt"
LOG_FILE = "results.csv"
# ===================================

success_count = 0
fail_count = 0
lock = threading.Lock()

# Show VERN logo
def show_logo():
    logo = r"""
 __     ______  ____   _   _ 
 \ \   / / __ \|  _ \ | \ | |
  \ \_/ / |  | | |_) ||  \| |
   \   /| |  | |  _ < | . ` |
    | | | |__| | |_) || |\  |
    |_|  \____/|____/ |_| \_|
            Load Tester - VERN
    """
    print(logo)

# Load proxies
def load_proxies():
    try:
        with open(PROXY_FILE, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
            return proxies
    except FileNotFoundError:
        print(f"[!] Proxy file '{PROXY_FILE}' not found.")
        return []

proxies = load_proxies()

def get_proxy_dict(proxy):
    return {"http": proxy, "https": proxy}

# Send a single request
def send_request(session, proxy=None):
    global success_count, fail_count
    try:
        if HTTP_METHOD == "POST":
            if USE_JSON:
                resp = session.post(TARGET_URL, headers=HEADERS, json=POST_DATA, proxies=proxy, timeout=10)
            else:
                resp = session.post(TARGET_URL, headers=HEADERS, data=POST_DATA, proxies=proxy, timeout=10)
        else:
            resp = session.get(TARGET_URL, headers=HEADERS, proxies=proxy, timeout=10)

        with lock:
            if resp.status_code == 200:
                success_count += 1
            else:
                fail_count += 1
            log_result(resp.status_code, proxy)
            print(f"[{threading.current_thread().name}] Status: {resp.status_code}")
    except Exception as e:
        with lock:
            fail_count += 1
            log_result("ERROR", proxy)
            print(f"[{threading.current_thread().name}] Request failed: {e}")

def log_result(status, proxy_used):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), status, proxy_used])

# Worker thread
def worker():
    session = requests.Session()
    for _ in range(REQUESTS_PER_THREAD):
        proxy = get_proxy_dict(random.choice(proxies)) if proxies else None
        send_request(session, proxy)
        if DELAY > 0:
            time.sleep(DELAY)

# Main runner
def run_test():
    global success_count, fail_count
    show_logo()
    print(f"\n[+] Starting test: {THREADS} threads × {REQUESTS_PER_THREAD} requests")
    print(f"[+] Target: {TARGET_URL}\n")

    # Clear log
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Status", "Proxy"])

    start = time.time()
    threads = []

    for i in range(THREADS):
        t = threading.Thread(target=worker, name=f"Thread-{i+1}")
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    duration = time.time() - start
    print("\n[✓] Test completed!")
    print(f"Total: {THREADS * REQUESTS_PER_THREAD} requests")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Duration: {duration:.2f} sec")
    print(f"Requests/sec: {(success_count + fail_count) / duration:.2f}")

if __name__ == "__main__":
    run_test()
