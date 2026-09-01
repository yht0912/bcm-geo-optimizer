# Production Release Gate

## Required receipt

For every authorized production change, record:

- target property and exact URLs/files;
- change identifier and timestamp;
- pre-change backup or reversible state;
- changed files and hashes when appropriate;
- syntax/build/test result;
- origin response;
- public edge response;
- redirect, canonical, robots, sitemap, structured data, and rendered DOM checks as relevant;
- monitoring window and rollback path;
- official platform submission/readback receipts, separately labeled;
- unresolved risks.

## Verification layers

1. **Configured** — settings or credentials exist.
2. **Authorized** — identity can access the resource.
3. **Verified** — platform ownership check passed.
4. **Readback** — a real API/export returns current resource data.
5. **Submitted** — URL or sitemap request was accepted.
6. **Observed effect** — crawl, index, rank, answer, visit, or conversion evidence exists.

Never use a lower layer as proof of a higher one.

## Rollback triggers

Define explicit rollback conditions, such as:

- elevated 4xx/5xx rate;
- broken rendering or conversion path;
- canonical or robots regression;
- structured data invalidation;
- severe performance regression;
- unintended disclosure;
- duplicated or misleading claims.

## Secret handling

Credentials belong in a secret store or environment-specific encrypted configuration. They must not enter source control, examples, issue logs, screenshots, reports, or public release archives.
