import sqlite3

DB_NAME = "traffic_system.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Junctions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS junctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            cycle_time INTEGER DEFAULT 120
        )
    """)

    # Approaches (North, South, East, West)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approaches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            junction_id INTEGER,
            arm_name TEXT NOT NULL,
            road_name TEXT NOT NULL,
            capacity_vph INTEGER DEFAULT 1800,
            FOREIGN KEY (junction_id) REFERENCES junctions (id)
        )
    """)

    # Traffic Density logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            approach_id INTEGER,
            vehicle_count INTEGER NOT NULL,
            queue_length_m REAL NOT NULL,
            avg_speed_kmh REAL NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (approach_id) REFERENCES approaches (id)
        )
    """)

    # Signal Timing allocations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            junction_id INTEGER,
            mode TEXT NOT NULL, -- 'FIXED' or 'DYNAMIC'
            north_green INTEGER NOT NULL,
            south_green INTEGER NOT NULL,
            east_green INTEGER NOT NULL,
            west_green INTEGER NOT NULL,
            yellow_time INTEGER DEFAULT 3,
            cycle_length INTEGER NOT NULL,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (junction_id) REFERENCES junctions (id)
        )
    """)

    # Simulation results for comparisons
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS simulation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_name TEXT NOT NULL,
            mode TEXT NOT NULL,
            total_vehicles INTEGER,
            avg_delay_sec REAL,
            avg_queue_len REAL,
            throughput_vph REAL,
            run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed initial junction: MAU Yola Campus Junction
    cursor.execute("SELECT COUNT(*) FROM junctions")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO junctions (name, location, cycle_time) VALUES (?, ?, ?)",
            ("MAU Main Gate Junction", "Modibbo Adama University, Yola", 120)
        )
        junction_id = cursor.lastrowid
        
        arms = [
            ("North", "Sangere / University Core Road"),
            ("South", "Yola-Mubi Expressway (Inbound)"),
            ("East", "Staff Quarters / Phase 2 Road"),
            ("West", "Yola-Mubi Expressway (Outbound)")
        ]
        for arm_name, road_name in arms:
            cursor.execute(
                "INSERT INTO approaches (junction_id, arm_name, road_name) VALUES (?, ?, ?)",
                (junction_id, arm_name, road_name)
            )

    conn.commit()
    conn.close()
    print("Database initialized successfully with MAU Yola sample junction.")

if __name__ == "__main__":
    init_db()
