# Constraint-first Action Model

## Purpose

The action queue chooses what to do first without pretending to predict rankings or recommendations.

## Ordering logic

Actions are sorted lexicographically by observable planning attributes:

1. priority class: `P0`, `P1`, `P2`, `P3`;
2. limiting layer: access, discovery, retrieval, entity, answerability, corroboration, recommendation fit, conversion;
3. stronger direct evidence;
4. greater expected impact and affected reach;
5. lower effort and risk;
6. greater reversibility;
7. stable action ID as a deterministic tie-breaker.

This deliberately avoids a composite “GEO score.” A single number would hide why an action moved and could be mistaken for outcome evidence.

## Required action fields

| Field | Meaning |
|---|---|
| `action_id` | Stable unique identifier |
| `priority_class` | P0–P3 classification |
| `limiting_layer` | Highest observed layer affected |
| `observed_gap` | Specific problem linked to evidence |
| `evidence_ref` | Governed reference to that evidence |
| `evidence_strength` | 0–1 confidence in the observed gap |
| `impact` | 1–5 expected outcome relevance |
| `reach` | 1–5 affected intent/page/site scope |
| `effort` | 1–5 relative implementation effort |
| `risk` | 1–5 production/compliance/reputation risk |
| `reversibility` | 1–5 ease of safe rollback |
| `expected_state` | Next evidence-ladder state sought |
| `acceptance_check` | Direct test that closes the action |

## Evidence strength guide

- `1.0`: direct reproducible observation or official readback;
- `0.75`: strong consistent evidence with a known limitation;
- `0.5`: plausible but incomplete or indirect evidence;
- `0.25`: hypothesis requiring validation;
- `0.0`: unsupported idea; keep out of the committed queue.

Inputs remain operator judgments. Preserve their source and owner. Re-run the queue when evidence or constraints change.
