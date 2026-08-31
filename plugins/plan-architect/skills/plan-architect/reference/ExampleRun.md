# Worked Example: Redis-backed Rate Limiter

This picks up exactly where `spec-architect`'s worked example stops. That run ended with a
validated `design.md` and `validation.md` for a two-component rate limiter; this one turns
them into a delivery order. Criterion ids (`R1.1`, `R1.2`, `R2.1`) and component names carry
over unchanged — that is the whole point of the handoff.

This is the fixture the validator is tested against — running `validate_plan.py` over these
three documents produces a **PASS**.

## inventory.md

```markdown
# Delivery Inventory

## Sources

- [D1] `design.md` — spec-architect output, validation passed
- [D2] `requirements.md` — criterion ids carried over unchanged

## Components

| Component | Responsibility | Exists |
|---|---|---|
| `RateLimiter` | Enforces per-key request rates | no |
| `RedisStore` | Persists counters with TTL | no |

## Criteria

## R1 — Rate limiting

1. WHEN a request arrives, the **`RateLimiter`** SHALL compare the count to the limit.
2. WHEN the limit is exceeded, the **`RateLimiter`** SHALL reject with 429.

## R2 — Outage handling

1. WHEN Redis is unreachable, the **`RedisStore`** SHALL fail open.

## Risks

- [K1] Fail-open is specified but unexercised — [D1] gives `bump()` a `None` return for an
  unreachable store, and nothing yet proves the caller honours it.
```

## spine.md

```markdown
# Walking Skeleton

## The thinnest path

One request, one key, one counter: the limiter asks the store for a count and returns a
decision. That exercises the whole round trip — request in, Redis touched, answer out —
without window arithmetic, outage handling, or 429 formatting. Those are thickenings of a
path that already works, not prerequisites for it.

## Spine

| Component | Role on the path |
|---|---|
| `RateLimiter` | entry — receives the request and returns the decision |
| `RedisStore` | exit — the counter whose value the decision reads |

## First demo

Send one request for a key. Watch a counter appear in Redis and an allowed response come
back. Nothing is stubbed: the decision is real, it is just always the same decision.

## Deferred to later milestones

- Rejecting at the limit — the skeleton reads the count and allows regardless
- Fail-open behaviour when the store is unreachable
```

## plan.md

```markdown
# Execution Plan

## Approach

M1 walks the spine end to end with the thinnest behaviour that is still real, so the Redis
round trip and the decision path are proven together before either is elaborated. Every
milestone after it thickens that path along one axis at a time — first the decisions it can
return, then what it does when the store is gone.

## M1 — End-to-end limit decision for one key

**Delivers**: R1.1
**Touches**: `RateLimiter`, `RedisStore`
**Depends on**: none
**Demo**: Send one request for a key; observe a counter in Redis and an allowed response.
**Risk retired**: Proves the increment-and-read round trip and the decision path work together, before any window or failure logic exists to confuse a failure.

## M2 — Rejection at the limit

**Delivers**: R1.2
**Touches**: `RateLimiter`
**Depends on**: M1
**Demo**: Send requests past the configured limit; observe a 429 on the one that exceeds it.
**Risk retired**: Confirms the limit comparison and the refusal response on a path already known to reach Redis, so a wrong answer is a comparison bug and nothing else.

## M3 — Fail open when Redis is unreachable

**Delivers**: R2.1
**Touches**: `RedisStore`
**Depends on**: M1
**Demo**: Stop Redis, then send a request; observe it allowed rather than refused or erroring.
**Risk retired**: Retires the outage behaviour [K1] flagged as specified but unexercised — the one requirement no amount of happy-path traffic would have caught.
```

## plan-validation.md — generated

```markdown
# Plan Validation Report

## Delivery order

| Milestone | Delivers | Touches | Depends on |
|---|---|---|---|
| M1 End-to-end limit decision for one key | R1.1 | RateLimiter, RedisStore | — |
| M2 Rejection at the limit | R1.2 | RateLimiter | M1 |
| M3 Fail open when Redis is unreachable | R2.1 | RedisStore | M1 |

## Traceability

| Criterion | Requirement | Delivered by | Status |
|---|---|---|---|
| R1.1 | R1 Rate limiting | M1 | ok |
| R1.2 | R1 Rate limiting | M2 | ok |
| R2.1 | R2 Outage handling | M3 | ok |

## Coverage

- Criteria: 3
- Delivered exactly once: 3 (100%)
- Uncovered: none
- Claimed by more than one milestone: none
- Dangling references: none

## Skeleton

- Spine: RateLimiter -> RedisStore
- M1 touches: RateLimiter, RedisStore
- Walks the spine end to end: yes

## Verdict

**PASS** — 3 criteria each delivered by exactly one of 3 milestones, M1 walks the spine end
to end, every milestone demonstrable. Ready to build.
```

## The plan this rejects

The obvious alternative orders by layer: M1 builds `RedisStore` with unit tests against a
local Redis, M2 builds `RateLimiter` on top of it. It looks tidy, it covers all three
criteria exactly once, and its dependencies are in order — it fails anyway:

```
## Skeleton

- Spine: RateLimiter -> RedisStore
- M1 touches: RedisStore
- Walks the spine end to end: NO

- M1 does not touch RateLimiter, which is on the spine

## Verdict

**FAIL** — M1 does not walk the spine.
```

That is the check earning its place. The layered plan defers every question worth asking
early — does the round trip work, is the interface right, does a decision actually come back
— until the last milestone, where a surprise is most expensive. Nothing about the criteria
coverage catches it; only the spine does.
