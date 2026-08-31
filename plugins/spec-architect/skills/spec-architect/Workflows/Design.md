# Design — Phase 4

**Prerequisite**: requirements are agreed.
**Goal**: specify each component well enough that someone else could build it without re-deriving the decisions already made.

This phase carries the weight. Research, Blueprint and Requirements exist to feed it; Validation exists to check it.

## The Satisfies line

Every component section carries one **`**Satisfies**: R1.1, R2.3`** line naming the criteria it is responsible for. This is the only place coverage is declared, and it is what Phase 5 reads.

One declaration per component, not tags scattered through the interface — a reader should be able to answer "what is this component on the hook for?" from a single line, and a reviewer should be able to spot an over-broad component by how long that line gets. A component with no `Satisfies` line is invisible to validation, however well specified it otherwise is.

## Output — `design.md`

```markdown
# Component Design

## [ComponentName]

**Responsibility**: [copied verbatim from the blueprint — do not let it drift]
**Location**: `src/path/to/component.py`
**Satisfies**: R1.1, R1.2

### Interface

\`\`\`python
class ComponentName:
    def handle(self, request: Request) -> Result:
        """[what it does, and what it does when the input is invalid]"""
\`\`\`

### Data model

\`\`\`python
@dataclass
class Thing:
    field: str
\`\`\`

### Dependencies

- `[OtherComponent]` — [what it needs from it]
- [external service] — [what happens when it is unavailable]

## [NextComponent]

**Responsibility**: [...]
**Location**: `src/path/to/next.py`
**Satisfies**: R2.1

### Interface
[...]
```

## Rules the validator enforces

- Component sections are `## ComponentName` at heading level 2, matching the blueprint roster exactly.
- Each declares `**Satisfies**: R1.1, R2.3`; every id must exist in `requirements.md`.
- Together the `Satisfies` lines must cover every criterion.

## Keep out

No milestones, no task lists, no sequencing, no estimates. If you find yourself writing "first we build X, then Y", stop — that is the planning step, and it is deliberately a different document produced by a different skill. A design that has absorbed a delivery plan is hard to review as a design.

**Gate**: "All [N] components specified, every criterion claimed. Validate?"
