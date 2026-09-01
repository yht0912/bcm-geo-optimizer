# Data Interoperability and Privacy Export

## Canonical formats

Use the bundled JSON Schemas when moving evidence between an agent, spreadsheet, platform export, or analysis pipeline:

- `schemas/evidence-bundle.schema.json`
- `schemas/action-bundle.schema.json`

The Python tools remain the executable validation authority for v1.1. The schemas make the contract portable; they do not validate whether an observation is truthful.

## CSV import

The importer accepts UTF-8 or UTF-8-with-BOM CSV and rejects unknown columns by default. This reduces accidental export of notes, contact data, or platform credentials.

Required columns:

`observation_id,panel_version,prompt_id,prompt_hash,provider,model,locale,region,observed_at,status,brand,source_urls,evidence_excerpt,limitations`

Optional column:

`capture_ref`

Use `|` between multiple source URLs. Do not put the prompt text, answer body, cookies, tokens, user profiles, or raw browser captures in this transport format.

```bash
python3 scripts/geo_csv_import.py \
  --input observations.csv \
  --study-id study-2026-q3 \
  --purpose "Matched baseline panel" \
  --output evidence.json
```

The importer records the input SHA-256 for provenance and validates every observation before writing JSON.

## Privacy export

The privacy exporter uses HMAC-SHA-256 pseudonyms. It transforms observation IDs, panel IDs, prompt IDs, brand names, source URLs, evidence excerpts, and capture references while preserving provider, model, locale, region, status, and prompt hash for matched analysis.

Provide a salt through an environment variable. Use the same salt only when two exports must remain matchable. Keep it out of source control and reports.

```bash
export GEO_ANONYMIZATION_SALT='use-a-private-random-value-of-16-or-more-bytes'
python3 scripts/geo_privacy_export.py \
  --input evidence.json \
  --time-granularity day \
  --output evidence-public.json
```

Time options:

- `exact`: retain the original timestamp;
- `day`: retain the date and remove time/offset;
- `month`: retain only the month;
- `none`: replace all timestamps with a fixed value.

## Residual risk

This is a **de-identification aid, not a guarantee of anonymity**. Provider, locale, region, status pattern, sample size, prompt hash, and collection timing can still support re-identification when combined with outside knowledge.

Before sharing an export:

1. review the transformed file manually;
2. reduce time/region precision when not needed;
3. remove rare observations or small cohorts when they identify a customer;
4. do not publish the HMAC salt;
5. confirm that disclosure is allowed by contracts, privacy law, and provider terms;
6. keep raw captures and credentials outside the export.

## Compatibility policy

- Patch versions may tighten validation without changing required fields.
- Minor versions may add optional fields or new schemas.
- Breaking field or semantic changes require a major version.
- Tools should preserve unknown top-level metadata only when explicitly documented; the privacy exporter intentionally drops it.
