# Validation — Phase 5

**Prerequisite**: `research.md`, `blueprint.md`, `requirements.md` and `design.md` all exist.
**Goal**: prove mechanically that nothing was left unaccounted for. This is what makes the spec *verified* rather than merely *written*.

## Run it

```bash
python3 scripts/validate_spec.py --path <output-dir>
```

It writes `validation.md` and exits non-zero if anything fails. Four checks:

| Check | Fails when |
|---|---|
| **coverage** | a criterion in `requirements.md` is claimed by no component |
| **references** | a `Satisfies` line names a criterion that does not exist |
| **naming** | the blueprint roster and the design's component sections disagree |
| **evidence** | a finding cites an undeclared source, or a declared source is never cited |

A non-zero exit is the phase failing. It is not an advisory — route back and fix the document, do not proceed past it.

## Reading a failure

- **Uncovered criterion** — some component should own it. Add it to that component's `Satisfies` line and specify the behaviour. Do not delete the criterion to make the check green; if it genuinely is not needed, remove it in Phase 3 with a note saying why.
- **Dangling reference** — a `Satisfies` id points at nothing. Usually a typo, or a requirement renumbered without updating Design.
- **Roster disagreement** — a component was renamed on one side only, or designed without being planned. Reconcile the names; if the component is genuinely new, it belongs in the blueprint too.
- **Evidence gap** — either a claim lost its source, or a source was read and never used. Both are worth a look: the first is an unsupported claim, the second often means a finding was dropped but its evidence was left behind.

## Output — `validation.md`

Generated, not authored. It contains a traceability table (every criterion and the components that satisfy it), coverage counts, the component-roster comparison, evidence totals, and a verdict line.

**Gate**: "Validation passed — every criterion satisfied, rosters agree, evidence cited. `design.md` and `validation.md` are the handoff pair for planning."

## After a pass

Stop here. Milestones, sequencing and the walking-skeleton question belong to the planning step, which reads this output rather than being folded into it.
