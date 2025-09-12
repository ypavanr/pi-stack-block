from flask import Flask, request, jsonify, g
import sqlite3, os
from pathlib import Path
from services.blocks import create_block,get_all_blocks,get_all_tags,get_blocks_by_all_tags,delete_block_by_id
from flask_cors import CORS



app = Flask(__name__, instance_relative_config=True)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://192.168.68.107:8080",
            ]
        }
    },
     supports_credentials=True  
)

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

@app.post("/create-block")
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
    

@app.get("/get-all-blocks")
def route_get_all_blocks():
    try: 
        result=get_all_blocks(
            get_db()
        )
        return jsonify(result),200
    except ValueError as e:
        app.logger.exception("GET /blocks failed")
        return jsonify({"error": "internal server error"}), 500
    

@app.get("/get-all-tags")
def route_get_all_tags():
    try:
        return jsonify(get_all_tags(get_db())), 200
    except Exception:
        app.logger.exception("GET /tags failed")
        return jsonify({"error": "internal server error"}), 500



@app.get("/blocks/by-tags")
def route_blocks_by_tags():
    raw = request.args.getlist("tags")
    selected: list[str] = []
    if raw:
        if len(raw) == 1 and "," in raw[0]:
            selected = [t.strip() for t in raw[0].split(",")]
        else:
            selected = [t.strip() for t in raw]

    try:
        data = get_blocks_by_all_tags(get_db(), selected)
        return jsonify(data), 200
    except Exception:
        app.logger.exception("GET /blocks/by-tags failed")
        return jsonify({"error": "internal server error"}), 500
    

@app.delete("/blocks/<int:block_id>")
def route_delete_block(block_id):
    try:
        if delete_block_by_id(get_db(), block_id):
            return "", 204
        return jsonify({"error": "not found"}), 404
    except Exception:
        app.logger.exception("DELETE /blocks/<id> failed")
        return jsonify({"error": "internal server error"}), 500