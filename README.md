# BCM GEO Outcome Engine

[![CI](https://github.com/yht0912/bcm-geo-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/yht0912/bcm-geo-optimizer/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-1.2.0-2563eb)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Zero dependencies](https://img.shields.io/badge/runtime-dependencies-0-16a34a)](scripts)

An outcome-first **Generative Engine Optimization (GEO) Skill** for AI citations, recommendations, search visibility, and attributable growth.

BCM GEO Outcome Engine helps Codex, Claude, and compatible agents answer the question most GEO tools avoid:

> Did the work produce an externally observable mention, citation, recommendation, qualified visit, lead, or sale?

[中文说明](README.zh-CN.md) · [Skill instructions](SKILL.md) · [Evidence contract](references/evidence-contract.md)

## Why this Skill exists

Technical checks matter, but they are not the outcome. A successful crawl, sitemap submission, schema deployment, audit score, or `llms.txt` response does not prove that an AI system cited or recommended a brand.

This Skill enforces a verifiable evidence ladder:

```text
reachable -> discovered -> crawled -> indexed -> ranked
          -> mentioned -> cited -> recommended -> converted
```

It reports the highest observed state without skipping steps.

## What makes it different

- **Recommendation outcome loop:** baseline, diagnose, release, discovery window, matched retest, attribution.
- **No self-scoring as success:** internal readiness can guide work but cannot prove external visibility.
- **Matched prompt measurement:** provider, locale, region, and exact prompt hash must align.
- **Honest uncertainty:** unavailable, negative, missing, and conflicting evidence remain visible.
- **Search + AI coverage:** Google, Bing, Baidu, ChatGPT, Claude, Gemini, Copilot, Perplexity, and other observable systems.
- **Multi-site governance:** one preferred property/page per intent, with cannibalization controls.
- **Production safety:** backup, origin, edge, rendered DOM, receipt, monitoring, and rollback checks.
- **Conversion continuity:** recommendation visibility connects to qualified visits and business outcomes only when tracking is verified.
- **Offline deterministic tools:** no API keys, no hidden network calls, and zero runtime dependencies.
- **Portable evidence data:** strict CSV import, versioned JSON Schemas, and privacy-aware case export.
- **Claim publication gate:** implementation, outcome, observed-change, and causal claims have different evidence requirements.
- **Multilingual integrity:** locale-aware diagnostics replace universal English-only word-count or capitalization heuristics.

## Install

Clone the repository into your shared agent skills directory:

```bash
git clone https://github.com/yht0912/bcm-geo-optimizer.git \
  "$HOME/.agents/skills/bcm-geo-optimizer"
```

If your agent reads a different skills directory, link the shared copy:

```bash
ln -s "$HOME/.agents/skills/bcm-geo-optimizer" \
  "$HOME/.codex/skills/bcm-geo-optimizer"
```

Start a new agent session after installation so the Skill catalog refreshes.

## Use

Ask naturally or invoke the Skill explicitly:

```text
Use $bcm-geo-optimizer to establish a baseline across ChatGPT, Gemini,
Perplexity, Google, and Bing, then produce an evidence-backed 90-day plan.
```

```text
Use $bcm-geo-optimizer to compare our baseline and retest prompt panels.
Report only matched observations and do not claim causality.
```

The Skill first defines the commercial decision and stable prompt panel, then diagnoses the highest limiting layer before proposing work.

## Evidence tools

Create a scorecard from observed evidence:

```bash
python3 scripts/geo_outcome_scorecard.py \
  --input examples/evidence-sample.json \
  --output /tmp/geo-scorecard.json
```

Compare a baseline and retest:

```bash
python3 scripts/geo_delta_compare.py \
  --baseline examples/evidence-baseline.json \
  --retest examples/evidence-retest.json \
  --output /tmp/geo-delta.json
```

Build a transparent, constraint-first action queue:

```bash
python3 scripts/geo_action_prioritizer.py \
  --input examples/actions-sample.json \
  --output /tmp/geo-action-queue.json
```

Import a spreadsheet export without accepting unknown columns:

```bash
python3 scripts/geo_csv_import.py \
  --input examples/evidence-sample.csv \
  --study-id example-study \
  --purpose "Synthetic import check" \
  --output /tmp/geo-evidence.json
```

Create a deterministic, de-identified review copy:

```bash
export GEO_ANONYMIZATION_SALT='use-a-private-random-value-of-16-or-more-bytes'
python3 scripts/geo_privacy_export.py \
  --input /tmp/geo-evidence.json \
  --time-granularity day \
  --output /tmp/geo-evidence-public.json
```

Gate outcome claims before publication:

```bash
python3 scripts/geo_claim_gate.py \
  --input examples/outcome-claims-sample.json \
  --output /tmp/geo-claim-gate.json \
  --strict
```

The tools validate supplied observations and calculate transparent rates with Wilson 95% intervals. They do not browse, invent evidence, or attribute causality.

The privacy export reduces disclosure risk but does not guarantee anonymity. Review residual risks before sharing. See [data interoperability and privacy export](references/data-interoperability.md).

## Evidence input

Each observation includes a stable prompt ID/hash, provider, model, locale, region, timestamp, outcome state, source URLs, evidence excerpt, and limitations. See the full [evidence contract](references/evidence-contract.md).

Allowed primary states:

- `unavailable`
- `not_mentioned`
- `mentioned`
- `cited`
- `recommended`
- `negative`

Examples are synthetic and use `example.com`; they are not provider benchmarks.

Portable contracts:

- [Evidence bundle JSON Schema](schemas/evidence-bundle.schema.json)
- [Action bundle JSON Schema](schemas/action-bundle.schema.json)
- [Outcome claim JSON Schema](schemas/outcome-claim.schema.json)

## Verify the package

```bash
python3 scripts/validate_package.py
python3 -m unittest discover -s tests -v
```

CI runs package validation, unit tests, and both example workflows on supported Python versions.

## Design principles

1. Real answers and official readback outrank internal scores.
2. Implementation receipts and outcome evidence are separate.
3. Changes must map to an observed gap and acceptance check.
4. Small panels are directional and always report sample size.
5. Causal claims require a causal design.
6. GEO must help a real user make a better decision.
7. Credentials and customer data never belong in the Skill or evidence examples.

## Independent implementation

This repository is an original implementation built from first principles around outcome measurement, production verification, and business attribution. It does not include source code, prompt text, scoring formulas, documentation text, or assets copied from other GEO projects. See the registered [methodology and intellectual-property boundary](references/methodology-and-ip.md).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for pull requests and [SECURITY.md](SECURITY.md) for private vulnerability reporting. Do not submit credentials, private customer data, live session captures, or unverifiable recommendation claims.

## License

BCM's original public implementation is licensed under [MIT](LICENSE).
Copyright remains with 南昌包参谋品牌策划有限公司; the license does not include
BCM trademarks, production services, credentials, customer data, or private
strategy. See [Ownership](OWNERSHIP.md), [Provenance](PROVENANCE.md),
[third-party notices](THIRD_PARTY_NOTICES.md), and
[trademark policy](TRADEMARKS.md).
