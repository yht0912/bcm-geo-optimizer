# Evidence Contract

## Purpose

This contract prevents implementation activity from being reported as recommendation success.

## Observation schema

Each AI-answer observation must contain:

| Field | Requirement |
|---|---|
| `observation_id` | Unique, stable identifier |
| `panel_version` | Version of the prompt panel |
| `prompt_id` | Stable prompt identifier |
| `prompt_hash` | SHA-256 of normalized prompt text |
| `provider` | Observed answer provider |
| `model` | Model name when visible, otherwise `unknown` |
| `locale` | BCP 47-style locale or documented equivalent |
| `region` | Country/market code or `unknown` |
| `observed_at` | ISO 8601 timestamp with timezone |
| `status` | One allowed outcome state |
| `brand` | Brand being evaluated |
| `source_urls` | URLs actually shown in the answer |
| `evidence_excerpt` | Short excerpt supporting the assigned state |
| `capture_ref` | Optional local or governed evidence reference |
| `limitations` | Known collection or interpretation limits |

Allowed `status` values:

- `unavailable`: no valid answer could be observed;
- `not_mentioned`: valid answer, brand absent;
- `mentioned`: brand appears without a recommendation or qualifying source citation;
- `cited`: answer presents a source URL supporting the brand or its claim;
- `recommended`: answer explicitly selects, shortlists, or advises considering the brand;
- `negative`: answer explicitly warns against, rejects, or materially criticizes the brand.

`recommended` and `negative` can also be cited. Record source URLs even though status is a single primary state.

## Aggregation rules

- Denominator for visibility rates: valid observations excluding `unavailable`.
- Mention rate: `mentioned + cited + recommended + negative` divided by valid observations.
- Citation rate: observations with at least one qualifying source URL divided by valid observations.
- Recommendation rate: `recommended` divided by valid observations.
- Negative rate: `negative` divided by valid observations.
- Always report `n`, missing/unavailable count, panel version, and coverage.
- Use Wilson score intervals for binomial rates.

## Matched comparison rules

Compare only keys that match on:

`prompt_id + provider + locale + region`

Also require equal `prompt_hash` and compatible panel versions. A model change is allowed only when disclosed; report model drift separately.

If matched coverage is below the configured threshold, label the comparison `insufficient_matched_coverage`. Never repair missing observations by inventing values.

## Claim boundary

Use the strongest supportable wording:

- “Observed in 3 of 20 valid answers” is acceptable.
- “Recommendation rate rose 10 percentage points in the matched panel” is acceptable.
- “The change caused a 10-point rise” is not acceptable without a causal design.
- “AI platforms recommend the brand” is not acceptable from a single answer.

## Storage and privacy

Store credentials separately from evidence. Redact personal data, session data, internal URLs, and sensitive customer identifiers before sharing or publishing. Give captures a retention policy and access scope.
