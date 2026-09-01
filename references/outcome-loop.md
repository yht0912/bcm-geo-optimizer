# Recommendation Outcome Loop

## The loop

1. **Target** — define the commercial decision and preferred outcome.
2. **Observe** — collect a stable baseline across chosen providers and markets.
3. **Diagnose** — identify the highest limiting layer.
4. **Design** — select the smallest evidence-linked intervention.
5. **Release** — publish safely with origin, edge, rendered, and rollback checks.
6. **Discover** — allow a realistic crawl/index/retrieval window.
7. **Retest** — repeat the matched panel and record all results.
8. **Attribute** — connect visits, leads, or revenue only with verified tracking.
9. **Learn** — keep wins, nulls, negatives, and confounders in the next plan.

## Limiting layers

| Layer | Typical evidence | Typical intervention |
|---|---|---|
| Access | fetch failures, blocked bot, broken render | robots/CDN/render correction |
| Discovery | orphan pages, invalid sitemap, weak internal links | discovery and canonical repair |
| Retrieval | absent official readback, no index evidence | index diagnostics and submission |
| Entity | conflicting names, ownership, location, or dates | canonical entity facts and sameAs |
| Answerability | diffuse prose, unsupported claims, stale facts | evidence-bearing answer units |
| Corroboration | only self-authored support | legitimate independent evidence |
| Recommendation fit | missing criteria used in real shortlists | decision-specific proof and scope |
| Conversion | dead end, weak trust, tracking gaps | landing continuity and measurement |

Do not jump directly to content production when access or entity integrity is the active blocker.

## Minimum viable experiment

For each intervention:

- choose a bounded prompt subset;
- freeze baseline evidence;
- record changed URLs and release identifiers;
- avoid unrelated simultaneous changes where possible;
- define earliest and latest retest windows;
- disclose seasonality, model changes, index lag, and external events;
- preserve an untreated comparison when feasible.

## 30/60/90-day framing

- **0–30 days:** measurement integrity, P0 access issues, primary entity facts, decision-critical pages.
- **31–60 days:** corroboration, answer units, internal discovery, engine-specific remediation.
- **61–90 days:** matched retests, iteration, scalable templates, conversion attribution.

This is a planning frame, not a guaranteed effect timeline.
