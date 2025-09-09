from typing import Iterable, Dict, Any, List, Optional
import sqlite3

def _normalize_tags(tags: Optional[Iterable[str] | str]) -> List[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        tags_iter = (t.strip() for t in tags.split(","))
    else:
        tags_iter = (str(t).strip() for t in tags)

    seen, out = set(), []
    for t in tags_iter:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out

def create_block(conn: sqlite3.Connection, *, question: str, answer: str, tags: Optional[Iterable[str] | str] = None) -> Dict[str, Any]:
    
    q = (question or "").strip()
    a = (answer or "").strip()
    if not q or not a:
        raise ValueError("Both 'question' and 'answer' are required.")

    tag_list = _normalize_tags(tags)

    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute(
            "INSERT INTO blocks (question, answer) VALUES (?, ?)",
            (q, a)
        )
        block_id = cur.lastrowid

        for name in tag_list:
            cur.execute(
                "INSERT INTO tags (name) VALUES (?) "
                "ON CONFLICT(name) DO NOTHING",
                (name,)
            )
            cur.execute("SELECT id FROM tags WHERE name = ?", (name,))
            tag_id = cur.fetchone()[0]

            cur.execute(
                "INSERT OR IGNORE INTO block_tags (block_id, tag_id) VALUES (?, ?)",
                (block_id, tag_id)
            )

        conn.commit()

        cur.execute(
            "SELECT t.name FROM tags t "
            "JOIN block_tags bt ON bt.tag_id = t.id "
            "WHERE bt.block_id = ? ORDER BY t.name",
            (block_id,)
        )
        tags_out = [r[0] for r in cur.fetchall()]

        return {"id": block_id, "question": q, "answer": a, "tags": tags_out}

    except Exception:
        conn.rollback()
        raise
