# spec-architect

Produce a **verified architecture and design specification** for a single implementation — the "what" and "how" of the system's shape — with no execution plan mixed in.

## Overview

Five phases, each gated on the one before:

1. **Research** (`research.md`) — technology and pattern choices, each cited to a page actually opened. Search snippets are pointers, not evidence.
2. **Blueprint** (`blueprint.md`) — component roster, in/out-of-scope boundaries, data flow.
3. **Requirements** (`requirements.md`) — criteria a reviewer can pass or fail, each owned by a named component. Mines an existing DoD/PRD rather than reinventing them.
4. **Design** (`design.md`) — interfaces and data models, each component declaring a `**Satisfies**: R1.1, R2.3` line naming what it is on the hook for.
5. **Validation** (`validation.md`) — generated, not authored. Checks coverage, references, component naming and evidence; exits non-zero on any gap.

**What it deliberately does not do**: sequence work into milestones, choose walking-skeleton versus horizontal slicing, or emit a task list. A design and a plan answer different questions; a document trying to be both gets reviewed as neither.

## Installation

```bash
claude plugin install spec-architect@xcoda-ai-marketplace
```

## What's included

- **Skill** — `spec-architect`, routing across the five phase workflows.
- **Workflows** — `Research.md`, `Blueprint.md`, `Requirements.md`, `Design.md`, `Validation.md`, each with its output template and gate.
- **Reference** — `reference/ExampleRun.md`, a complete two-component worked example (Redis-backed rate limiter), validated to pass.
- **Tool** — `scripts/validate_spec.py`:

  ```bash
  python3 scripts/validate_spec.py --path <output-dir>
  ```

  | Check | Fails when |
  |---|---|
  | coverage | a criterion is claimed by no component |
  | references | a `Satisfies` line names a criterion that does not exist |
  | naming | the blueprint roster and the design's sections disagree |
  | evidence | a finding cites an undeclared source, or a source is never cited |

## Usage

```
"Spec the architecture for webhook retry delivery. Here's the DoD: @webhook-retry-dod.md"
"I need an architecture spec for a rate limiter service, Redis-backed"
```

When validation passes, `design.md` and `validation.md` are the handoff pair for the companion [`plan-architect`](../plan-architect) plugin — this skill's output is that step's input, not a substitute for it.

## Relationship to `dod-architect`

The companion [`dod-architect`](../dod-architect) plugin produces the DoD that Phase 3 mines. Both share a source-citation style (`[S1]`-style ids declared once and referenced inline), so the documents read as one system.
