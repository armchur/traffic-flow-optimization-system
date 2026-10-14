"""
Traffic Flow Optimization System - Web Server
Modibbo Adama University, Yola - Final Year Project
"""

from flask import Flask, render_template, request, jsonify
from optimizer import compute_dynamic_splits, compute_fixed_splits
from simulation import run_simulation
from database import get_connection, init_db

app = Flask(__name__)

# Ensure DB is created on launch
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/optimize", methods=["POST"])
def optimize():
    data = request.json or {}
    traffic_input = data.get("traffic", {
        "North": {"count": 15, "queue": 20},
        "South": {"count": 75, "queue": 80},
        "East":  {"count": 10, "queue": 10},
        "West":  {"count": 50, "queue": 55}
    })
    cycle_time = int(data.get("cycle_time", 120))

    dynamic = compute_dynamic_splits(traffic_input, total_cycle=cycle_time)
    fixed = compute_fixed_splits(list(traffic_input.keys()), total_cycle=cycle_time)

    # Save allocation to database
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signal_allocations 
            (junction_id, mode, north_green, south_green, east_green, west_green, cycle_length)
            VALUES (1, 'DYNAMIC', ?, ?, ?, ?, ?)
        """, (dynamic.get("North", 0), dynamic.get("South", 0), dynamic.get("East", 0), dynamic.get("West", 0), cycle_time))
        conn.commit()
        conn.close()
    except Exception as e:
        print("DB Log warning:", e)

    return jsonify({
        "status": "success",
        "cycle_time": cycle_time,
        "dynamic_splits": dynamic,
        "fixed_splits": fixed,
        "traffic_input": traffic_input
    })

@app.route("/api/simulate", methods=["POST"])
def simulate():
    data = request.json or {}
    scenario = data.get("scenario", "MAU Yola Peak Traffic")
    cycles = int(data.get("cycles", 10))
    
    arrivals = data.get("arrivals", None)
    results = run_simulation(scenario_name=scenario, cycles=cycles, arrival_rates=arrivals)
    return jsonify(results)

@app.route("/api/history", methods=["GET"])
def history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mode, north_green, south_green, east_green, west_green, cycle_length, calculated_at 
        FROM signal_allocations 
        ORDER BY id DESC LIMIT 10
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    print("\n=======================================================")
    print("  TRAFFIC FLOW OPTIMIZATION SYSTEM - SERVER RUNNING")
    print("  Open your browser and visit: http://127.0.0.1:5000")
    print("=======================================================\n")
    app.run(debug=True, port=5000)
