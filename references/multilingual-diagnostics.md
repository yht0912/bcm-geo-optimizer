# Multilingual diagnostic policy

Do not apply English word-count, pronoun, capitalization, currency, or sentence-boundary heuristics as universal GEO laws.

For every content diagnostic:

1. record the document and query locale;
2. select locale-aware tokenization and sentence rules;
3. treat fixed passage-length ranges as hypotheses, not recommendation probabilities;
4. evaluate whether a fact unit is self-contained, sourced, current, scoped, and useful to the decision;
5. keep the diagnostic separate from observed AI answer outcomes.

Chinese content should be evaluated using character/word segmentation suited to Chinese, not whitespace word counts. Local intent must preserve city, service area, eligibility, and current factual constraints. Translated or localized pages should be compared within the same locale and region.

When a locale-specific analyzer is unavailable, return `unknown` for unsupported measures and continue with language-agnostic checks such as public accessibility, source linkage, dates, author/entity identity, canonical URLs, structured facts, and real answer evidence.
