# Presentation and viva preparation

## Suggested eight-minute demonstration

1. **Problem (45 seconds):** Show a review praising food and criticizing delivery. Explain why a star rating or single polarity misses useful information.
2. **Language challenge (45 seconds):** Show Romanized Marathi, Hindi in Devanagari, and English in one workflow. Explain shared vocabulary and script ambiguity.
3. **Live analysis (90 seconds):** Analyze a contrast example, then a negation example. Show the clause and cue evidence. Show a failed sarcasm or implicit-aspect example candidly.
4. **Corpus analytics (60 seconds):** Show aspect sentiment bars, LDA topics, and TF-IDF terms. Distinguish topic discovery from supervised sentiment prediction.
5. **Data protocol (60 seconds):** Show the collector's source columns and a human annotation. State actual source/count/language/annotation agreement numbers only after collecting them.
6. **Evaluation (90 seconds):** Compare the four baselines on one test split. Explain macro-F1, confusion matrices, held-out fitting, demo exclusion, and dataset fingerprint.
7. **Pipeline and conclusion (90 seconds):** Inspect morphology, POS limitations, bigrams, and LSA. Explain known failure modes and the next measurable improvement.

## Questions and answers

**What is new compared with ordinary sentiment analysis?**
The app associates distinct sentiment with explicit aspects, preserves evidence, and supports actual code-mixed data collection and independent annotations. The rule algorithm itself is a baseline, not a claim of novel state-of-the-art research.

**Why character TF-IDF?**
Character n-grams can share features across spelling variants and Romanized words without requiring a full word vocabulary. Whether that improves results is tested on held-out data, not assumed.

**Why not just use a translation API or an LLM?**
This implementation supports local reproducibility, inspectable decision rules, and low compute requirements. Translation or a multilingual transformer could be added as a separately evaluated model; neither is currently used.

**Is this a trained multilingual ABSA model?**
No. Live aspect extraction and sentiment attribution are rules. The experiment fits supervised overall-sentiment classifiers from independent labels. LDA and SVD are fitted unsupervised corpus models.

**What does neutral mean?**
In human labels, no evaluative stance. In the rule engine, no assigned polarity cue or zero net polarity without opposing signs. The distinction between actual neutrality and missed cues is a limitation to discuss.

**How do you avoid data leakage?**
Exclude demo rows, normalize/deduplicate before splitting, use one fixed split, and fit vectorizers on training text only. Audit near duplicates, product/source grouping, and test-informed lexicon tuning separately; these are not automatically solved.

**Does a 5-star rating mean every aspect is positive?**
No. It is review-level metadata and can disagree with text or contain multiple aspect polarities. Gold aspect labels must be independently assigned.

**Are TF-IDF terms explanations of the live classifier?**
No. The keyword cloud describes corpus weighting. Live rule explanations show aspect mentions, opinion cues, and negation. The separate learned classifiers need separate feature-level explanation if extended.

**What are the embeddings?**
TF-IDF document vectors projected through truncated SVD (latent semantic analysis), compared with cosine similarity. They are not pretrained transformer word embeddings.

**What are the language identification limits?**
Devanagari is shared by Marathi and Hindi, and Romanized spellings vary. The engine recognizes selected tokens and reports ambiguity. It is not a validated language classifier.

**What is not implemented?**
Learned multilingual NER, a dedicated emotion classifier, contextual embeddings, general transliteration, implicit aspects, and production deployment. The course mapping explicitly marks these limits.

**What would most strengthen the final submission?**
A real, documented, independently annotated code-mixed corpus; agreement measurements; a locked test set; per-language/domain scores; and an error-driven extension evaluated against this baseline. Visual polish complements these results but cannot replace them.
