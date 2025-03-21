# Codul complet cu Flask, autentificare, dashboard, redenumire PDF, etc.
# LTS Martie25 – HX711 + Web + PDF + Buton GPIO + Autentificare

"""
Acest program:
1. Citește greutatea de la senzorul HX711
2. Permite Start/Stop printr-un buton fizic (toggle pe GPIO24)
3. Salvează valorile în fișier CSV doar când este activat
4. Oferă interfață web securizată cu autentificare:
   - /login      → autentificare utilizator
   - /           → pagină cu grafic live (protejată)
   - /latest     → ultimă valoare (protejată)
   - /history    → istoric CSV (protejată)
   - /pdf        → PDF raport (protejată)
5. Pornește automat la boot (via systemd)
"""

import threading
import time
import csv
import os
import signal
from datetime import datetime
from hx711 import HX711
from flask import Flask, jsonify, send_file, render_template_string, request, redirect, url_for, session
from functools import wraps
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO
from werkzeug.security import generate_password_hash, check_password_hash

# ==================== CONFIG ====================
DOUT_PIN = 5
SCK_PIN = 6
BUTTON_PIN = 24
CSV_FILE = "masuratori.csv"
PDF_DIR = "rapoarte"
os.makedirs(PDF_DIR, exist_ok=True)

# ==================== AUTENTIFICARE ====================
USERNAME = "admin"
PASSWORD_HASH = generate_password_hash("parola123")

# ==================== FLASK APP ====================
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Decorator pentru autentificare
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
            session["logged_in"] = True
            return redirect(url_for("index"))
        return "<h3>Login greșit</h3><a href='/login'>Încearcă din nou</a>"
    return '''
        <form method="post">
            <h3>Autentificare</h3>
            Utilizator: <input type="text" name="username"><br>
            Parolă: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

# ==================== VARIABILE ====================
latest_data = {"timestamp": None, "value": None}
recording = False

# ==================== INIT ====================
hx = HX711(dout_pin=DOUT_PIN, pd_sck_pin=SCK_PIN)
hx.zero()

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def toggle_recording(channel):
    global recording
    recording = not recording
    print(f"\n🎮 Sistem {'PORNIT' if recording else 'OPRIT'}")

GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=toggle_recording, bouncetime=500)

# ==================== MĂSURĂTORI ====================
def measurement_loop():
    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timp", "Greutate (g)"])
        print("🟢 Sistem pregătit. Așteaptă apăsarea butonului pentru start.")
        while True:
            try:
                val = max(0, hx.get_weight_mean(5))
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                latest_data["timestamp"] = timestamp
                latest_data["value"] = round(val, 2)
                if recording:
                    writer.writerow([timestamp, round(val, 2)])
                    file.flush()
                    print(f"[{timestamp}] {val:.2f} g")
                time.sleep(1)
            except Exception as e:
                print("Eroare:", e)
                time.sleep(1)

# ==================== RUTE PROTEJATE ====================
@app.route("/")
@login_required
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Greutate Live</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h2>Grafic Greutate Live</h2>
        <canvas id="grafic" width="400" height="200"></canvas>
        <script>
            const ctx = document.getElementById('grafic').getContext('2d');
            const chart = new Chart(ctx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Greutate (g)', data: [], borderWidth: 2 }] },
                options: { scales: { y: { beginAtZero: true } } }
            });
            async function actualizeaza() {
                const r = await fetch('/latest');
                const j = await r.json();
                const t = j.timp, v = j.valoare;
                if (chart.data.labels.length > 20) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }
                chart.data.labels.push(t);
                chart.data.datasets[0].data.push(v);
                chart.update();
            }
            setInterval(actualizeaza, 1000);
        </script>
        <p><a href="/pdf" target="_blank">📄 Descarcă PDF</a> | <a href="/logout">🔒 Logout</a></p>
    </body>
    </html>
    """)

@app.route("/latest")
@login_required
def latest():
    return jsonify(latest_data)

@app.route("/history")
@login_required
def history():
    rows = []
    try:
        with open(CSV_FILE) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except:
        pass
    return jsonify(rows)

@app.route("/pdf")
@login_required
def pdf():
    try:
        with open(CSV_FILE) as f:
            reader = csv.DictReader(f)
            data = list(reader)
            timp = [row['Timp'] for row in data]
            greutate = [float(row['Greutate (g)']) for row in data]

        plt.figure(figsize=(10,5))
        plt.plot(timp, greutate, marker='o')
        plt.xticks(rotation=45)
        plt.xlabel("Timp")
        plt.ylabel("Greutate (g)")
        plt.title("Raport măsurători")
        plt.tight_layout()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = f"{PDF_DIR}/raport_{timestamp}.pdf"
        plt.savefig(pdf_path)
        plt.close()
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)})

# ==================== PORNIRE ====================
def signal_handler(sig, frame):
    print("\n🛑 Închidere...")
    GPIO.cleanup()
    exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    thread = threading.Thread(target=measurement_loop, daemon=True)
    thread.start()
    app.run(host="192.168.0.137", port=5000)