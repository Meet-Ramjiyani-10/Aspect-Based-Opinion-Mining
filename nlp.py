"""Explainable, offline Marathi/Hindi/English ABSA baseline. No remote inference."""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict

VERSION = "1.0.0-rule-baseline"
# Include combining marks: Python's \w does not preserve Devanagari matras.
TOKEN = re.compile(r"[a-zA-Z0-9]+(?:['’][a-zA-Z]+)*|[\u0900-\u097f]+|[\U0001F300-\U0001FAFF]", re.UNICODE)
ASPECTS = {
    "Food": "food taste tasty meal pizza biryani khana khaana jevan jevanachi चव जेवण खाना स्वाद अन्न",
    "Delivery": "delivery delivered rider shipping courier parcel डिलिव्हरी डिलिवरी डिलीवरी पोहोचली पोहोचला",
    "Service": "service staff support waiter customer सेवा कर्मचारी सर्विस स्टाफ",
    "Price": "price cost expensive cheap value paisa paise kimat kimmat किंमत कीमत पैसे महाग स्वस्त",
    "Quality": "quality product material build packaging package दर्जा गुणवत्ता पॅकिंग पॅकेजिंग",
    "App": "app application interface login payment refund crash bug पेमेंट अॅप ॲप रिफंड अ‍ॅप",
    "Battery": "battery charging charger बॅटरी बैटरी चार्जिंग",
    "Camera": "camera photo photos picture कॅमेरा कैमरा फोटो",
}
ASPECT_LOOKUP = {w: a for a, words in ASPECTS.items() for w in words.split()}
POSITIVE = set("good great excellent amazing awesome delicious tasty fresh fast quick friendly helpful perfect love loved best nice smooth affordable reliable happy satisfied mast chhan chan changla changli changle bhari bhannat sundar swadisht accha achha achi achhi achhe badhiya badiya sasta sasti उत्तम छान चांगला चांगली चांगले मस्त भारी स्वादिष्ट अच्छा अच्छी अच्छे बढ़िया बढिया ताजा जलद स्वस्त समाधानकारक आवडले आवडला आवडली 😊 😍 ❤ 👍".split())
NEGATIVE = set("bad terrible awful horrible poor worst slow late delayed cold stale rude broken damaged expensive overpriced disappointing disappointed useless crash crashes buggy pathetic hate hated waste kharab bakwas bekar ganda gandi mahag vait wait खराब बकवास बेकार वाईट महाग खराबच उशीर थंड उद्धट गंदा गंदी निराश खराबी 😡 😠 👎".split())
NEGATORS = set("not no never nahi nahin nai na nako nahiye naste navhta navhati नाही नाहीये नव्हता नव्हती नको नहीं नही मत बिना".split())
INTENSIFIERS = set("very really extremely too khup khoop bahut bohot ekdum खूप फार बहुत एकदम".split())
MARATHI = set("aahe ahe aahet nahiye changla changli changle chhan chan khup khoop jevan vait mahag pan mala zala zali hota hoti aahe नाहीये आहे आहेत छान चांगला चांगली चांगले खूप जेवण वाईट पण मला झाला झाली होती होता".split())
HINDI = set("hai hain tha thi bahut bohot accha achha achi khana lekin mujhe mera ka ki aur nahi nahin badhiya badiya hai है हैं था थी बहुत अच्छा अच्छी खाना लेकिन मुझे मेरा की और नहीं".split())
SHARED = set("mast kharab paisa paise nahi खराब मस्त पैसे नाही".split())
STOP = set("the a an is are was were this that it and or of to in for with on my i me hai hain ahe aahe ka ki ke aur पण पण आहे है तो हे एक व आणि".split())
CONTRAST = re.compile(r"[.!?।;,\n]+|\b(?:but|however|lekin|magar|pan)\b|लेकिन|मगर|पण", re.I)


def normalize(text):
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\b([a-z]+)n['’]t\b", r"\1 not", text)
    text = re.sub(r"([a-z])\1{2,}", r"\1\1", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text):
    return TOKEN.findall(normalize(text))


def language_info(words):
    counts = Counter()
    tagged = []
    for word in words:
        label = "mr" if word in MARATHI else "hi" if word in HINDI else "shared" if word in SHARED else "devanagari-unknown" if re.search(r"[\u0900-\u097f]", word) else "en/unknown"
        counts[label] += 1
        tagged.append({"token": word, "language": label})
    mr, hi = counts["mr"], counts["hi"]
    label = "Marathi-English" if mr > hi else "Hindi-English" if hi > mr else "Indic/English ambiguous" if mr or hi or counts["shared"] or counts["devanagari-unknown"] else "English/unknown"
    known = counts["mr"] + counts["hi"] + counts["shared"]
    return {"label": label, "method": "lexicon heuristic; shared-script and Romanized words may be ambiguous", "counts": dict(counts), "tokens": tagged, "mix_ratio": round(known / max(len(words), 1), 3)}


def polarity(score, signs):
    if 1 in signs and -1 in signs:
        return "mixed"
    return "positive" if score > 0 else "negative" if score < 0 else "neutral"


def analyze(text, review_id="", metadata=None):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Review text must be a non-empty string.")
    if len(text) > 10000:
        raise ValueError("Each review must contain at most 10,000 characters.")
    normalized = normalize(text)
    words = tokens(text)
    mentions = defaultdict(list)
    all_cues = []
    for clause in filter(str.strip, CONTRAST.split(normalized)):
        ws = tokens(clause)
        targets = [(i, ASPECT_LOOKUP[w], w) for i, w in enumerate(ws) if w in ASPECT_LOOKUP]
        cues = []
        for i, word in enumerate(ws):
            if word not in POSITIVE and word not in NEGATIVE:
                continue
            base = 1 if word in POSITIVE else -1
            before = ws[max(0, i - 3):i]
            # Postposed negation is frequent in Hindi/Marathi: "accha nahi", "changla nahi".
            after = ws[i + 1:i + 3]
            next_target = min((j for j, _, _ in targets if j > i), default=len(ws))
            after = ws[i + 1:min(i + 3, next_target)]
            preceding_target = max((j for j, _, _ in targets if j < i), default=-1)
            # Restrict negation to current predicate when another opinion intervenes.
            prev_cue = max((j for j in range(i) if ws[j] in POSITIVE | NEGATIVE), default=-1)
            before = ws[max(0, i - 3, prev_cue + 1, preceding_target):i]
            negation_count = sum(w in NEGATORS for w in before + after)
            negated = negation_count % 2 == 1
            weight = 1.5 if any(w in INTENSIFIERS for w in before) else 1.0
            score = base * (-1 if negated else 1) * weight
            cue = {"word": word, "negated": negated, "score": score}
            cues.append((i, cue))
            all_cues.append(cue)
        if targets:
            buckets = defaultdict(list)
            for pos, cue in cues:
                # Nearest explicit target within the same clause; ties prefer prior target.
                nearest = min(targets, key=lambda t: (abs(t[0] - pos), t[0] > pos))
                buckets[nearest[1]].append(cue)
            for aspect in dict.fromkeys(a for _, a, _ in targets):
                mentions[aspect].append({"clause": clause.strip(), "terms": list(dict.fromkeys(w for _, a, w in targets if a == aspect)), "cues": buckets[aspect]})
    aspects = []
    for aspect, evidence in mentions.items():
        cues = [c for mention in evidence for c in mention["cues"]]
        score = sum(c["score"] for c in cues)
        signs = {1 if c["score"] > 0 else -1 for c in cues}
        aspects.append({"aspect": aspect, "sentiment": polarity(score, signs), "score": score, "evidence": evidence, "strength": "explicit cue" if cues else "no opinion cue"})
    signs = {1 if c["score"] > 0 else -1 for c in all_cues}
    overall = polarity(sum(c["score"] for c in all_cues), signs)
    return {"id": str(review_id), "text": text, "normalized": normalized, "language": language_info(words), "word_count": len(words), "sentence_count": len([s for s in re.split(r"[.!?।]+", text) if s.strip()]), "aspects": aspects, "sentiment": overall, "opinion_cues": all_cues, "tokens": words, "metadata": metadata or {}, "engine": VERSION, "limitations": ["Rule baseline; strength is evidence coverage, not calibrated probability.", "Implicit aspects, sarcasm, spelling variation, and long-distance attribution may be missed."]}


def corpus_insights(results):
    import numpy as np
    from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

    texts = [r["normalized"] for r in results]
    aspect_counts = defaultdict(Counter)
    for result in results:
        for item in result["aspects"]:
            aspect_counts[item["aspect"]][item["sentiment"]] += 1
    report = {"total": len(results), "sentiments": dict(Counter(r["sentiment"] for r in results)), "languages": dict(Counter(r["language"]["label"] for r in results)), "aspects": [{"aspect": a, **{s: c[s] for s in ["positive", "negative", "neutral", "mixed"]}, "total": sum(c.values())} for a, c in sorted(aspect_counts.items(), key=lambda p: -sum(p[1].values()))], "topics": [], "keywords": [], "semantic_neighbors": []}
    if not texts:
        return report
    params = {"tokenizer": tokens, "token_pattern": None, "lowercase": False, "stop_words": list(STOP), "max_features": 3000}
    try:
        vectorizer = TfidfVectorizer(**params, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return report
    names = vectorizer.get_feature_names_out()
    weights = np.asarray(matrix.mean(axis=0)).ravel()
    report["keywords"] = [{"term": str(names[i]), "weight": round(float(weights[i]), 4)} for i in weights.argsort()[-18:][::-1]]
    counts_vectorizer = CountVectorizer(**params)
    counts = counts_vectorizer.fit_transform(texts)
    count_names = counts_vectorizer.get_feature_names_out()
    if len(texts) >= 3 and len(count_names) >= 3:
        lda = LatentDirichletAllocation(n_components=min(4, len(texts), len(count_names)), random_state=42, max_iter=15)
        lda.fit(counts)
        report["topics"] = [{"topic": i + 1, "terms": [str(count_names[j]) for j in component.argsort()[-6:][::-1]]} for i, component in enumerate(lda.components_)]
    if matrix.shape[0] >= 3 and matrix.shape[1] >= 3:
        embedding = TruncatedSVD(n_components=min(16, min(matrix.shape) - 1), random_state=42).fit_transform(matrix)
        norms = np.linalg.norm(embedding, axis=1, keepdims=True)
        embedding = embedding / np.maximum(norms, 1e-12)
        similarities = embedding @ embedding.T
        np.fill_diagonal(similarities, -2)
        for i in range(min(5, len(texts))):
            j = int(similarities[i].argmax())
            report["semantic_neighbors"].append({"review": results[i]["id"], "neighbor": results[j]["id"], "cosine": round(float(similarities[i, j]), 3)})
    return report


def pipeline_details(text, corpus=None):
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    ws = tokens(text)
    stemmer = PorterStemmer()
    lemma = WordNetLemmatizer()
    pos, pos_method = [], "unavailable; install NLTK resources using setup command"
    try:
        import nltk
        # English tagger is deliberately restricted to Latin tokens.
        latin = [w for w in ws if re.fullmatch("[a-z]+", w)]
        pos = [{"token": w, "tag": tag} for w, tag in nltk.pos_tag(latin)]
        pos_method = "NLTK English averaged perceptron; Indic/Romanized Indic tags are not validated"
    except LookupError:
        pass
    lemmas, lemma_method = [], "WordNet unavailable; install resources"
    try:
        lemmas = [{"token": w, "lemma": lemma.lemmatize(w)} for w in ws if re.fullmatch("[a-z]+", w)]
        lemma_method = "WordNet noun lemmatization on Latin-script tokens; Romanized Indic output is not validated"
    except LookupError:
        pass
    training = [tokens(t) for t in (corpus or [text])]
    bigrams, contexts, vocab = Counter(), Counter(), set()
    for sequence in training:
        padded = ["<s>"] + sequence + ["</s>"]
        vocab.update(padded[1:])
        bigrams.update(zip(padded, padded[1:]))
        contexts.update(padded[:-1])
    padded = ["<s>"] + [w if w in vocab else "<unk>" for w in ws] + ["</s>"]
    vocab.add("<unk>")
    factors = [{"bigram": f"{a} → {b}", "probability": (bigrams[a, b] + 1) / (contexts[a] + len(vocab))} for a, b in zip(padded, padded[1:])]
    log_probability = sum(math.log(f["probability"]) for f in factors)
    return {"normalized": normalize(text), "language": language_info(ws), "stems": [{"token": w, "stem": stemmer.stem(w)} for w in ws if re.fullmatch("[a-z]+", w)], "lemmas": lemmas, "lemma_method": lemma_method, "pos": pos, "pos_method": pos_method, "bigrams": factors, "log_probability": log_probability, "perplexity": math.exp(-log_probability / max(1, len(factors))), "ngram_note": "Add-one-smoothed bigram model. Trained on current imported corpus (or input itself if empty); this is a demonstration, not held-out perplexity.", "entities": [{"text": m.group(), "type": "URL"} for m in re.finditer(r"https?://\S+", text)] + [{"text": m.group(), "type": "AMOUNT"} for m in re.finditer(r"(?:₹|Rs\.?\s*)\d+(?:\.\d+)?", text)], "entity_method": "Pattern-based URL/amount extraction; not a trained NER model"}
