import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import storage
from experiments import evaluate
from nlp import analyze, corpus_insights, pipeline_details, tokens


class NLPTests(unittest.TestCase):
    def aspect_map(self, text):
        return {a["aspect"]: a["sentiment"] for a in analyze(text)["aspects"]}

    def test_contrast_assigns_local_sentiment(self):
        self.assertEqual(self.aspect_map("Food khup chhan aahe pan delivery late hoti."), {"Food": "positive", "Delivery": "negative"})

    def test_hindi_postposed_negation(self):
        self.assertEqual(self.aspect_map("Service accha nahi hai. Food fresh hai."), {"Service": "negative", "Food": "positive"})

    def test_english_negation(self):
        self.assertEqual(self.aspect_map("Food is not good but delivery is fast."), {"Food": "negative", "Delivery": "positive"})

    def test_devanagari_marks_and_negation(self):
        self.assertIn("अच्छा", tokens("खाना अच्छा नहीं है।"))
        self.assertEqual(self.aspect_map("खाना अच्छा नहीं है।"), {"Food": "negative"})

    def test_mixed_same_aspect(self):
        self.assertEqual(self.aspect_map("Food is good but food is cold."), {"Food": "mixed"})

    def test_unseen_aspect_does_not_invent_label(self):
        self.assertEqual(analyze("I went there yesterday.")["aspects"], [])

    def test_neutral_mention(self):
        self.assertEqual(self.aspect_map("Delivery arrived."), {"Delivery": "neutral"})

    def test_two_targets_same_clause(self):
        self.assertEqual(self.aspect_map("Food good delivery bad"), {"Food": "positive", "Delivery": "negative"})

    def test_input_limits(self):
        for value in [None, "", " ", "a" * 10001]:
            with self.assertRaises(ValueError):
                analyze(value)

    def test_corpus_small_and_non_latin(self):
        self.assertEqual(corpus_insights([])["total"], 0)
        report = corpus_insights([analyze("Food good", "1"), analyze("Delivery bad", "2"), analyze("खाना अच्छा", "3")])
        self.assertEqual(report["total"], 3)
        self.assertTrue(report["topics"])
        self.assertTrue(report["semantic_neighbors"])

    def test_bigram_probabilities(self):
        details = pipeline_details("Food is good.")
        self.assertTrue(all(0 < f["probability"] <= 1 for f in details["bigrams"]))
        self.assertGreaterEqual(details["perplexity"], 1)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "data")
        self.patch = patch.object(storage, "DB", Path(self.tmp.name) / "reviews.sqlite3")
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        # SQLite connections may be finalized by GC on Windows.
        import gc
        gc.collect()
        self.tmp.cleanup()

    def test_import_dedupe_provenance_and_annotation(self):
        result = storage.import_csv('text,source\n"Food good",Public export\n"FOOD good",Other\n')
        self.assertEqual(result["added"], 1)
        self.assertEqual(result["skipped"], 1)
        row = storage.list_reviews()[0]
        storage.annotate(row["id"], {"sentiment": "positive", "aspects": {"Food": "positive"}})
        self.assertEqual(storage.list_reviews()[0]["annotation"]["sentiment"], "positive")

    def test_import_is_atomic_on_invalid_row(self):
        with self.assertRaises(ValueError):
            storage.import_csv('text\nFood good\n' + 'a' * 10001)
        self.assertEqual(storage.list_reviews(), [])

    def test_demo_excluded(self):
        storage.import_csv('text\nFood good\n', demo=True)
        row = storage.list_reviews()[0]
        storage.annotate(row["id"], {"sentiment":"positive"})
        with self.assertRaises(ValueError):
            evaluate(storage.list_reviews())

    def test_invalid_annotation(self):
        with self.assertRaises(ValueError):
            storage.annotate("unknown", {"sentiment":"positive","aspects":{"invented":"positive"}})


class ExperimentTests(unittest.TestCase):
    def test_shared_split_reproducible_and_no_leakage(self):
        rows = [{"id":str(i),"text":f"Food {'good' if i % 2 else 'bad'} review number {i}","is_demo":0,"annotation":{"sentiment":"positive" if i % 2 else "negative", "aspects":{"Food":"positive" if i % 2 else "negative"}}} for i in range(30)]
        a, b = evaluate(rows), evaluate(rows)
        self.assertEqual(a["test_ids"], b["test_ids"])
        self.assertFalse(set(a["train_ids"]) & set(a["test_ids"]))
        self.assertEqual(len(a["models"]), 4)
        self.assertGreater(a["aspect_evaluation"]["gold_aspect_support"], 0)
        json.dumps(a)


if __name__ == "__main__":
    unittest.main()
