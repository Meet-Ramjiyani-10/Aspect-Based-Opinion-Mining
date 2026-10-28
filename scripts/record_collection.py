"""Record local acquisition counts without redistributing review text."""
import collections
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import storage
from nlp import language_info, tokens

path = Path("data/collected_food_reviews.csv")
with path.open(encoding="utf-8-sig") as stream:
    raw = list(csv.DictReader(stream))
rows = [r for r in storage.list_reviews() if not r["is_demo"]]
manifest = {
    "source": "Google Play:com.application.zomato",
    "collection_recorded_at": datetime.now(timezone.utc).isoformat(),
    "retrieval_locales": ["mr", "hi", "en"],
    "raw_unique_source_records": len(raw),
    "unique_imported_texts": len(rows),
    "raw_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "language_estimates_unverified": dict(collections.Counter(language_info(tokens(r["text"]))["label"] for r in rows)),
    "human_annotations": sum(bool(r["annotation"].get("sentiment")) for r in rows),
    "note": "Locale and heuristics do not establish code-mixing. Manual language filtering and independent human annotations required.",
}
Path("data/collection_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
