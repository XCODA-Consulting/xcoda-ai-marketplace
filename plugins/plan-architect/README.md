# plan-architect

Turn a settled design into a **walking-skeleton execution plan** — milestones that each land something you can see, in an order that retires integration risk first rather than last.

## Overview

Four phases, each gated on the one before:

1. **Inventory** (`inventory.md`) — components, criteria and risks, mined from whatever exists: a `spec-architect` document set, a DoD, a wiki page, or the codebase. This is the validator's authority, which is what lets the plugin run standalone.
2. **Spine** (`spine.md`) — the thinnest path that still crosses the whole system, from the trigger to the thing you can observe.
3. **Milestones** (`plan.md`) — `M1` walks the spine; each later milestone thickens it along one axis. Every milestone declares what it delivers, what it touches, what it depends on, what you will see, and what risk it retires.
4. **Validation** (`plan-validation.md`) — generated, not authored. Exits non-zero on any gap.

The opinion is enforced, not suggested: because `M1` must touch every component on the spine, a plan that builds the storage layer first and wires it up last **fails the check** — even with perfect criterion coverage and correct dependencies.

**What it deliberately does not do**: revisit component boundaries or interfaces, break milestones into tasks, or estimate. A design change discovered while planning is a finding to take back to the design, not something to settle under a milestone heading.

## Installation

```bash
claude plugin install plan-architect@xcoda-ai-marketplace
```

## What's included

- **Skill** — `plan-architect`, routing across the four phase workflows.
- **Workflows** — `Inventory.md`, `Spine.md`, `Milestones.md`, `Validation.md`, each with its output template and gate.
- **Reference** — `reference/ExampleRun.md`, a complete worked example (Redis-backed rate limiter) that continues `spec-architect`'s, validated to pass — and a closing section showing the layered plan the validator rejects.
- **Tool** — `scripts/validate_plan.py`:

  ```bash
  python3 scripts/validate_plan.py --path <output-dir>
  ```

  | Check | Fails when |
  |---|---|
  | coverage | a criterion is delivered by no milestone, or by more than one |
  | references | a `Delivers` id names no real criterion, or `Depends on` points at a later milestone |
  | naming | a `Touches` component is absent from the roster, or a roster component is built by nobody |
  | skeleton | `M1` does not touch every spine component, or the spine is shorter than two |
  | demonstrability | a milestone has no `Demo` or no `Risk retired` |

## Prerequisites

- A settled design — `design.md` from `spec-architect`, a plain design doc, a DoD, or the codebase itself
- Python 3.9+ to run the validator; no third-party packages

## Usage

```
"The design's validated. Plan the rollout. @design.md @validation.md"
"How should we sequence the webhook retry work? Here's the DoD."
"Break this into milestones — I don't want to integrate at the end again."
```

The report is written as `plan-validation.md` rather than `validation.md`, so a plan can share a directory with a `spec-architect` document set without the two colliding.

## Relationship to `spec-architect`

The companion [`spec-architect`](../spec-architect) plugin produces the `design.md` and `validation.md` that Phase 1 mines, and stops deliberately short of sequencing — its final gate names this step as the handoff. Criterion ids cross that boundary unchanged, so `R1.1` in a design is `R1.1` in the plan and the traceability survives. Neither plugin needs the other: this one will mine a DoD or a codebase just as readily.
