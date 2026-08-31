# Blueprint — Phase 2

**Prerequisite**: the stack from Research is agreed.
**Goal**: name the parts, draw how data moves between them, and fix the boundary of what is being built.

The component names chosen here are used verbatim in Requirements, Design and Validation. Renaming one later without propagating it breaks traceability silently, so pick names you can live with.

## What good looks like

- **One responsibility per component**, stated in a single sentence with no "and".
- **A data path you can trace end to end**, from the triggering input to the observable result.
- **Named interfaces**, including the protocol — "talks to" is not an interface.
- **An explicit out-of-scope list.** What you refuse to build is as load-bearing as what you commit to; it is the thing reviewers argue with, and better argued with now.

## Output — `blueprint.md`

```markdown
# Component Blueprint

## Objective

[One paragraph: what the system does once this is built, and how you would know it works.]

## Boundaries

### In scope
- [capability that WILL be built]
- [integration that WILL be supported]

### Out of scope
- [capability deliberately excluded — and, if useful, where it might land later]

## Components

| Component | Responsibility |
|---|---|
| `[ComponentName]` | [single responsibility, one sentence] |
| `[ComponentName]` | [single responsibility, one sentence] |

## Data flow

\`\`\`mermaid
flowchart LR
    IN[Trigger] --> A[ComponentName]
    A --> B[ComponentName]
    B --> OUT[Result]
\`\`\`

## Interfaces

- **`[ComponentA]` → `[ComponentB]`** — [protocol and payload shape]
- **`[ComponentA]` → external** — [service, protocol, auth]
- **Failure behaviour** — [what each hop does when the next one is unavailable]
```

## Rules the validator enforces

- Components are declared in the table as `` `Name` `` in backticks — that cell is the roster.
- The roster must match the `## ComponentName` sections in `design.md` exactly, in both directions.

**Gate**: "Blueprint complete — [N] components, boundaries drawn, data path traced. These names carry through the rest of the documents. Write requirements?"
