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

That separation is the point. A design and a plan answer different questions and fail in different ways, and a document trying to be both gets reviewed as neither — sequencing arguments crowd out the question of whether the design is right. When the spec passes validation, `design.md` and `validation.md` are the handoff pair for `plan-architect`, with `requirements.md` supplying the criterion text.

If asked for milestones or a rollout order, say it is out of scope here and point at
`plan-architect`. If that plugin is not available, provide the handoff artifacts rather
than improvising a delivery plan inside this skill.

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
- Python 3 and access to the bundled script in an environment with script execution, for mechanical validation

## Resource and output paths

Resolve `Workflows/`, `reference/`, and `scripts/` relative to the directory containing
this loaded `SKILL.md`, including when the host has installed it into a cache. Use the
host's skill resource reader when resources are exposed as URIs. For shell execution,
resolve the script to an absolute filesystem path and quote it; do not assume the current
directory is the skill directory or rely on a host-specific plugin-root variable.

Keep all generated documents in the user's chosen project/output directory (default:
the project's current directory). Resolve that directory to an absolute path before
running validation; do not write deliverables into the installed plugin directory.

## Principles

1. **Evidence before opinion.** No technology claim without a source you opened. Recalled knowledge tells you what to search for, not what is true.
2. **Traceability in both directions.** Every criterion is satisfied by a component; every `Satisfies` id names a real criterion.
3. **Gate each phase.** Get agreement before advancing; do not run all five silently unless asked to.
4. **Fail closed.** A non-zero validator exit is the phase failing, not a note to route around.
5. **No plan.** See Scope.

## Running validation

Replace the placeholders with the resolved absolute skill directory and the user's
absolute output directory.

```bash
python3 "<absolute-skill-dir>/scripts/validate_spec.py" --path "<absolute-output-dir>"
```

Checks coverage, references, component naming and evidence; writes `validation.md`; exits non-zero on any gap.

If Python execution, the bundled script, or filesystem access is unavailable, report
**validation pending** and provide the resolved command for an environment with access
to the script and documents. Do not manufacture `validation.md`, claim a pass, or mark
the design ready for planning until the script runs successfully and generates a passing
report.

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
-> Out of scope here. Hand design.md + validation.md, supported by requirements.md, to plan-architect.
```
