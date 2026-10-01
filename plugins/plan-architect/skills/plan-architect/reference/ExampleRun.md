# Worked example: Redis-backed rate limiter

This fictional project uses a reviewed architecture rather than a spec-architect report.
The source snapshots below make its plan self-contained. `ExamplePlan.json` preserves
the requirement IDs and component names and passes the bundled structural validator.

## Requirements

- **R1.1:** When a request arrives, RateLimiter compares the shared per-key count to the configured limit.
- **R1.2:** When the count exceeds the limit, RateLimiter rejects the request with HTTP 429.
- **R2.1:** When Redis is unavailable, RedisStore reports unavailability and RateLimiter allows the request.

Scope includes local integration and controlled staging verification using the existing
feature switch and test route. Production rollout, per-endpoint quotas, and alternative
stores are out of scope. Owners, dates, and estimates have not been supplied.

## Architecture

**RateLimiter** exposes `check(key) -> Decision`, called by existing HTTP middleware
behind an existing feature switch. A decision permits a request when the count is at or
below the configured limit and maps an exceeded limit to HTTP 429. Key derivation,
limit, and window duration use existing configuration.

**RedisStore** exposes `bump(key, window_s) -> int | None`. It atomically increments
the shared per-key count and sets the TTL on the first increment in the window. Redis
is shared across replicas. The existing bounded client timeout is retained; timeout or
unavailability returns None, which RateLimiter interprets as allow. Recovery resumes
counting without restarting the service. Counters are ephemeral; there is no schema
migration. Switch disablement restores the baseline middleware path.

The executable path is HTTP request → RateLimiter → RedisStore → Redis → decision
→ HTTP response. This design is already decided; the plan sequences its implementation.

## Readiness review

In this fictional scenario, the requester and design owner read the requirements and
architecture, agreed on scope, interfaces, fail-open behavior, and feature-switch
rollback, and asked for the whole planning workflow. No design decisions remain open.
Staging credentials are pending external logistics; they block staging tasks, not local
implementation. This is a readiness review, not mechanical architecture validation.

## Planning result

1. **M1:** exercise a real request-to-Redis path across two replicas below the limit.
2. **M2:** deepen that path with rejection, counter reset, outage, and recovery behavior.
3. **M3:** demonstrate agreed behavior and rollback in staging once access is available.

T3 (rejection) and T4 (outage handling) can proceed in parallel after T2. T5 depends on
both and on external prerequisite P1. The milestone graph carries M1 → M2 → M3,
consistent with those task edges. No dates or people are invented.

## Run the example

Copy `reference/ExamplePlan.json` to `plan.json` in a temporary/project output directory,
then run from any working directory:

```bash
python3 "<absolute-skill-dir>/scripts/validate_plan.py" --path "<absolute-example-output-dir>"
```

Expected: exit `0`, `plan.md`, and `plan-validation.md` with **PASS**, all three criteria
and both components covered, and P1 visibly pending. A structural pass does not authorize
T5 to start before staging access is available. Identical JSON renders identical Markdown.

## Spec-architect variation

For a real spec handoff, read `design.md`, `validation.md`, and `requirements.md` plus
any needed blueprint/research context. Declare each as a source; set readiness kind to
`spec-architect` and `validation_source` to the report's source ID. Record the passing
current report and readiness agreement in evidence. Reuse the exact criterion IDs and
component names. The rest of the milestone/task format is unchanged.
