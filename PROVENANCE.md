# Provenance record

## Independent implementation

BCM GEO Outcome Engine was designed and implemented as an independent,
outcome-first method. Its code, schema expression, prompts/instructions,
examples, tests, and documentation were not imported from another GEO project.

AI coding tools may assist implementation. A release nevertheless requires
human selection of requirements, review of every published file, deterministic
tests, security/origin validation, and an approved Git commit. A chat transcript
alone is not release evidence.

## Conceptual research references

Two public projects were reviewed only for product-landscape understanding:

- `yaojingang/GEOHub` at fixed audit commit
  `2210f7f22153cfdf721905c2ac86318db97401b1`;
- `zubair-trabzada/geo-seo-claude` at fixed audit commit
  `a58098a839e2c97df7ae89191b3021fa9e0f88c3`.

No source code, prompt wording, scoring formula, documentation expression,
visual asset, or sample customer material was imported. The conceptual review
and BCM-specific differences are documented in
`references/methodology-and-ip.md`.

On 2026-09-01, a read-only comparison of 35 textual files in this repository
against both fixed commits found zero identical files and zero matching
seven-line sequences after comments, blank lines, short lines, and whitespace
differences were removed. Dependencies, build output, release output, and Git
metadata were excluded. This is engineering provenance evidence, not a legal
infringement opinion or a substitute for forensic expert analysis.

## Dependency boundary

Runtime scripts use only the Python standard library and local BCM modules. The
package does not vendor third-party code. GitHub Actions and a Python runtime
are development/execution tools, not redistributed runtime libraries. The
validation script checks the runtime import boundary before release.

## Release record

Every release must retain the Git commit, package SHA-256, test result,
`ORIGIN.json`, license/copyright notices, and public readback. Releases are
built from a clean commit, not directly from a production directory.
