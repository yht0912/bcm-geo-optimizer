# Contributing

Issues, reproducible test cases, localization feedback, and design discussion
that improve evidence quality, international coverage, production safety, or
reproducibility are welcome. Until the maintainer publishes a legally reviewed
contribution agreement and explicit acceptance process, unsolicited external
source-code contributions are not merged. This keeps the copyright chain and
outbound license unambiguous.

## Before opening a pull request

1. Open an issue before preparing implementation code.
2. Do not copy third-party code, prompts, formulas, documentation expression,
   tests, or assets into a proposal.
3. Identify every external source, license, employer, client, or contract that
   could affect a proposed contribution.
4. Keep the implementation dependency-free unless a strong, documented need exists.
5. Add or update tests for behavior changes.
6. Use synthetic or fully anonymized examples.
7. Preserve unavailable, null, negative, and conflicting observations.
8. Do not claim ranking, recommendation, traffic, or conversion effects without reproducible evidence.
9. Do not add credentials, customer inventories, private paths, internal domains, cookies, or session captures.
10. Run:

   ```bash
   python3 scripts/validate_package.py
   python3 -m unittest discover -s tests -v
   ```

Sending code without an accepted contribution agreement does not transfer
copyright or require the maintainers to review or merge it.

## Scope

Good contributions include:

- clearer evidence contracts;
- additional deterministic measurements;
- safe engine-specific verification guidance;
- locale and multi-site governance improvements;
- accessibility and documentation improvements;
- evaluation cases that catch overclaiming.

Bulk scraping, fabricated engagement, fake citations, ranking manipulation, provider circumvention, and unverifiable benchmark claims are out of scope.
