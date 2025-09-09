import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'data.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

os.makedirs(INSTANCE_DIR, exist_ok=True)

if os.path.exists(DB_PATH):
    print("Database already initialized.")
    sys.exit(0)

if not os.path.exists(SCHEMA_PATH):
    print(f"schema.sql not found at: {SCHEMA_PATH}")
    sys.exit(1)

try:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")   
        conn.execute("PRAGMA synchronous = FULL;")  
        conn.execute("PRAGMA busy_timeout = 5000;")

        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        conn.executescript(sql_script)
       

    print("Database initialized successfully.")
except Exception as e:
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except OSError: pass
    print(f"Initialization failed: {e}")
    sys.exit(1)
