# Project overview

Aspect Based Opinion Mining on Real Marathi English and Hindi English Customer Reviews

BhashaLens | Natural Language Processing Laboratory Project Report

Program: B.Tech. Computer Science and Engineering (AI and ML) | Semester V Course: Natural Language Processing Laboratory | Code: BCS25PC15 Department: Computer Science and Engineering (AI and ML), PCCOE, Pune

 Submitted by  Meet Ramjiyani PRN: 124B1C062 Class: TY AIML Academic year: 2026 to 2027

## Abstract

Customer reviews often combine Marathi or Hindi vocabulary with English and may praise one service aspect while criticising another. BhashaLens implements a local, explainable aspect-based opinion mining workbench that preserves review text, identifies explicit aspect categories, assigns sentiment using local opinion cues, and presents corpus-level insights. The application integrates review collection, CSV import, SQLite storage, human annotation, and reproducible evaluation.

The implemented baseline uses normalization, script-aware tokenization, language lexicons, clause splitting, nearest-aspect attribution, negation handling and intensifier weighting. Complementary demonstrations include Porter stemming, WordNet lemmatization, English POS tagging, TF-IDF, LDA topics, latent semantic analysis and smoothed bigram probabilities. The evaluation framework compares majority, rule, word TF-IDF and character TF-IDF sentiment baselines.

A collection run obtained 300 public Zomato Google Play review records, yielding 205 unique imported texts. Twenty-four synthetic fixtures support demonstrations. Language estimates remain unverified and there are currently no independently annotated real reviews; therefore this report establishes implementation and software-test results, not real-world accuracy.

## Report guide

Pages 2 to 10 cover objectives, architecture and libraries, data provenance, preprocessing, analysis methods, interface operation, syllabus mapping, evaluation and testing, and conclusions with references. The report documents the implemented system, its laboratory coverage and the remaining evaluation work.


<!-- PAGE BREAK -->

# Problem definition and objectives

## Problem statement

A review-level rating or a single sentiment label can hide conflicting experiences. For example, a customer may appreciate food quality but dislike delivery speed. The review "Food khup chhan aahe pan delivery late hoti" contains positive food sentiment and negative delivery sentiment. The project aims to identify these separate opinions while retaining interpretable evidence.

Naturally occurring code-mixed text is challenging because writers use Devanagari, Romanized Indic words, English, emojis and inconsistent spellings. Marathi and Hindi share a script and some vocabulary. A requested review locale cannot establish the actual language, and a fixed dictionary cannot cover all forms. The project consequently exposes language ambiguity and treats its live analysis as a baseline.

## Project objectives

- Build a functioning local pipeline for collecting, importing, inspecting and analysing customer reviews.
- Associate positive, negative, neutral or mixed opinions with explicit aspect categories and display the supporting clause and cue words.
- Demonstrate laboratory NLP techniques through intermediate outputs that students can inspect and explain.
- Store independently assigned human labels separately from predictions and evaluate baselines on a common held-out split.
- Document provenance, reproducibility settings, assignment coverage and failure modes without claiming unmeasured performance.
## Scope and intended users

The workbench is intended for laboratory demonstrations and small research experiments. The real acquisition focuses on a food-delivery application. The broader aspect inventory also includes battery and camera to support product-review demonstrations; these categories are not central to the Zomato study. A final domain-specific experiment should declare a consistent inventory.

## Relationship to course outcomes

| Outcome | Project evidence |
| --- | --- |
| CO1 Text preprocessing | Normalization, tokenization, counts and inspection outputs. |
| CO2 POS tagging | Optional English NLTK tagging demonstration with explicit language limitations. |
| CO3 Text classification | Word and character TF-IDF logistic regression comparisons. |
| CO4 NLP pipeline | Collection through analysis, storage, interface and evaluation. |

The current system does not implement a learned multilingual ABSA model, general transliteration, speech recognition, translation or a dedicated emotion taxonomy. These are potential extensions rather than completed capabilities.


<!-- PAGE BREAK -->

# System architecture and libraries

## Application architecture

The browser interface sends JSON requests to a Python HTTP server bound to 127.0.0.1. The server exposes analysis, corpus, import, annotation, pipeline and evaluation endpoints. SQLite persists review text, provenance, demo status and annotation JSON. Scientific libraries perform corpus analysis and classifier experiments locally; no remote language-model inference is used.

 Data flow:  Public review collector or CSV file -> validation and duplicate checks -> SQLite corpus -> normalization and NLP analysis -> dashboard and exports. Human annotations form a separate path from SQLite to the evaluation module. Exploratory topics and similarities use the corpus; supervised feature fitting uses training data only.

## Libraries and technologies

| Library or technology | Role | Declared requirement |
| --- | --- | --- |
| Python | HTTP service, pipeline, collection and experiments | 3.11 to 3.13 recommended |
| NumPy | Matrices, vector norms and cosine calculations | >=2.1 and <3 |
| scikit-learn | TF-IDF, count vectors, LDA, SVD, logistic regression and metrics | >=1.6 and <2 |
| NLTK | Porter stemming, WordNet lemmas and English POS tags | >=3.9 and <4 |
| google-play-scraper | Retrieval of public Google Play reviews | >=1.2.7 and <2 |
| SQLite via sqlite3 | Persistent local review and annotation database | Python standard library |
| HTML CSS JavaScript | Responsive interface, charts, filtering and downloads | Browser native; no UI framework |
| Other standard modules | re, unicodedata, csv, json, hashlib, pathlib, collections, math, unittest | Bundled with Python |

The requirement ranges above come from requirements.txt and are not a locked environment manifest. The initial checks reported scikit-learn 1.8.0, NumPy 2.3.0 and NLTK 3.10.0; the review collector installed version 1.2.7. Final experiment reports should archive the actual environment versions.

## Source organisation

app.py handles HTTP requests; nlp.py implements the NLP methods; storage.py handles transactions, imports and annotations; experiments.py builds the shared evaluation. web/ contains the interface. scripts/ contains collection and CLI experiment utilities. tests/test_project.py contains regression and integration checks.

NLTK tagger and WordNet resources are separate data downloads. POS and lemma panels report resource absence when unavailable. The report-generation libraries are tooling dependencies and do not form part of the application NLP pipeline.


<!-- PAGE BREAK -->

# Dataset provenance and preparation

## Source and collection procedure

The dataset was acquired from public Google Play reviews of the Zomato Android application, identified by com.application.zomato. It was not scraped from restaurant reviews on the Zomato website and was not downloaded as a ready-labelled Kaggle benchmark. The collector calls the google-play-scraper reviews API with country="in", newest-first sorting and locale requests mr, hi and en [1].

| Acquisition measure | Recorded value |
| --- | --- |
| Collection date | 20 October 2026 |
| Requested records | 100 each for mr, hi and en |
| Distinct source review records | 300 |
| Unique texts imported | 205 |
| Repeated texts skipped at import | 95 |
| Synthetic teaching fixtures | 24 |
| Stored corpus including fixtures | 229 |
| Independent real-review annotations | 0 |

Collection first deduplicates source review identifiers. Import then hashes case-folded text with collapsed whitespace, so distinct source records with identical normalized text can collapse into one stored review. The 95 skipped rows are repeated texts in this import, not proof of fraudulent reviews.

## Data fields and provenance

The raw CSV includes text, source, source_url, language, language_estimate, retrieval_locale, collected_at, review_date, rating and source_id_hash. SQLite retains the core imported provenance fields, demo status and human annotation JSON; additional acquisition fields remain in the raw CSV. The collection manifest records acquisition counts and the raw file SHA-256 for traceability.

## Language verification and corpus quality

| Heuristic estimate on unique real texts | Count |
| --- | --- |
| English or unknown | 158 |
| Hindi English candidate | 21 |
| Marathi English candidate | 10 |
| Ambiguous Indic candidate | 16 |

These estimates do not prove bilingual usage. Locale, star rating and model predictions must not be used as independent ground truth. Manually verify language and code-mixing, remove irrelevant or personal content, and retain exclusion reasons. The collector omits reviewer names and images as separate fields; review text itself still needs privacy review. Synthetic fixtures are excluded from evaluation.


<!-- PAGE BREAK -->

# Preprocessing and linguistic inspection

## Normalization and tokenization

The working copy of each review undergoes Unicode NFC normalization and lowercasing. URL strings are removed, simple English contraction patterns expose negation, repeated Latin letters are reduced, and whitespace is collapsed. The original review remains available for inspection. This process reduces superficial variation but is not a general spelling corrector or transliteration model.

A custom tokenizer recognises Latin alphanumeric words, Devanagari sequences and selected emoji ranges. Explicit Devanagari ranges preserve combining vowel marks that a naive word expression can lose. The displayed word count is operationally a token count and may include numbers or emojis. Sentence counting splits at sentence-ending punctuation; it is not a trained sentence-boundary detector.

## Language estimation

Each token is checked against manually authored Marathi and Hindi vocabularies, a shared-word set and its script. Recognised Marathi versus Hindi token counts determine a heuristic review label, with an ambiguous category for some ties or shared-script cases. Unrecognised Latin tokens remain English or unknown. The method can label a monolingual Indic review as an Indic-English candidate because it does not independently verify English presence.

## Morphology and part of speech

| Technique | Implementation | Interpretation |
| --- | --- | --- |
| Stemming | NLTK PorterStemmer on Latin tokens | Example: running -> run; Romanized Indic stems are not validated. |
| Lemmatization | WordNetLemmatizer with noun default | Example: cameras -> camera; not full contextual lemmatization. |
| POS tagging | NLTK English averaged perceptron on Latin tokens | English tags are inspectable; Hindi/Marathi accuracy is not established. |
| Pattern entities | Regular expressions for URLs and amounts | Example: Rs 250 -> AMOUNT; no trained person/location/organisation NER. |

## Operational examples

Input: "Service accha nahi hai. Food fresh hai." The tokenizer retains accha and nahi as separate tokens. The opinion stage can reverse the positive cue accha using postposed negation and separately detect fresh for Food. The pipeline inspector shows intermediate morphology and tagging independently of live opinion classification.

Preprocessing is shared conceptually across the application, but the supervised word TF-IDF comparison uses scikit-learn tokenization rather than the custom dashboard tokenizer. Stop words are removed for exploratory corpus vectors, not from the sentiment cue stream, so negation is retained during rule analysis.


<!-- PAGE BREAK -->

# Aspect sentiment and corpus modelling

## Explainable aspect sentiment algorithm

The live engine uses manually authored lexicons for eight categories: Food, Delivery, Service, Price, Quality, App, Battery and Camera. Reviews are split into clauses at punctuation and contrast words such as but, pan and lekin. Each recognised opinion cue is assigned to the nearest explicit aspect target within that clause; ties prefer the preceding target. No implicit aspect is inferred when no supported target is present.

Positive cues start at +1 and negative cues at -1. A recognised preceding intensifier increases magnitude to 1.5. Local negation before or shortly after a cue reverses its sign, with boundaries intended to reduce interference from neighbouring targets and opinions. Both positive and negative signs produce mixed sentiment. Mentions without assigned cues receive neutral. Overall sentiment uses all review cues and is computed separately from each aspect.

| Synthetic review fragment | Assigned aspect | Evidence and result |
| --- | --- | --- |
| Food khup chhan aahe | Food | chhan with khup: +1.5, positive |
| delivery late hoti | Delivery | late: -1, negative |
| Service accha nahi hai | Service | accha negated by nahi: -1, negative |

A cue score measures rule weight, not calibrated confidence. The clause "Food khup chhan aahe pan delivery late hoti" therefore yields overall mixed sentiment. Sarcasm, long-distance syntax, context-sensitive words, unusual spellings and implicit aspects remain known failure modes.

## TF IDF topics and semantic representations

Corpus keyword extraction fits word unigrams and bigrams with at most 3,000 features, then ranks terms by mean TF-IDF weight. LDA operates on count vectors with up to four topics, 15 iterations and seed 42; six high-weight words describe each topic. These exploratory word groups are not validated semantic categories [2].

Truncated SVD projects TF-IDF into up to 16 latent dimensions, depending on matrix size. Normalized vectors are compared by cosine similarity to display neighbouring reviews. These are corpus-level LSA document embeddings, not pretrained Word2Vec, FastText or transformer word embeddings.

## Bigram language model

Add-one smoothing estimates P(next | previous) = (bigram count + 1) / (previous-token context count + vocabulary size). Boundary and unknown tokens are included. Sequence log probability sums logarithms; perplexity is exp(-log probability / predicted-token count). The inspector trains on the current corpus, or the input itself if empty, so its perplexity is a teaching demonstration rather than held-out model quality.


<!-- PAGE BREAK -->

# Interface implementation and operation

## Five application sections

| Section | Purpose and user action |
| --- | --- |
| Overview | Inspect predicted sentiment totals, aspect distributions, LDA topics, TF-IDF words and review previews. Load synthetic fixtures or export analysis JSON. |
| Review analyzer | Enter one review in Roman or Devanagari scripts. Read aspect labels, overall polarity, clause evidence, negated cues and operational counts. |
| Dataset and labels | Import CSV, search and filter predictions/language estimates, browse 25 rows per page, and independently annotate overall sentiment and every explicit aspect. |
| NLP pipeline | Run an input through normalization, token language estimates, stemming, optional lemmas/POS, bigrams, pattern entities and corpus semantic neighbours. |
| Model evaluation | Inspect label readiness and compare the four baselines once prerequisites are met. Review confusion matrices, errors, aspect metrics and exportable experiment metadata. |

## Usability refinements

The fixed navigation originally allowed its lower content to fall outside a short browser viewport. It now has independent vertical scrolling and a compact layout for shorter desktop heights. Additional bottom spacing and wrapping keep long outputs accessible. Dataset pagination limits each page to 25 reviews, and section changes reset document scroll position.

Evaluation now displays imported real-review counts, labelled-review progress and per-class support. Run experiment stays unavailable until minimum label conditions appear satisfied; the server still validates normalized duplicates and conflicting labels. Export report remains disabled until an experiment exists. This explains missing results without encouraging invented labels or fabricated scores.

## Running the application

From D:/PROJECT/NLP_project, install requirements in a virtual environment and run python app.py. Open http://127.0.0.1:8765. NLTK resources may be installed separately for the English tagger and WordNet. Review collection additionally requires network access; analysis of an existing corpus operates locally.

## Storage and service boundaries

Imports are transactional and limited to 2,000 rows, 10,000 characters per review and an 8 MB HTTP request. Source metadata is user-supplied and not independently verified on import. The local service uses loopback binding, same-origin write checks and a restrictive content policy; it is not a production authentication or hosting solution. Exported labels and predictions should be archived separately to preserve research traceability.


<!-- PAGE BREAK -->

# Mapping to laboratory assignments

The mini project integrates the following techniques from BCS25PC15. Coverage describes the implemented code, not automatic equivalence to each exact standalone lab assignment. Dataset substitutions and partial tasks should be discussed with the assessor.

| Lab | Required task | Project mapping and coverage |
| --- | --- | --- |
| 1 | Scrape web data | Public Google Play collector with traceable sources and timestamps. Implemented. |
| 2 | HuffPost language detection counts tokenization | Analyzer and inspector provide estimates, counts and tokens on customer reviews. Technique covered; required news dataset is not used. |
| 3 | English stemming and WordNet lemmatization | Porter stems and WordNet noun lemmas in the pipeline. Implemented for English/Latin demonstration; resources required for WordNet. |
| 4 | POS embeddings and text classification | English POS inspector, LSA document embeddings, TF-IDF classifiers. Partial: classification is not POS-feature based and embeddings are document-level. |
| 5 | Named Entity Recognition | URL/amount patterns only. Partial: trained multilingual person/location/organisation NER is not implemented. |
| 6 | TF IDF | Corpus keyword weights plus word/character classifier features. Implemented. |
| 7 | N gram models | Bigram contexts and counts in the pipeline inspector. Implemented. |
| 8 | Sequence probability using N grams | Add-one bigram factors, log probability and demonstration perplexity. Implemented; no held-out LM evaluation. |
| 9 | LSI or LDA | Truncated-SVD LSA similarities and LDA topics. Implemented. |
| 10 | Sentiment emotions opinion mining topics | Aspect and overall polarity plus LDA. Partial: no separate emotion classifier such as joy/anger/sadness. |
| 11 | NLP pipeline mini project | Collection, storage, preprocessing, prediction, explanation, interface, labels and evaluation. Implemented. |

## Assessment evidence and submission scope

The project supplies source code, reproducible commands, synthetic sample inputs, original review provenance, an annotation guide and a test suite. The journal draft includes objectives, outcomes, theory, dataset description, sample output, conclusion and an assessor signature field. Final assessment should additionally include actual annotated-data results and screenshots of the student-run demonstration.

The exact standalone HuffPost assignment, full trained NER task, POS-based classification and emotion identification should not be claimed as fully completed by the current project. The honest contribution is an integrated, inspectable baseline with clear extension points.


<!-- PAGE BREAK -->

# Evaluation metrics and testing

## Baseline comparison and split design

The experiment compares majority-class prediction, the explainable rule baseline, word TF-IDF logistic regression and character TF-IDF logistic regression. Learned models predict overall review sentiment; live aspect analysis remains rule-based. Word features use unigrams/bigrams; character features use char_wb n-grams of lengths 3 to 5. Both use up to 20,000 features, sublinear term frequency, balanced class weights, 1,000 maximum iterations and seed 42.

Eligible data must contain at least 20 unique annotated non-demo reviews, two represented classes and at least four examples in every represented class. Normalized duplicate text is removed and conflicting overall labels are rejected. One stratified 70/30 train/test split is shared by all baselines. Vectorizers fit training text only. The report records train/test IDs, class support, errors and a dataset fingerprint.

| Metric | Definition or interpretation |
| --- | --- |
| Accuracy | Correct overall predictions / number of test reviews. |
| Precision and recall | TP/(TP+FP) and TP/(TP+FN), calculated per class. |
| F1 and macro F1 | 2PR/(P+R); macro F1 averages all four sentiment labels. Unsupported labels currently contribute zero. |
| Confusion matrix | Gold-label rows against predicted-label columns, with fixed label order. |
| Aspect extraction P R F1 | Micro-aggregated category overlap on test rows with nonempty gold aspect labels. |
| End to end aspect sentiment | Correctly detected gold aspects with correct polarity / all evaluated gold aspects. |

## Measured software results and unmeasured model results

All 16 regression/integration tests passed in the latest verification. They cover negation, contrast clauses, Devanagari tokens, mixed/neutral cases, input limits, corpus methods, bigram validity, transactional imports, deduplication, annotations, demo exclusion and reproducible splitting. Passing fixtures establishes tested software behavior, not 100 percent real-review accuracy.

Browser checks confirmed live evidence output, search, pagination, the annotation dialog, readiness guidance and seven pipeline panels. The bottom LSA panel was reachable after scrolling and the sidebar footer remained accessible. The most recent export-download check timed out, so completion of that browser download was not verified in that pass.

No real-data accuracy, F1, per-language performance or annotator agreement is available because there are no independent real-review labels. Aspect evaluation currently skips rows with empty gold dictionaries, so false positives on genuinely aspect-free reviews are not fully assessed. Near-duplicate/source leakage and test-informed lexicon tuning also require a separate audit.


<!-- PAGE BREAK -->

# Findings limitations and references

## Observed corpus predictions

A rule-engine audit on 205 unique real reviews, excluding the synthetic fixtures, produced 110 positive, 14 negative, 80 neutral and 1 mixed prediction. At least one supported explicit aspect was detected in 55 reviews and none in 150. These counts describe predictions and coverage; they are not correctness or customer-satisfaction measurements.

Predicted review-level aspect mentions were App 24, Food 17, Service 16, Delivery 9, Price 5, Quality 3, Camera 1 and Battery 0. Multiple aspects can occur in one review. Limited aspect coverage and the unexpected cross-domain Camera mention are reasons to curate data and inspect errors, rather than to assume strong multilingual performance.

## Limitations and future work

Priority improvements are manually verified code-mixed data, independent exhaustive aspect annotation, a second annotator on a shared subset, agreement measurement and a locked test set. Final analysis should break results down by language, script and aspect, and audit near duplicates and source/product grouping. Fix the aspect-free-row evaluation limitation before making extraction claims.

Subsequent model extensions may include validated transliteration, context-sensitive aspect attribution, multilingual NER, emotion classification and a trained multilingual ABSA model. Each extension should be compared against the existing baseline on unchanged held-out data. A larger corpus and more complex model alone do not establish improved performance.

## Conclusion

BhashaLens delivers a local end-to-end NLP workbench with explainable aspect opinions, syllabus demonstrations, traceable review collection and an evaluation framework. It provides a practical basis for the laboratory mini project. Its completed result is the implementation and tested workflow; real-world effectiveness remains an empirical question requiring verified languages and independent labels.

## References

[1] JoMingyu. Google Play Scraper for Python. Collector API and usage documentation. https://github.com/JoMingyu/google-play-scraper

[2] scikit-learn. TF-IDF vectorizer and text topic extraction documentation. https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html

[3] NLTK Project. Natural Language Toolkit documentation. https://www.nltk.org/

[4] Patwa et al. 2020. SemEval 2020 Task 9 Overview of Sentiment Analysis of Code Mixed Tweets. https://aclanthology.org/2020.semeval-1.100/ This is background research, not the source of the project review corpus.

[5] Project evidence: requirements.txt, nlp.py, experiments.py, storage.py, scripts/collect_reviews.py, data/collection_manifest.json and tests/test_project.py. External documentation checked 22 October 2026.


<!-- PAGE BREAK -->
