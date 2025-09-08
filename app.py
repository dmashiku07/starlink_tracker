from flask import Flask, request, jsonify, render_template
from datetime import datetime
import sqlite3
import math

app = Flask(__name__)
DB_NAME = "gps_data.db"


# ----------- DB Setup -----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gps_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    lat REAL,
                    lng REAL,
                    altitude REAL,
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()


init_db()


# ----------- Haversine Distance -----------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # distance in meters


# ----------- Routes -----------
@app.route("/")
def index():
    return render_template("map.html")


@app.route("/tracker", methods=["POST"])
def tracker_data():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    device_id = data.get("ident")
    lat = data.get("position.latitude")
    lng = data.get("position.longitude")
    altitude = data.get("position.altitude")
    timestamp = datetime.utcnow().isoformat()

    # Save into DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO gps_history (device_id, lat, lng, altitude, timestamp) VALUES (?, ?, ?, ?, ?)",
              (device_id, lat, lng, altitude, timestamp))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"}), 200


@app.route("/history", methods=["GET"])
def get_history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT device_id, lat, lng, altitude, timestamp FROM gps_history ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "device_id": row[0],
            "lat": row[1],
            "lng": row[2],
            "altitude": row[3],
            "timestamp": row[4]
        })

    # Calculate distance traveled
    total_distance = 0
    for i in range(1, len(history)):
        total_distance += haversine(history[i - 1]["lat"], history[i - 1]["lng"],
                                    history[i]["lat"], history[i]["lng"])

    return jsonify({"points": history, "distance_meters": total_distance})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
