"""Collect public Play Store reviews, without reviewer names or profile images."""
import argparse
import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nlp import language_info, tokens


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, help="Play Store application ID, e.g. com.application.zomato")
    parser.add_argument("--count", type=int, default=200, help="Maximum per requested locale")
    parser.add_argument("--languages", nargs="+", default=["mr", "hi", "en"])
    parser.add_argument("--output", type=Path, default=Path("data/collected_reviews.csv"))
    args = parser.parse_args()
    if not 1 <= args.count <= 1000:
        parser.error("Use a count between 1 and 1000 per locale.")
    try:
        from google_play_scraper import Sort, reviews
    except ImportError:
        parser.exit(1, "Install requirements first: python -m pip install -r requirements.txt\n")
    collected, seen = [], set()
    for lang in args.languages:
        # Locale is a retrieval setting, never a verified language annotation.
        batch, _ = reviews(args.app, lang=lang, country="in", sort=Sort.NEWEST, count=args.count)
        for row in batch:
            text = (row.get("content") or "").strip()
            if not text or row["reviewId"] in seen:
                continue
            seen.add(row["reviewId"])
            collected.append({"text": text, "source": f"Google Play:{args.app}", "source_url": f"https://play.google.com/store/apps/details?id={args.app}&reviewId={row['reviewId']}", "language": "unverified", "language_estimate": language_info(tokens(text))["label"], "retrieval_locale": lang, "collected_at": datetime.now(timezone.utc).isoformat(), "review_date": row["at"].isoformat(), "rating": row.get("score", ""), "source_id_hash": hashlib.sha256(row["reviewId"].encode()).hexdigest()})
    if not collected:
        parser.exit(1, "No reviews returned. No file was written.\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(collected[0]))
        writer.writeheader()
        writer.writerows(collected)
    print(f"Saved {len(collected)} unique public reviews to {args.output}.")
    print("Manually verify language and code-mixing; locale and star rating are not gold labels.")


if __name__ == "__main__":
    main()
