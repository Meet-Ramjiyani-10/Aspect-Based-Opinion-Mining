"""Reproducible evaluation. Vectorizers fit training data only."""
import hashlib
from collections import Counter

from nlp import analyze, normalize

LABELS = ["negative", "neutral", "positive", "mixed"]


def evaluate(rows):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline

    annotated = [r for r in rows if r["annotation"].get("sentiment") and not r["is_demo"]]
    # Normalized duplicates must never cross the split, even if capitalization/URLs differ.
    unique = {}
    conflicts = 0
    for r in annotated:
        key = normalize(r["text"])
        if key in unique and unique[key]["annotation"]["sentiment"] != r["annotation"]["sentiment"]:
            conflicts += 1
        unique.setdefault(key, r)
    if conflicts:
        raise ValueError("Conflicting labels found on normalized duplicates. Resolve them before evaluation.")
    annotated = list(unique.values())
    counts = Counter(r["annotation"]["sentiment"] for r in annotated)
    if len(annotated) < 20 or len(counts) < 2 or min(counts.values()) < 4:
        raise ValueError("Evaluation needs at least 20 unique, annotated, non-demo reviews, at least two sentiment classes, and at least four examples in each represented class.")
    train, test = train_test_split(annotated, test_size=0.3, random_state=42, stratify=[r["annotation"]["sentiment"] for r in annotated])
    y_train = [r["annotation"]["sentiment"] for r in train]
    y_test = [r["annotation"]["sentiment"] for r in test]

    def metrics(predictions):
        return {"accuracy": float(accuracy_score(y_test, predictions)), "macro_f1": float(f1_score(y_test, predictions, labels=LABELS, average="macro", zero_division=0)), "confusion_matrix": confusion_matrix(y_test, predictions, labels=LABELS).tolist(), "per_class": classification_report(y_test, predictions, labels=LABELS, output_dict=True, zero_division=0)}

    models = {}
    majority = Counter(y_train).most_common(1)[0][0]
    models["Majority baseline"] = metrics([majority] * len(test))
    rule_predictions = [analyze(r["text"])["sentiment"] for r in test]
    models["Explainable rule baseline"] = metrics(rule_predictions)
    for name, analyzer, ngram in [("Word TF-IDF + Logistic Regression", "word", (1, 2)), ("Character TF-IDF + Logistic Regression", "char_wb", (3, 5))]:
        model = Pipeline([("tfidf", TfidfVectorizer(analyzer=analyzer, ngram_range=ngram, max_features=20000, sublinear_tf=True)), ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))])
        model.fit([r["text"] for r in train], y_train)
        predictions = model.predict([r["text"] for r in test]).tolist()
        models[name] = metrics(predictions)
        models[name]["errors"] = [{"id": r["id"], "text": r["text"], "gold": gold, "predicted": pred} for r, gold, pred in zip(test, y_test, predictions) if gold != pred]
    # Aspect labels are independent of overall labels and evaluate only explicitly annotated rows.
    tp = fp = fn = correct = support = 0
    for row in test:
        gold = row["annotation"].get("aspects", {})
        if not gold:
            continue
        pred = {a["aspect"]: a["sentiment"] for a in analyze(row["text"])["aspects"]}
        tp += len(gold.keys() & pred.keys())
        fp += len(pred.keys() - gold.keys())
        fn += len(gold.keys() - pred.keys())
        correct += sum(pred.get(a) == sentiment for a, sentiment in gold.items())
        support += len(gold)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    return {"labels": LABELS, "seed": 42, "train_count": len(train), "test_count": len(test), "dataset_hash": hashlib.sha256("\n".join(sorted(r["id"] + str(r["annotation"]) for r in annotated)).encode()).hexdigest(), "test_ids": [r["id"] for r in test], "train_ids": [r["id"] for r in train], "class_counts": dict(counts), "models": models, "aspect_evaluation": {"gold_aspect_support": support, "extraction_precision": precision, "extraction_recall": recall, "extraction_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0, "end_to_end_sentiment_accuracy": correct / support if support else None}, "notes": ["70/30 stratified split; seed 42; fit vectorizers only on train.", "Macro-F1 averages all four labels, including unsupported labels as zero.", "Synthetic demo rows excluded. Imported provenance is user-supplied, not independently verified.", "Scores estimate this split only. Use a locked external test set for final claims.", "Trained classifiers compare overall sentiment only. Live ABSA continues using the rule engine."]}
