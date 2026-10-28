"""Run the same reproducible experiment as the dashboard, export a JSON artifact."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import storage
from experiments import evaluate

if __name__ == "__main__":
    try:
        report = evaluate(storage.list_reviews())
    except ValueError as exc:
        raise SystemExit(str(exc))
    path = Path("artifacts/evaluation.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {path}")
