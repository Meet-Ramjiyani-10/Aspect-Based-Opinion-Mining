# Ground-truth annotation protocol

## Unit and population

One customer review is one item. Target naturally occurring Marathi-English or Hindi-English customer reviews in Roman, Devanagari, or mixed scripts. Retain English-only examples as a separately reported control group, not as substitutes for code-mixed coverage.

Record source, URL or source identifier, collection date, retrieval locale, and manual language label. Remove personal identifiers and copied promotional content. Never infer actual language solely from the requested locale.

## Overall sentiment

| Label | Decision |
| --- | --- |
| positive | Clear favorable evaluation, no substantive unfavorable opinion |
| negative | Clear unfavorable evaluation, no substantive favorable opinion |
| neutral | Descriptive content with no clear evaluation |
| mixed | Both favorable and unfavorable opinions, even if about different aspects |

Sarcasm is labelled by intended meaning when reasonably clear and flagged in an external adjudication log. Ambiguous items should be adjudicated or excluded with recorded reasons. Do not guess intended language or polarity silently.

## Aspect inventory

Food: taste, freshness, food temperature, food item quality. Delivery: rider/courier behavior, delay, delivery execution. Service: staff/support behavior and service interactions. Price: affordability, value, cost. Quality: generic product/material/build/packaging. App: application usability, bugs, payments/refunds. Battery: charging, endurance. Camera: photographs and image quality.

Assign every explicit aspect, including neutral mentions. If an item discusses a genuine aspect outside the inventory, record it in the adjudication log; do not force it into an unrelated category. Interpret context: cold food is generally negative, while cold drinks can be positive. The rule baseline cannot resolve all such cases.

The initial inventory is cross-domain. For a focused food-delivery study, predeclare that domain and analyze the relevant categories separately. Do not compare camera-review and restaurant-review results as if domains were interchangeable.

Examples (synthetic):

| Text | Overall | Aspect labels |
| --- | --- | --- |
| Food chhan aahe pan delivery late hoti. | mixed | Food=positive, Delivery=negative |
| Service accha nahi hai. | negative | Service=negative |
| Delivery arrived at 4 pm. | neutral | Delivery=neutral |
| Camera mast hai but battery poor hai. | mixed | Camera=positive, Battery=negative |

## Recommended procedure

1. Freeze the codebook and aspect definitions before annotation.
2. Independently double-label a 50-review pilot without viewing predictions.
3. Resolve disagreements and revise the codebook before freezing the final test set.
4. Double-label at least 20% of the final corpus. Measure Cohen's kappa for overall sentiment and agreement on aspect presence/polarity. Record actual values; none are supplied by this project.
5. Keep product/source groups and near-duplicate variants in one partition. The built-in splitter removes normalized duplicates, but does not automatically group by product/source.
6. Report sample sizes by language, script, domain, sentiment, and aspect. Report disagreement and exclusion counts.
7. Use the dashboard to save adjudicated labels. Its annotation editor does not preload predictions as gold.

## Dataset card to complete

Collection period: __________
Sources and permission/usage basis: __________
Raw count / deduplicated count / eligible code-mixed count: __________
Hindi-English / Marathi-English / other language counts: __________
Script distribution: __________
Annotators and competence in languages: __________
Agreement method / score / adjudication count: __________
Split construction and leakage audit: __________
Intended use and known exclusions: __________

Ratings may support exploratory comparisons, but must not replace independently annotated aspect polarity. Synthetic examples and rule predictions must never be reported as real human ground truth.
