# Contributing

Contributions that improve evidence quality, international coverage, production safety, or reproducibility are welcome.

## Before opening a pull request

1. Keep the implementation dependency-free unless a strong, documented need exists.
2. Add or update tests for behavior changes.
3. Use synthetic or fully anonymized examples.
4. Preserve unavailable, null, negative, and conflicting observations.
5. Do not claim ranking, recommendation, traffic, or conversion effects without reproducible evidence.
6. Do not add credentials, customer inventories, private paths, internal domains, cookies, or session captures.
7. Run:

   ```bash
   python3 scripts/validate_package.py
   python3 -m unittest discover -s tests -v
   ```

## Scope

Good contributions include:

- clearer evidence contracts;
- additional deterministic measurements;
- safe engine-specific verification guidance;
- locale and multi-site governance improvements;
- accessibility and documentation improvements;
- evaluation cases that catch overclaiming.

Bulk scraping, fabricated engagement, fake citations, ranking manipulation, provider circumvention, and unverifiable benchmark claims are out of scope.
