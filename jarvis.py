import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

MODEL = os.environ.get("JARVIS_MODEL", "openai/gpt-4o-mini")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

HOME = Path.home()
TASK_FILE = HOME / ".jarvis" / "tasks.json"
TASK_FILE.parent.mkdir(parents=True, exist_ok=True)

CONTACTS = {
    "mom": "",
    "dad": "",
    "brother": "",
    "sister": "",
}

APPS = {
    "youtube": "com.google.android.youtube",
    "whatsapp": "com.whatsapp",
    "chrome": "com.android.chrome",
    "facebook": "com.facebook.katana",
    "instagram": "com.instagram.android",
    "gmail": "com.google.android.gm",
}

FORBIDDEN_PATTERNS = [
    "factory reset",
    "wipe phone",
    "erase everything",
    "delete everything",
    "format phone",
    "bypass password",
    "bypass pin",
    "bypass lock",
    "bypass security",
    "hack",
    "steal",
    "root phone",
    "disable security",
    "rm -rf",
    "chmod",
]

def run_safe_cmd(cmd_list, timeout=12):
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return result.stdout.strip()
    except Exception:
        return ""

def speak(text):
    if not text:
        return
    clean_text = str(text)
    clean_text = re.sub(r"https?://\S+", "", clean_text)
    clean_text = re.sub(r"\{.*?\}", "", clean_text, flags=re.S)
    clean_text = re.sub(r"\[.*?\]", "", clean_text, flags=re.S)
    clean_text = re.sub(r"[^\w\s.,!?'%-]", "", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    if not clean_text:
        return
    print(f"JARVIS: {clean_text}", flush=True)
    run_safe_cmd(["termux-tts-speak", "-l", "en", "-r", "0.95", clean_text])

def listen_speech():
    try:
        result = subprocess.run(
            ["termux-speech-to-text"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
        return result.stdout.strip()
    except Exception:
        return ""

def get_battery():
    output = run_safe_cmd(["termux-battery-status"])
    try:
        data = json.loads(output)
        pct = data.get("percentage")
        if pct is not None:
            return f"Your battery is at {pct} percent, Boss."
    except Exception:
        pass
    return "I couldn't verify battery levels, Boss."

def toggle_flashlight(state):
    if state in ("on", "off"):
        run_safe_cmd(["termux-torch", state])
        return f"Flashlight switched {state}, Boss."
    return "Please specify on or off, Boss."

def set_brightness(percent):
    try:
        val = max(0, min(100, int(percent)))
        scaled = round(val * 255 / 100)
        run_safe_cmd(["termux-brightness", str(scaled)])
        return f"Brightness set to {val} percent, Boss."
    except Exception:
        return "Could not adjust brightness, Boss."

def set_volume(percent):
    try:
        val = max(0, min(100, int(percent)))
        scaled = round(val * 15 / 100)
        run_safe_cmd(["termux-volume", "music", str(scaled)])
        return f"Volume set to {val} percent, Boss."
    except Exception:
        return "Could not adjust volume, Boss."

def open_app(app_name):
    clean_name = app_name.lower().strip()
    for name, pkg in APPS.items():
        if name in clean_name:
            run_safe_cmd(["monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
            return f"Opening {name.title()}, Boss."
    return f"I am not authorized to open {app_name}, Boss."

def call_contact(name):
    clean_name = name.lower().strip()
    for contact, number in CONTACTS.items():
        if contact in clean_name:
            if number and re.match(r"^\+?[0-9]{7,15}$", number.strip()):
                run_safe_cmd(["termux-telephony-call", number.strip()])
                return f"Calling {contact.title()}, Boss."
            return f"No valid phone number saved for {contact.title()}, Boss."
    return f"{name.title()} is not in your contacts, Boss."

def load_tasks():
    try:
        if not TASK_FILE.exists():
            return []
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_tasks(tasks):
    try:
        with open(TASK_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def add_task(task_text):
    sanitized = re.sub(r"[^\w\s.,-]", "", task_text).strip()
    if not sanitized:
        return "Task description is empty, Boss."
    tasks = load_tasks()
    tasks.append({"task": sanitized, "completed": False})
    if save_tasks(tasks):
        return f"Task saved: {sanitized}, Boss."
    return "Failed to save the task, Boss."

def list_tasks():
    tasks = load_tasks()
    active = [item["task"] for item in tasks if isinstance(item, dict) and not item.get("completed", False)]
    if not active:
        return "You have no active tasks, Boss."
    return "Your active tasks are: " + "; ".join(active) + "."

def get_location_coords():
    output = run_safe_cmd(["termux-location", "-p", "network"], timeout=15)
    if not output or "latitude" not in output:
        output = run_safe_cmd(["termux-location", "-p", "gps"], timeout=15)
    try:
        data = json.loads(output)
        lat = data.get("latitude")
        lon = data.get("longitude")
        if lat is not None and lon is not None and str(lat).strip() != "":
            return float(lat), float(lon)
    except Exception:
        pass
    return None, None

def get_location():
    lat, lon = get_location_coords()
    if lat is not None and lon is not None:
        return f"Your approximate location is latitude {lat:.2f}, longitude {lon:.2f}, Boss."
    return "Location unavailable. Please make sure phone GPS is enabled, Boss."

def get_weather():
    lat, lon = get_location_coords()
    if lat is None or lon is None:
        lat, lon = 20.59, 78.96
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature"
        req = urllib.request.Request(url, headers={"User-Agent": "JarvisAssistant/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        current = data.get("current", {})
        temp = current.get("temperature_2m")
        feels = current.get("apparent_temperature")
        if temp is not None:
            return f"The current temperature is {temp} degrees Celsius, feels like {feels} degrees, Boss."
    except Exception:
        pass
    return "I couldn't fetch the weather forecast right now, Boss."

def get_time():
    out = run_safe_cmd(["date", "+%I:%M %p"])
    return f"The time is {out}, Boss." if out else "Time is unavailable."

def get_date():
    out = run_safe_cmd(["date", "+%A, %d %B %Y"])
    return f"Today is {out}, Boss." if out else "Date is unavailable."

def is_forbidden(text):
    text_lower = text.lower()
    return any(p in text_lower for p in FORBIDDEN_PATTERNS)

def handle_direct_command(text):
    lower = text.lower().strip()
    if is_forbidden(lower):
        return "That request is restricted for safety reasons, Boss."

    shutdown_words = ["shutdown", "shut down", "shut", "exit", "quit", "stop jarvis", "close jarvis", "sleep", "goodbye", "bye"]
    if any(w == lower or lower.endswith(w) or lower.startswith(w) for w in shutdown_words):
        speak("Shutting down safely. Goodbye, Boss.")
        return "__EXIT__"

    if "battery" in lower or "charge" in lower:
        return get_battery()

    if any(w in lower for w in ["flashlight", "torch", "light"]):
        if any(w in lower for w in ["on", "enable", "start"]):
            return toggle_flashlight("on")
        if any(w in lower for w in ["off", "disable", "stop"]):
            return toggle_flashlight("off")

    if "brightness" in lower:
        if "max" in lower or "full" in lower or "100" in lower:
            return set_brightness(100)
        if "min" in lower or "low" in lower or "zero" in lower:
            return set_brightness(10)
        match = re.search(r"(\d{1,3})", lower)
        if match:
            return set_brightness(int(match.group(1)))

    if "volume" in lower or "sound" in lower:
        if "max" in lower or "full" in lower or "100" in lower:
            return set_volume(100)
        if "mute" in lower or "zero" in lower or "silent" in lower:
            return set_volume(0)
        match = re.search(r"(\d{1,3})", lower)
        if match:
            return set_volume(int(match.group(1)))

    if "open " in lower or "launch " in lower:
        for app_name in APPS:
            if app_name in lower:
                return open_app(app_name)

    if "call " in lower or "dial " in lower:
        for contact in CONTACTS:
            if contact in lower:
                return call_contact(contact)

    if any(q in lower for q in ["list task", "show task", "my task", "what are my task"]):
        return list_tasks()

    for pattern in ["add task ", "add a task ", "remember to ", "remind me to "]:
        if pattern in lower:
            task = text.split(pattern, 1)[-1].strip()
            if task:
                return add_task(task)

    if any(q in lower for q in ["where am i", "my location", "current location", "gps", "coordinates", "address"]):
        return get_location()

    if any(q in lower for q in ["weather", "temperature", "forecast", "how hot", "how cold"]):
        return get_weather()

    if any(q in lower for q in ["what time", "the time", "current time", "tell me time"]):
        return get_time()

    if any(q in lower for q in ["today's date", "what date", "current date", "which date", "what day"]):
        return get_date()

    return None

def ask_ai(user_text):
    if not OPENROUTER_API_KEY:
        return "My AI network is not configured, Boss."
    system_prompt = (
        "You are J.A.R.V.I.S., a polite, concise personal assistant. "
        "Address the user as Boss. Answer in 1 to 2 clear sentences. "
        "Never invent system actions."
    )
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.2,
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "JARVIS Safe Android Assistant",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        result = json.loads(raw)
        choices = result.get("choices", [])
        if not choices:
            return "I couldn't process an answer right now, Boss."
        answer = choices[0].get("message", {}).get("content", "")
        answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.S | re.I).strip()
        return answer if answer else "I couldn't process an answer right now, Boss."
    except Exception:
        return "I am unable to reach the AI network right now, Boss."

def process_command(text):
    clean_text = text.strip()
    if not clean_text or len(clean_text) <= 1:
        return
    result = handle_direct_command(clean_text)
    if result == "__EXIT__":
        raise SystemExit
    if result:
        speak(result)
        return
    print("🧠 Processing with AI...")
    answer = ask_ai(clean_text)
    speak(answer)

def main():
    print()
    print("=" * 52)
    print("        J.A.R.V.I.S. — HARDENED ASSISTANT       ")
    print("=" * 52)
    print(f"🔑 OpenRouter: {'CONFIGURED' if OPENROUTER_API_KEY else 'NOT CONFIGURED'}")
    print(f"🧠 Model: {MODEL}")
    print("🎤 Voice: Continuous listening")
    print("🛡️ Security: 100% Safe Execution (shell=False)")
    print()
    print("Say 'shutdown', 'sleep', or 'exit' to stop.")
    print()
    speak("JARVIS security protocols active. Ready, Boss.")
    while True:
        try:
            print("\n🎤 Listening for command...", flush=True)
            text = listen_speech()
            if not text:
                time.sleep(0.5)
                continue
            print(f"You: {text}", flush=True)
            process_command(text)
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nJARVIS stopped safely.")
            break
        except SystemExit:
            break
        except Exception:
            time.sleep(1)
            continue

if __name__ == "__main__":
    main()
  
