# Requirements — Phase 3

**Prerequisite**: the blueprint is agreed.
**Goal**: state what the system must do, in criteria a reviewer can pass or fail, each owned by a named component.

## Where these come from

If a DoD or PRD exists, **mine it** — do not reinvent criteria from memory. Every requirement here should trace to something a source actually asked for. Where the source implies an architectural constraint rather than a behaviour (a prohibition, a mandatory path, a data shape), carry that constraint into the requirement text so Design cannot quietly lose it.

Where no source asked for something you believe is needed, say so explicitly rather than laundering it in as though it were requested. An invented requirement that reads like a customer ask is worse than an open question.

## Writing a criterion

Each criterion is one numbered line, in the form:

> WHEN *[trigger]*, the **`[Component]`** SHALL *[observable, checkable behaviour]*.

- **Observable** — a reviewer can tell whether it happened without reading the implementation.
- **One behaviour per line.** "and" usually means two criteria.
- **Owned** — name the component from the blueprint that is responsible.
- Criteria are numbered within their requirement, so `## R2` line 3 is criterion `R2.3`. Design refers to it by that id.

## Output — `requirements.md`

```markdown
# Requirements

## R1 — [Capability name]

1. WHEN [trigger], the **`[Component]`** SHALL [behaviour].
2. WHEN [trigger], the **`[Component]`** SHALL [behaviour].

## R2 — [Another capability]

1. WHEN [trigger], the **`[Component]`** SHALL [behaviour].

## R3 — [Quality attribute, e.g. throughput or recovery]

1. WHEN [load or failure condition], the **`[Component]`** SHALL [measurable behaviour].
```

## Rules the validator enforces

- Requirement headings are `## R<n> — <title>` (em dash, en dash or hyphen all parse).
- Criteria are numbered lines beneath a requirement heading; their ids are `R<n>.<line>`.
- Every criterion must be claimed by some component in `design.md`, or Phase 5 fails.

**Gate**: "[N] requirements, [M] criteria, each assigned to a component. Design them?"
