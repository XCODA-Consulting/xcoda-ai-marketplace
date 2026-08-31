---
name: plan-architect
description: Turn a settled design into a walking-skeleton execution plan — milestones that each deliver named criteria, declare what they touch, and state what you will see when they land — mechanically checked, so a horizontally sliced plan fails instead of shipping. USE WHEN "plan the rollout", "execution plan", "break this into milestones", "what order should we build this in", "sequence the work", OR user has a design or a DoD and needs delivery order rather than more architecture.
---

# PlanArchitect

Four phases, each gated on the one before, producing a delivery order whose soundness is checked by a script rather than by eye:

| Phase | Workflow | Produces |
|---|---|---|
| 1. Inventory | `Workflows/Inventory.md` | `inventory.md` — components, criteria and risks, from whatever sources exist |
| 2. Spine | `Workflows/Spine.md` | `spine.md` — the thinnest path that crosses the whole system |
| 3. Milestones | `Workflows/Milestones.md` | `plan.md` — M1 walks the spine; each later one thickens it |
| 4. Validation | `Workflows/Validation.md` | `plan-validation.md` — generated; fails closed on any gap |

## Scope — read before starting

This produces the **order of delivery**, not the design and not a task list. It does not revisit component boundaries, choose interfaces, or decompose a milestone into tickets.

That separation is the point. Planning is where architecture arguments get reopened by the back door — "while we're sequencing this, should `RedisStore` really own the TTL?" — and a document that answers both questions gets reviewed as neither. If the design turns out to be wrong, that is a finding to take back to the design, not a thing to fix inside the plan. Say so and stop rather than quietly re-architecting under a milestone heading.

Task breakdown is likewise out. A milestone names what lands and how you will see it; how to get there is the implementer's call, and a checklist written now is stale before it is read.

## Conventions

Four small conventions carry the plan, and the validator enforces all four:

- **Criterion ids** — carried over *unchanged* from the design's requirements. `## R1 — Title` with numbered lines beneath makes criteria `R1.1`, `R1.2`. Renumbering at the boundary is how traceability gets lost between documents.
- **Milestone ids** — `## M1 — Title`, numbered from 1, in delivery order.
- **The five labels** — every milestone carries `**Delivers**`, `**Touches**`, `**Depends on**`, `**Demo**` and `**Risk retired**`, each on its own line.
- **One owner per criterion** — exactly one milestone delivers each. Two milestones both claiming `R1.1` means neither owns it.

Component names are written identically in the inventory, the spine and the plan. A rename propagated to only one document is exactly the drift Phase 4 catches.

## Prerequisites

- A settled design — `design.md` from `spec-architect`, a plain design doc, a DoD, or the codebase itself
- The acceptance criteria the work is answerable to, if they exist anywhere already
- A target directory for the documents (default: current directory)

## Principles

1. **Walk before you thicken.** M1 crosses the entire system doing the smallest real thing. Integration risk is the risk worth retiring first, and a plan that defers it to the end has hidden its hardest problem behind its easiest work.
2. **Every milestone is demonstrable.** If you cannot say what you will *see*, it is not a milestone — it is a phase of work, and phases of work are how a plan reports 80% complete for a month.
3. **Gate each phase.** Get agreement before advancing; do not run all four silently unless asked to.
4. **Fail closed.** A non-zero validator exit is the phase failing, not a note to route around.
5. **No redesign.** See Scope.

## Running validation

```bash
python3 scripts/validate_plan.py --path <output-dir>
```

Checks coverage, references, component naming, skeleton and demonstrability; writes `plan-validation.md`; exits non-zero on any gap.

## Examples

**From a validated spec**
```
User: "The design's validated. Plan the rollout. @design.md @validation.md"
-> Phase 1: inventory the components and carry the criterion ids over unchanged
-> Phase 2: spine = RateLimiter -> RedisStore, the thinnest end-to-end path
-> Phase 3: M1 walks it; M2 and M3 thicken along one axis each
-> Phase 4: validate_plan.py passes; plan-validation.md written
```

**No prior spec**
```
User: "How should we sequence the webhook retry work? Here's the DoD."
-> Phase 1 mines the DoD for components and criteria; the inventory becomes the authority
```

**Asked to redesign**
```
User: "While you're planning, the store should own retry state instead"
-> That is a design change, not a sequencing one. Take it back to the design and
   re-plan from the result, rather than deciding it inside a milestone.
```
