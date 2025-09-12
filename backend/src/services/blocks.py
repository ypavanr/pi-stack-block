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
            "INSERT INTO blocks (question, answer) VALUES (?, ?) ON CONFLICT(question, answer) DO NOTHING",
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


def get_all_blocks(conn: sqlite3.Connection):
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT
                b.id,
                b.question,
                b.answer,
                GROUP_CONCAT(t.name, ',') AS tag_csv
            FROM blocks b
            LEFT JOIN block_tags bt ON bt.block_id = b.id
            LEFT JOIN tags t        ON t.id = bt.tag_id
            GROUP BY b.id
            ORDER BY b.id DESC
        """)
        rows = cur.fetchall()

        results = []
        for (bid, q, a, tag_csv) in rows:
            tags = []
            if tag_csv:
                seen = set()
                for name in (n.strip() for n in tag_csv.split(',')):
                    if name and name not in seen:
                        seen.add(name)
                        tags.append(name)
            results.append({
                "id": bid,
                "question": q,
                "answer": a,
                "tags": tags
            })

        return results
    except Exception:
        conn.rollback()
        raise


def get_all_tags(conn: sqlite3.Connection):
     cur = conn.cursor()
     try:
         cur.execute(
             "SELECT name FROM tags"
         )
         rows=cur.fetchall()
         return [row["name"] if isinstance(row, sqlite3.Row) else row[0] for row in rows]
     except Exception:
        conn.rollback()
        raise


def _normalize_selected_tags(tags: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for t in tags:
        if not t:
            continue
        s = str(t).strip().lower()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out

def get_blocks_by_all_tags(conn: sqlite3.Connection, selected_tags: Iterable[str]) -> List[Dict[str, Any]]:
 
    sel = _normalize_selected_tags(selected_tags)
    if not sel:
        return [] 
    placeholders = ",".join("?" * len(sel))
    params = sel + [len(sel)]

    sql = f"""
    WITH matching AS (
      SELECT bt.block_id
      FROM block_tags bt
      JOIN tags t ON t.id = bt.tag_id
      WHERE lower(t.name) IN ({placeholders})
      GROUP BY bt.block_id
      HAVING COUNT(DISTINCT lower(t.name)) = ?
    )
    SELECT b.id, b.question, b.answer,
           GROUP_CONCAT(t2.name, ',') AS tag_csv
    FROM matching m
    JOIN blocks b          ON b.id = m.block_id
    LEFT JOIN block_tags bt2 ON bt2.block_id = b.id
    LEFT JOIN tags t2         ON t2.id = bt2.tag_id
    GROUP BY b.id
    ORDER BY b.id DESC;
    """

    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()

    results: List[Dict[str, Any]] = []
    for bid, q, a, tag_csv in rows:
        tags: List[str] = []
        seen = set()
        if tag_csv:
            for n in (s.strip() for s in tag_csv.split(",")):
                if n and n not in seen:
                    seen.add(n)
                    tags.append(n)
        results.append({"id": bid, "question": q, "answer": a, "tags": tags})
    return results
    

def delete_block_by_id(conn: sqlite3.Connection, block_id: int) -> bool:
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("DELETE FROM blocks WHERE id = ?", (block_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    except Exception:
        conn.rollback()
        raise
