# Methodology and intellectual-property boundary

## Versioned method identity

- Method ID: `bcm-geo-evidence-action-retest`
- Initial method version: `1.0.0`
- Owner label: `BCM`
- Objective: improve externally observable search visibility, AI mentions, citations, recommendations, and attributable conversions without promoting implementation signals into outcome claims.

This identifier is a technical registry and provenance mechanism. It is not a claim that a patent, trademark, or copyright registration has been granted.

Every evidence bundle should carry the method ID, method version, evidence-contract version, and the non-causality boundary. This makes later recomputation explicit even when the software package changes.

## Independent implementation

BCM GEO was designed and implemented independently. Public third-party projects may be reviewed to understand the problem landscape, but their source code, prompt text, documentation expression, scoring formula, and visual assets are not imported.

Conceptual reviews recorded for method development:

- `yaojingang/GEOHub`: evidence objects, replayable work, explicit missing states, and offline recomputation were useful problem-framing ideas.
- `zubair-trabzada/geo-seo-claude`: modular audit routing, client-readable reporting, and periodic comparison were useful product-organization ideas.

BCM GEO differs materially by requiring real answer evidence, matched prompt-panel retests, official search readback, multi-site intent ownership, explicit negative/null states, production rollback evidence, and a claim gate that separates observed change from causality.

## Public layer

The open package may include:

- evidence and action field definitions;
- versioned JSON Schemas;
- generic deterministic validators and aggregators;
- synthetic examples;
- public documentation of state and claim boundaries.

The public layer must not contain real customer inventories, internal domains, production paths, account identifiers, credentials, browser state, private thresholds, or confidential strategies.

## Protected layer

The production system retains:

- customer and site data;
- production connectors and operational orchestration;
- private provider adapters and site-specific strategy;
- internal thresholds, commercial rules, and release records;
- passwords, tokens, cookies, keys, server paths, and security controls.

Publishing the public method does not disclose the protected implementation or grant access to production data.

## Claim ownership and defensibility

Each material claim must state its type, evidence references, confidence, limitations, and highest verified outcome state. A change in an internal diagnostic score is not itself a search or AI outcome. A matched baseline/retest establishes an observed change, not causality. A causal estimate additionally requires an identified design, control reference, and assumptions.

Use `scripts/geo_claim_gate.py` and `schemas/outcome-claim.schema.json` before publishing a result summary.
