# Milestones — Phase 3

**Prerequisite**: the spine is agreed.
**Goal**: order the work as milestones that each land something you can see, starting with the one that walks the spine.

This phase carries the weight. Inventory and Spine exist to feed it; Validation exists to check it. M1 is already determined — it is the spine, walked. The judgement is in what comes after, and it is one judgement repeated: what is the next thing that, if it were wrong, we would most want to find out now?

## Ordering after M1

- **Thicken one axis at a time.** A milestone that adds a decision *and* a failure mode *and* a second input type will fail in three ways at once and tell you nothing about which.
- **Risk first, convenience last.** Pull the milestone that retires a `[K…]` risk forward, even when something else is easier. The order exists to surface bad news early; sorting by ease inverts it.
- **Dependencies point backwards only.** A milestone may depend on earlier ones. If it needs a later one, the order is wrong — reorder rather than noting the cycle.

## Writing a milestone

Every milestone carries five labels, each on its own line. Two of them are where plans usually go soft:

> **Demo**: what you will run, and what you will *see*. "Retries are implemented" is not a demo; "kill the subscriber, publish an event, watch three attempts land in the log with widening gaps" is.

> **Risk retired**: what this milestone proves that was not proven before. If the honest answer is "nothing, it was always going to work", the milestone is probably a task belonging inside another one.

## Output — `plan.md`

```markdown
# Execution Plan

## Approach

[One paragraph: the skeleton, then the axis each subsequent milestone thickens along and why
in that order.]

## M1 — [What lands, stated as a capability]

**Delivers**: R1.1
**Touches**: `[ComponentName]`, `[ComponentName]`
**Depends on**: none
**Demo**: [What you run, and what you see.]
**Risk retired**: [What this proves that nothing proved before.]

## M2 — [What lands]

**Delivers**: R1.2, R2.1
**Touches**: `[ComponentName]`
**Depends on**: M1
**Demo**: [What you run, and what you see.]
**Risk retired**: [What this proves.]
```

## Rules the validator enforces

- Milestones are `## M1 — Title`, numbered from 1 in delivery order.
- Every criterion in the inventory is delivered by **exactly one** milestone — none uncovered, none claimed twice.
- `**Depends on**` names only earlier milestones, or `none`. This is what rules out cycles.
- Every component in a `**Touches**` line is in the inventory roster, and `M1` touches the whole spine.
- `**Demo**` and `**Risk retired**` are present and non-empty on every milestone.

**Gate**: "[N] milestones, every criterion delivered once, M1 walks the spine. Validate?"
