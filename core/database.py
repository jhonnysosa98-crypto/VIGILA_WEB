import sqlite3
import os
import json
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "surveillance.db")

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de cámaras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cameras (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source_type TEXT NOT NULL, -- 'webcam', 'rtsp', 'synthetic', 'file'
            source_url TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            motion_enabled INTEGER DEFAULT 1,
            sensitivity INTEGER DEFAULT 30, -- 1-100 (umbral de detección)
            record_on_motion INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de eventos / alertas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            camera_name TEXT NOT NULL,
            event_type TEXT NOT NULL, -- 'motion', 'snapshot', 'recording'
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            snapshot_path TEXT,
            video_path TEXT,
            details TEXT,
            is_read INTEGER DEFAULT 0
        )
    ''')

    # Tabla de configuraciones del sistema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Configuración por defecto
    default_settings = {
        'alert_sound': 'true',
        'motion_record_seconds': '10',
        'max_storage_gb': '5',
        'stream_quality': '80'
    }

    for key, val in default_settings.items():
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, val))

    # Insertar cámaras por defecto si la tabla está vacía
    cursor.execute('SELECT COUNT(*) FROM cameras')
    count = cursor.fetchone()[0]
    if count == 0:
        default_cameras = [
            ('cam_1', 'Cámara Principal (Webcam)', 'webcam', '0', 1, 1, 35, 1),
            ('cam_2', 'Cámara Acceso / Entrada (Simulada)', 'synthetic', 'patrol_entrance', 1, 1, 30, 1),
            ('cam_3', 'Cámara Almacén / Perímetro (Simulada)', 'synthetic', 'warehouse_night', 1, 1, 40, 1)
        ]
        cursor.executemany('''
            INSERT INTO cameras (id, name, source_type, source_url, is_active, motion_enabled, sensitivity, record_on_motion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_cameras)

    conn.commit()
    conn.close()

def get_cameras(active_only=False):
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute('SELECT * FROM cameras WHERE is_active = 1 ORDER BY created_at ASC')
    else:
        cursor.execute('SELECT * FROM cameras ORDER BY created_at ASC')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_camera(camera_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cameras WHERE id = ?', (camera_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_camera(camera_id, name, source_type, source_url, motion_enabled=1, sensitivity=30, record_on_motion=1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cameras (id, name, source_type, source_url, is_active, motion_enabled, sensitivity, record_on_motion)
        VALUES (?, ?, ?, ?, 1, ?, ?, ?)
    ''', (camera_id, name, source_type, source_url, motion_enabled, sensitivity, record_on_motion))
    conn.commit()
    conn.close()

def update_camera(camera_id, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(camera_id)
    query = f"UPDATE cameras SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def delete_camera(camera_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cameras WHERE id = ?', (camera_id,))
    cursor.execute('DELETE FROM events WHERE camera_id = ?', (camera_id,))
    conn.commit()
    conn.close()

def log_event(camera_id, camera_name, event_type, snapshot_path=None, video_path=None, details=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (camera_id, camera_name, event_type, snapshot_path, video_path, details, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
    ''', (camera_id, camera_name, event_type, snapshot_path, video_path, details))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id

def get_events(limit=50, camera_id=None, event_type=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if camera_id:
        query += " AND camera_id = ?"
        params.append(camera_id)
    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_today_events_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM events WHERE date(timestamp) = date('now', 'localtime')")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def delete_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT snapshot_path, video_path FROM events WHERE id = ?', (event_id,))
    row = cursor.fetchone()
    if row:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        if row['snapshot_path']:
            p = os.path.join(base_dir, row['snapshot_path'].lstrip('/'))
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass
        if row['video_path']:
            p = os.path.join(base_dir, row['video_path'].lstrip('/'))
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else default

def set_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()
