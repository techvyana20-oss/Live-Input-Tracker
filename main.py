import tkinter as tk
from pynput.keyboard import Key, Listener
from pynput import mouse
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
    <html>
    <head>
        <meta http-equiv="refresh" content="1">
    </head>
    <body style="background:black;color:lime;font-family:monospace;">
        <h1>TechVyana Live</h1>
        <pre>{received_text}</pre>
    </body>
    </html>
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
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# -------- MAIN APP --------
import requests
import json

caps_on = False
shift_on = False
running = False

LOG_FILE = "log.txt"
text_buffer = ""

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

# -------- KEYBOARD HANDLER --------
def on_press(key):
    global caps_on, shift_on, text_buffer, key_count

    if not running:
        return

    try:
        char = key.char

        # LETTER HANDLING
        if char.isalpha():
            if caps_on ^ shift_on:
                char = char.upper()
            else:
                char = char.lower()

        # SPECIAL CHAR HANDLING
        elif shift_on:
            special_map = {
                '1': '!', '2': '@', '3': '#', '4': '$',
                '5': '%', '6': '^', '7': '&', '8': '*',
                '9': '(', '0': ')',
                '-': '_', '=': '+',
                '[': '{', ']': '}',
                ';': ':', "'": '"',
                ',': '<', '.': '>', '/': '?',
                '\\': '|'
            }
            char = special_map.get(char, char)

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

    # UI update
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

# -------- MOUSE HANDLER --------
def on_move(x, y):
    if running:
        status_label.config(text=f"Mouse: ({x}, {y})", fg="yellow")

def on_click(x, y, button, pressed):
    if running:
        action = "Pressed" if pressed else "Released"
        msg = f"\n[Mouse {button} {action} at ({x},{y})]\n"
        text_area.insert(tk.END, msg)
        text_area.see(tk.END)

def on_scroll(x, y, dx, dy):
    if running:
        msg = f"\n[Scroll ({dx},{dy})]\n"
        text_area.insert(tk.END, msg)
        text_area.see(tk.END)

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

# -------- THREADS --------
def start_keyboard():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def start_mouse():
    with mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll
    ) as listener:
        listener.join()

# -------- UI --------
root = tk.Tk()
root.title("TechVyana PRO Input Monitor")
root.geometry("800x550")
root.configure(bg="black")

tk.Label(root, text="TECHVYANA PRO", fg="lime", bg="black",
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
threading.Thread(target=start_keyboard, daemon=True).start()
threading.Thread(target=start_mouse, daemon=True).start()
threading.Thread(target=start_server, daemon=True).start()

update_stats()
auto_send()

# -------- PRINT LINKS --------
local_ip = get_local_ip()

print("Open on PC: http://127.0.0.1:5000")
print(f"Open on Phone: http://{local_ip}:5000")

root.mainloop()
