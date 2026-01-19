import os
import time
import requests
import datetime

# --- CONFIG ---
LOG_FILE = "../risk-dashboard/public/agent_logs.txt"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
THRESHOLD_SECONDS = 300 # 5 minutes

def send_alert(message):
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN":
        print(f"I would alert: {message}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, json=data)
    except Exception as e:
        print(f"Failed to send alert: {e}")

def check_health():
    print(f"[{datetime.datetime.now()}] Checking agent health...")
    
    if not os.path.exists(LOG_FILE):
        send_alert(f"🚨 CRITICAL: Log file not found at {LOG_FILE}. Is the agent running?")
        return

    # Check last modification time
    mtime = os.path.getmtime(LOG_FILE)
    now = time.time()
    diff = now - mtime
    
    if diff > THRESHOLD_SECONDS:
        send_alert(f"⚠️ WARNING: Agent stuck! Last log update was {int(diff)} seconds ago.")
    else:
        print(f"✅ Agent Healthy. Last active: {int(diff)}s ago.")

if __name__ == "__main__":
    # In a real deployed scenario, this might run as a cron job or a loop.
    # For now, let's run it once.
    check_health()
