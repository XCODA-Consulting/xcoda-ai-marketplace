# Spine — Phase 2

**Prerequisite**: the inventory is agreed.
**Goal**: identify the thinnest path that still crosses the whole system, so the first milestone can walk it end to end.

The spine is not a list of important components. It is the shortest route from the thing that triggers the system to the thing you can observe when it works — and M1 is required to touch every component on it. Choose the spine carelessly and you have either made M1 impossible or made it meaningless.

## Finding it

- **Start at the trigger, end at the evidence.** The first row receives the input; the last row is what you look at to know it worked. If nothing on the path is observable from outside, the spine is wrong.
- **Thin, not short.** Every component on the path stays on it; what shrinks is how much each one does. One key, one event, one request — the full route, carrying the least possible cargo.
- **Nothing stubbed on the path.** A mock inside the spine defeats the point: the risk being retired is that these parts work *together*. Stub what hangs off the path, never what is on it.
- **Refuse decoration.** Anything that makes the demo nicer rather than possible — retries, metrics, error formatting, a second key type — is a thickening. Name it in the deferred list so nobody thinks it was forgotten.

A good test: if the skeleton lands and the whole team can watch one real thing happen end to end, it is right. If landing it proves only that a layer compiles, it is not a spine.

## Output — `spine.md`

```markdown
# Walking Skeleton

## The thinnest path

[One paragraph: the single smallest real behaviour that crosses the system, and what it
deliberately does not do yet.]

## Spine

| Component | Role on the path |
|---|---|
| `[ComponentName]` | entry — [what starts the walk] |
| `[ComponentName]` | [what it contributes on the way through] |
| `[ComponentName]` | exit — [the observable result] |

## First demo

[What you will run and what you will see when M1 lands. Concrete enough that someone else
could perform it.]

## Deferred to later milestones

- [capability deliberately absent from the skeleton — and why it is a thickening, not a prerequisite]
```

## Rules the validator enforces

- The spine is the `` `Name` `` cells of the `## Spine` table, in row order — the order of the walk.
- It must name at least two components. A one-component spine is not an end-to-end path.
- Every spine component must appear in `M1`'s `**Touches**` line. This is the check that makes a horizontally sliced plan fail.

**Gate**: "Spine is [A] -> [B] -> [C], demonstrable by [first demo]. [N] capabilities deferred. Write the milestones?"
