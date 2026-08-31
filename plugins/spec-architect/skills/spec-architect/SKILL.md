---
name: spec-architect
description: Evidence-based architecture and design specification for a single implementation — the "what" and "how" (components, data flow, interfaces, requirements traceability), mechanically verified, with no execution plan. USE WHEN "design doc", "architecture spec", "technical specification", "system design", "spec the architecture", "design the components", OR user has requirements/a DoD/PRD and wants a verified design before planning implementation.
---

# SpecArchitect

Five phases, each gated on the one before, producing a design whose completeness is checked by a script rather than by eye:

| Phase | Workflow | Produces |
|---|---|---|
| 1. Research | `Workflows/Research.md` | `research.md` — choices, each cited to a page actually opened |
| 2. Blueprint | `Workflows/Blueprint.md` | `blueprint.md` — component roster, boundaries, data flow |
| 3. Requirements | `Workflows/Requirements.md` | `requirements.md` — checkable criteria, each owned by a component |
| 4. Design | `Workflows/Design.md` | `design.md` — interfaces, data models, `Satisfies` declarations |
| 5. Validation | `Workflows/Validation.md` | `validation.md` — generated; fails closed on any gap |

## Scope — read before starting

This produces the **shape of the system**, not a delivery plan. It does not sequence work into milestones, choose walking-skeleton versus horizontal slicing, or emit a task list.

That separation is the point. A design and a plan answer different questions and fail in different ways, and a document trying to be both gets reviewed as neither — sequencing arguments crowd out the question of whether the design is right. When the spec passes validation, `design.md` and `validation.md` are the handoff pair for a planning step.

If asked for milestones or a rollout order, say it is out of scope here and point at the planning step rather than improvising one.

## Conventions

Three small conventions carry the traceability, and the validator enforces all three:

- **Source ids** — research declares sources as `- [S1] <url>` and cites them inline as `[S1]`.
- **Criterion ids** — `## R2 — Title` with numbered lines beneath makes criteria `R2.1`, `R2.2`.
- **Satisfies lines** — each component section in `design.md` carries one `**Satisfies**: R1.1, R2.3` naming what it is on the hook for.

Component names are written identically in blueprint, requirements and design. A rename propagated to only one document is exactly the drift Phase 5 catches.

## Prerequisites

- Objectives, constraints and scope boundaries — from the user, or from a DoD/PRD
- Optionally an existing DoD/PRD to mine in Phase 3, so requirements trace to a real ask
- A target directory for the documents (default: current directory)

## Principles

1. **Evidence before opinion.** No technology claim without a source you opened. Recalled knowledge tells you what to search for, not what is true.
2. **Traceability in both directions.** Every criterion is satisfied by a component; every `Satisfies` id names a real criterion.
3. **Gate each phase.** Get agreement before advancing; do not run all five silently unless asked to.
4. **Fail closed.** A non-zero validator exit is the phase failing, not a note to route around.
5. **No plan.** See Scope.

## Running validation

```bash
python3 scripts/validate_spec.py --path <output-dir>
```

Checks coverage, references, component naming and evidence; writes `validation.md`; exits non-zero on any gap.

## Examples

**From a DoD**
```
User: "Spec the architecture for webhook retry delivery. Here's the DoD: @webhook-retry-dod.md"
-> Phase 1: research retry/backoff and idempotency patterns, cite each source
-> Phase 2: roster (RetryScheduler, DeliveryStore, WebhookSender), boundaries, data flow
-> Phase 3: criteria mined from the DoD, each owned by a component
-> Phase 4: interfaces plus Satisfies lines
-> Phase 5: validate_spec.py passes; validation.md written
```

**No prior document**
```
User: "Architecture spec for a rate limiter, Redis-backed, must survive a Redis outage"
-> Phase 1 starts from the stated constraints; phases proceed with a gate at each
```

**Asked for a plan**
```
User: "Design's validated, now plan the rollout"
-> Out of scope here. design.md + validation.md are the handoff to planning.
```
