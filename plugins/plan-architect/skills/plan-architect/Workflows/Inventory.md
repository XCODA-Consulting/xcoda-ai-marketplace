# Inventory — Phase 1

**Goal**: gather, into one document, everything the plan will be checked against — the components to be built, the criteria they must satisfy, and the risks that should shape the order.

**Why it is first**: the inventory is the validator's authority. It is what lets this skill run against a `spec-architect` document set, a DoD, a design doc someone wrote in a wiki, or a codebase with no documents at all, and still check the plan mechanically. Whatever the sources, the inventory is the same shape.

## Mining the sources

Read what exists rather than asking for a format. A validated `design.md` and `validation.md` are the easy case — the roster is its `##` component sections and the criteria are already numbered. A DoD gives you acceptance criteria and usually implies the components. A codebase gives you components and almost never gives you criteria; write them from the stated intent and say plainly that you did.

**Carry criterion ids over unchanged.** If the source numbers something `R2.1`, it stays `R2.1` here. Renumbering to close a gap in the sequence breaks every reference back to the design for no gain.

**Mark what already exists.** Brownfield work is the common case, and a component marked `partial` plans differently from one marked `no` — it usually belongs in the skeleton, because touching it is cheap and proves the seam.

**Record risks as risks, not as work.** A risk is something you do not yet know; it earns its place by changing the order. If it would not change what you build first, leave it out.

## Output — `inventory.md`

```markdown
# Delivery Inventory

## Sources

- [D1] `[file or system]` — [what it contributed, and how far to trust it]
- [D2] `[file or system]` — [what it contributed]

## Components

| Component | Responsibility | Exists |
|---|---|---|
| `[ComponentName]` | [single responsibility, one sentence] | no / partial / yes |
| `[ComponentName]` | [single responsibility, one sentence] | no / partial / yes |

## Criteria

## R1 — [Requirement title]

1. WHEN [trigger], the **`[Component]`** SHALL [observable behaviour].
2. WHEN [trigger], the **`[Component]`** SHALL [observable behaviour].

## R2 — [Requirement title]

1. WHEN [trigger], the **`[Component]`** SHALL [observable behaviour].

## Risks

- [K1] [What is unknown, and which source left it open — this is what earns a milestone its place in the order.]
```

## Rules the validator enforces

- Components are declared in the `## Components` table as `` `Name` `` in backticks in the first cell — that cell is the roster.
- Criteria are `## R1 — Title` headings with numbered lines beneath, making `R1.1`, `R1.2`. Em dash, en dash or hyphen all parse.
- Every roster component must be touched by some milestone, and every component a milestone touches must be in the roster.

**Gate**: "Inventory complete — [N] components, [M] criteria, [K] risks, drawn from [sources]. Find the spine?"
