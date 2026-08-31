# Validation — Phase 4

**Prerequisite**: `inventory.md`, `spine.md` and `plan.md` all exist.
**Goal**: prove mechanically that the plan delivers everything once, in a possible order, starting from a real skeleton. This is what makes the plan *checked* rather than merely *agreed*.

## Run it

```bash
python3 scripts/validate_plan.py --path <output-dir>
```

It writes `plan-validation.md` and exits non-zero if anything fails. Five checks:

| Check | Fails when |
|---|---|
| **coverage** | a criterion is delivered by no milestone, or by more than one |
| **references** | a `Delivers` id names no real criterion, or a `Depends on` points at a later milestone |
| **naming** | a `Touches` component is absent from the roster, or a roster component is built by nobody |
| **skeleton** | `M1` does not touch every spine component, or the spine is shorter than two |
| **demonstrability** | a milestone has no `Demo` or no `Risk retired` |

A non-zero exit is the phase failing. It is not an advisory — route back and fix the document, do not proceed past it.

The report is written as `plan-validation.md`, not `validation.md`, so a plan can live in the same directory as a `spec-architect` document set without the two reports colliding.

## Reading a failure

- **Uncovered criterion** — some milestone should deliver it. Add it to that milestone's `Delivers` line. Do not delete the criterion to make the check green; if it genuinely is not in scope, remove it from the inventory in Phase 1 with a note saying why.
- **Claimed twice** — two milestones both claim it, so neither owns it. Decide which one lands the behaviour; if it really does arrive in two pieces, the criterion is two criteria and belongs split in the inventory.
- **Out-of-order dependency** — a milestone needs a later one. Reorder them; the numbering is the delivery order, so renumbering *is* the fix.
- **Roster disagreement** — either a component was renamed on one side only, or something in the inventory is built by no milestone. The second is the interesting one: it usually means a component nobody planned, not a typo.
- **Skeleton gap** — `M1` does not walk the whole spine. This is the horizontal-slicing check, and it is the one worth arguing with before overriding: either M1 must grow to cross the system, or the spine was drawn thicker than the thinnest real path. Fix one of those, not the check.
- **Demonstrability gap** — a milestone cannot say what you would see. Usually it is a task that wandered up a level.

## Output — `plan-validation.md`

Generated, not authored. It contains the delivery order, a traceability table (every criterion and the milestone that delivers it), coverage counts, the spine comparison, the roster comparison, and a verdict line.

**Gate**: "Validation passed — every criterion delivered once, M1 walks the spine, every milestone demonstrable. `plan.md` and `plan-validation.md` are the handoff to implementation."

## After a pass

Stop here. The plan says what lands and in what order; how each milestone gets built is the implementer's call, and writing that down now only creates something to keep in sync.
