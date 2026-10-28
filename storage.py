import csv
import hashlib
import io
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB = Path(__file__).parent / "data" / "reviews.sqlite3"


@contextmanager
def connection():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id TEXT PRIMARY KEY, text TEXT NOT NULL, source TEXT NOT NULL,
        source_url TEXT DEFAULT '', language TEXT DEFAULT '', collected_at TEXT DEFAULT '',
        is_demo INTEGER NOT NULL DEFAULT 0, annotation TEXT DEFAULT '{}',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    try:
        with con:
            yield con
    finally:
        con.close()


def list_reviews():
    with connection() as con:
        return [{**dict(row), "annotation": json.loads(row["annotation"])} for row in con.execute("SELECT * FROM reviews ORDER BY created_at, id")]


def import_csv(content, demo=False):
    reader = csv.DictReader(io.StringIO(content.lstrip('\ufeff')))
    if not reader.fieldnames or "text" not in reader.fieldnames:
        raise ValueError("CSV requires a 'text' column. Optional: source, source_url, language, collected_at.")
    rows = list(reader)
    if len(rows) > 2000:
        raise ValueError("Import at most 2,000 reviews per file.")
    added = skipped = 0
    with connection() as con:
        for number, row in enumerate(rows, start=2):
            text = (row.get("text") or "").strip()
            if not text:
                skipped += 1
                continue
            if len(text) > 10000:
                raise ValueError(f"Row {number}: review exceeds 10,000 characters.")
            key = hashlib.sha256(" ".join(text.casefold().split()).encode()).hexdigest()[:20]
            source = "Synthetic teaching fixture" if demo else (row.get("source") or "User import; provenance unverified")
            cursor = con.execute("INSERT OR IGNORE INTO reviews (id,text,source,source_url,language,collected_at,is_demo) VALUES (?,?,?,?,?,?,?)", (key, text, source[:300], (row.get("source_url") or "")[:2000], (row.get("language") or "")[:50], (row.get("collected_at") or "")[:100], int(demo)))
            added += cursor.rowcount
            skipped += 1 - cursor.rowcount
    return {"added": added, "skipped": skipped, "total": len(list_reviews())}


def annotate(review_id, annotation):
    from nlp import ASPECTS
    labels = {"positive", "negative", "neutral", "mixed"}
    if not isinstance(annotation, dict) or annotation.get("sentiment") not in labels:
        raise ValueError("Choose positive, negative, neutral, or mixed.")
    aspects = annotation.get("aspects", {})
    if not isinstance(aspects, dict) or any(k not in ASPECTS or v not in labels for k, v in aspects.items()):
        raise ValueError("Invalid aspect annotation.")
    clean = {"sentiment": annotation["sentiment"], "aspects": aspects}
    with connection() as con:
        if not con.execute("UPDATE reviews SET annotation=? WHERE id=?", (json.dumps(clean), review_id)).rowcount:
            raise ValueError("Review not found.")
    return clean
