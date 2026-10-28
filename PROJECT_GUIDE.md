# BhashaLens — Aspect-Based Opinion Mining

**Aspect-Based Opinion Mining on Real Marathi-English and Hindi-English Customer Reviews**

BCS25PC15 · Natural Language Processing Laboratory · B.Tech. CSE (AI & ML), Semester V.

A local research workbench with a multilingual explainable baseline, persistent review corpus, independent annotations, TF-IDF/LDA/LSA analysis, and reproducible classifier comparisons. This project is independent of the CRM in the parent repository.

## Run

Python 3.11–3.13 recommended. From this directory:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Open **http://127.0.0.1:8765**. For this workspace, the core scientific packages are already available, so `python app.py` also works.

Optional NLTK resources enable English POS tagging and WordNet noun lemmatization:

```powershell
.venv\Scripts\python -m nltk.downloader -d .nltk_data averaged_perceptron_tagger_eng wordnet omw-1.4
$env:NLTK_DATA = "$PWD\.nltk_data"
```

NLTK resources are optional; missing resources are displayed honestly rather than replaced with fabricated tags. Porter stemming works offline. The English tagger does not establish accurate Marathi/Hindi POS tagging.

## Demo walkthrough

1. In Overview, choose **Load demo corpus**. The 24 synthetic teaching reviews exercise Marathi/Hindi/English, negation, and competing aspects. They are explicitly marked and excluded from evaluation.
2. In Review analyzer, enter `Food khup chhan aahe pan delivery late hoti.` Observe positive Food and negative Delivery, with original clause evidence.
3. Try `Service accha nahi hai. Food fresh hai.` Observe postposed Hindi negation.
4. Import a real-review CSV under Dataset & labels. Search and filter the corpus. Review the language estimates; Romanized Indic language recognition is heuristic.
5. Annotate the overall sentiment independently, then label every explicit aspect. Blank means absent. Do not copy model predictions into gold labels.
6. Inspect NLP pipeline for token identification, stemming, optional lemmatization/POS, pattern entities, smoothed bigram probabilities, and LSA neighbors.
7. With at least 20 annotated non-demo reviews, at least two classes, and at least four reviews per represented class, run Model evaluation. Export the experiment JSON.

## Collect real reviews

### Current local acquisition

On 20 October 2026, the collector successfully retrieved **300 distinct public review records** for Zomato across requested `mr`, `hi`, and `en` locales. Text deduplication imported **205 unique real review texts**. They are available in the local SQLite corpus alongside 24 synthetic fixtures. The raw export is `data/collected_food_reviews.csv`; `data/collection_manifest.json` records its SHA-256 and acquisition counts. Raw text and SQLite remain local and Git-ignored.

The imported real texts have **no independent human annotations yet**. Heuristic estimates identify 21 Hindi-English and 10 Marathi-English candidates, 16 ambiguous Indic candidates, and 158 English/unknown items. These are candidate counts, not validated language/code-mixing statistics. Curate and annotate the eligible subset before reporting project results.

The collector uses the documented [google-play-scraper API](https://github.com/JoMingyu/google-play-scraper). It retrieves public reviews with source URLs, collection timestamps, original ratings, and hashed review IDs, without reviewer names/images.

```powershell
python scripts/collect_reviews.py --app com.application.zomato --count 200 --languages mr hi en --output data/collected_food_reviews.csv
```

If using the workspace-local collector installation, run the same command with `PYTHONPATH` set:

```powershell
$env:PYTHONPATH = "$PWD\.vendor"
python scripts/collect_reviews.py --app com.application.zomato --count 200 --languages mr hi en
```

Import the resulting CSV through the dashboard. Availability depends on the upstream service. Retrieval locale is **not** a verified review-language label. Manually retain genuine code-mixed reviews and verify their language. Star ratings are metadata, never aspect sentiment ground truth. Check source usage conditions before collection or redistribution. No real review corpus is presented as a labelled benchmark by default.

CSV input:

```csv
text,source,source_url,language,collected_at
"YOUR ACTUAL REVIEW TEXT",Google Play:APP_ID,https://play.google.com/store/apps/details?id=APP_ID,unverified,2026-10-20T00:00:00Z
```

Only `text` is mandatory. Imported provenance is supplied by the user and is not independently verified. Deduplication ignores case and repeated whitespace. Imports are transactional and limited to 2,000 reviews, 10,000 characters per review, and an 8 MB HTTP request.

## What is implemented

| Component | Implementation | Honest scope |
| --- | --- | --- |
| Local app | Python HTTP server + SQLite + HTML/CSS/JS | Binds only to loopback; no production hosting/authentication |
| Normalization | NFC, case, URLs, contractions, repeated Latin letters | No learned transliteration or spelling correction |
| Language identification | Token lexicons + script awareness | Indic/Romanized ambiguity reported |
| Aspects | Food, Delivery, Service, Price, Quality, App, Battery, Camera lexicons | Explicit known mentions only |
| Sentiment | Clause-local nearest-target attribution, negation, intensifiers | Explainable rule baseline; no calibrated confidence |
| Mixed sentiment | Positive and negative cues in one aspect/review | Cue-based, not a learned discourse model |
| POS / lemmas | Optional NLTK English tagger / WordNet | English-only tools; resources required |
| Entity extraction | URL and amount patterns | Pattern extraction, not a trained NER model |
| TF-IDF | Word unigrams/bigrams | Current corpus visualization |
| Embeddings | TF-IDF + truncated SVD + cosine | Corpus-level LSA document embeddings |
| Topics | Count vectors + LDA, fixed seed | Exploratory topics; no quality claim |
| Language model | Add-one bigrams, log likelihood and perplexity | Demonstration on current corpus, not held-out LM evaluation |
| Evaluation | Majority, rule, word TF-IDF LR, char TF-IDF LR | Learned models compare overall sentiment; live ABSA stays rule-based |
| Aspect metrics | Extraction precision/recall/F1 and end-to-end polarity | Requires exhaustive human aspect labels on test reviews |

## Reproducible evaluation

The application excludes demo rows, checks class support, deduplicates normalized text before splitting, rejects conflicting duplicate labels, and uses one 70/30 stratified split with seed 42. TF-IDF fits training data only. The report includes test/train IDs, a dataset fingerprint, per-class metrics, confusion matrices, and model errors. Macro-F1 includes all four labels (unsupported labels count as zero), and accuracy is separate.

```powershell
python scripts/experiment.py
python -m unittest discover -s tests -v
node --check web/app.js
```

For final submission, grow beyond the minimum gate: aim for 600–1,000 independently checked reviews, balanced language coverage, a locked test set, two annotators on a shared subset, agreement measurement, and per-language results. The minimum gate only makes a small experiment possible; it does not validate research quality. Near-duplicates and source/domain leakage still require manual auditing. Do not tune lexicons after inspecting the final test set.

## Files

```text
app.py                       Local HTTP/API entry point
nlp.py                       ABSA and syllabus inspection algorithms
storage.py                   SQLite, import, provenance, labels
experiments.py               Shared held-out evaluation
web/                         Responsive dashboard
data/demo_reviews.csv        24 explicitly synthetic fixtures
scripts/collect_reviews.py   Public real-review collection
scripts/experiment.py        CLI experiment export
tests/test_project.py        Regression/integration checks
docs/JOURNAL.md              Lab write-up and syllabus mapping
docs/ANNOTATION_GUIDE.md     Ground-truth protocol
docs/VIVA.md                 Presentation and viva preparation
```

Runtime SQLite, collected reviews, local packages, and artifacts are ignored by Git. Data persists locally across restarts. Exports contain review text; handle them according to your dataset permissions.

## References

- Patwa et al., [SemEval-2020 Task 9: Sentiment Analysis of Code-Mixed Tweets](https://aclanthology.org/2020.semeval-1.100/). SentiMix supports Hindi-English sentiment research; tweets are not a Marathi customer-review ABSA benchmark.
- scikit-learn, [TF-IDF vectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html), [Logistic Regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), and [LDA topic extraction](https://scikit-learn.org/stable/auto_examples/applications/plot_topics_extraction_with_nmf_lda.html).
- [NLTK documentation](https://www.nltk.org/) and [public review collector documentation](https://github.com/JoMingyu/google-play-scraper).
