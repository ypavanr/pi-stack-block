from flask import Flask, request, jsonify, g
import sqlite3, os
from pathlib import Path
from services.blocks import create_block

app = Flask(__name__, instance_relative_config=True)

BASE_DIR = Path(__file__).resolve().parent.parent    
INSTANCE_DIR = BASE_DIR / "instance"                 
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)      
DB_PATH = INSTANCE_DIR / "data.db"                   

app.logger.info(f"Using DB: {DB_PATH}")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH.as_posix())
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
        g.db.execute("PRAGMA journal_mode = WAL;")
        g.db.execute("PRAGMA synchronous = FULL;")
        g.db.execute("PRAGMA busy_timeout = 5000;")
    return g.db

@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()

@app.post("/createblock")
def route_create_block():
    payload = request.get_json(force=True) or {}
    try:
        result = create_block(
            get_db(),
            question=payload.get("question", ""),
            answer=payload.get("answer", ""),
            tags=payload.get("tags")
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
