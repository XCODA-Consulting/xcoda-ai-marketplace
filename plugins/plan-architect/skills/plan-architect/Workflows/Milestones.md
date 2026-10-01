# Milestones — Stage 2

**Prerequisite:** design readiness agreed, or explicit authorization to draft through
the workflow with unresolved design gaps retained as blockers.

Choose the smallest useful path from a real trigger, across the relevant components and
integration boundaries, to an observable result. This walking skeleton can be narrow:
one request type, one tenant, a controlled environment. It should exercise real protocols
and persistence early rather than end with disconnected layers waiting for integration.

Then sequence additional behavior, failure handling, hardening, migration, and rollout
according to the requirements and risks. Do not automatically add production rollout
to a prototype; state when deployment/rollback does not apply and why.

## Record in plan.json

Each milestone declares an ID, title, outcome, milestone `depends_on` IDs, an end-to-end
`demo`, checkable `acceptance` gates, and `rollout`/`rollback` considerations. Dependencies
are prerequisites, not a calendar; independent milestones can proceed concurrently.

Set `strategy` to `walking-skeleton` by default and explain the actual first path in
`strategy_rationale`. Use `alternative` only with an explicit reason, for example an
irreducible migration prerequisite. Minimize prerequisite-only work and name when it
joins the executable path; avoid horizontal phases justified merely by component ownership.

Keep owners, dates, and estimates absent/null unless supplied. Note external constraints
and risks without inventing capacity or commitments.

**Gate:** agree on the slices, demonstrations, acceptance gates, and dependency order.
Whether the proposed demonstration is meaningful requires review; the validator only
checks that a demonstration and gates are recorded.
