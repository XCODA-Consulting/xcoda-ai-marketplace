# Worked Example: Redis-backed Rate Limiter

A complete two-component run through all five phases. This is the fixture the validator is
tested against — running `validate_spec.py` over these four documents produces a **PASS**.

## research.md

```markdown
# Technology Research

## Problem framing

Per-key request limiting for an HTTP service, where the limiter must degrade safely if its
counter store is unreachable rather than failing every request.

## Findings

| Choice | Why, with evidence |
|---|---|
| `Redis` | TTL counters are an established rate-limiting pattern [S1]. |

## Alternatives rejected

- **In-process counters** — cannot hold a shared limit across replicas.

## Sources

- [S1] https://redis.io/docs/latest/develop/use/patterns/
```

## blueprint.md

```markdown
# Component Blueprint

## Objective

Enforce a per-key request rate across all replicas, and keep serving traffic when the
counter store is down.

## Boundaries

### In scope
- Per-key fixed-window limiting
- Fail-open behaviour on store outage

### Out of scope
- Per-endpoint quotas — no ask for them yet

## Components

| Component | Responsibility |
|---|---|
| `RateLimiter` | Enforces per-key request rates |
| `RedisStore` | Persists counters with TTL |

## Data flow

\`\`\`mermaid
flowchart LR
    IN[Request] --> RL[RateLimiter]
    RL --> RS[RedisStore]
    RS --> RL
    RL --> OUT[Allow or 429]
\`\`\`

## Interfaces

- **`RateLimiter` → `RedisStore`** — increment-and-read for a key, returns the current count
- **Failure behaviour** — if `RedisStore` is unreachable, `RateLimiter` allows the request
```

## requirements.md

```markdown
# Requirements

## R1 — Rate limiting

1. WHEN a request arrives, the **`RateLimiter`** SHALL compare the count to the limit.
2. WHEN the limit is exceeded, the **`RateLimiter`** SHALL reject with 429.

## R2 — Outage handling

1. WHEN Redis is unreachable, the **`RedisStore`** SHALL fail open.
```

## design.md

```markdown
# Component Design

## RateLimiter

**Responsibility**: Enforces per-key request rates
**Location**: `src/limits/rate_limiter.py`
**Satisfies**: R1.1, R1.2

### Interface

\`\`\`python
class RateLimiter:
    def check(self, key: str) -> Decision:
        """Allow or reject. Allows when the store is unreachable."""
\`\`\`

## RedisStore

**Responsibility**: Persists counters with TTL
**Location**: `src/limits/redis_store.py`
**Satisfies**: R2.1

### Interface

\`\`\`python
class RedisStore:
    def bump(self, key: str, window_s: int) -> int | None:
        """Increment and return the count, or None if Redis is unreachable."""
\`\`\`
```

## validation.md — generated

```markdown
# Validation Report

## Traceability

| Requirement | Criterion | Satisfied by | Status |
|---|---|---|---|
| R1 Rate limiting | R1.1 | RateLimiter | ok |
| R1 Rate limiting | R1.2 | RateLimiter | ok |
| R2 Outage handling | R2.1 | RedisStore | ok |

## Coverage

- Criteria: 3
- Satisfied: 3 (100%)
- Uncovered: none
- Dangling references: none

## Verdict

**PASS** — 3 criteria all satisfied by a named component, rosters agree, evidence cited.
Ready for planning.
```

Note what is absent: no milestones, no task list, no ordering. That boundary is deliberate —
planning is a separate step that reads these documents.
