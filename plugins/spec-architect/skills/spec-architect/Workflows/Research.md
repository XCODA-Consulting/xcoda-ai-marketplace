# Research — Phase 1

**Goal**: settle the technology and pattern choices, with every claim traceable to a page you actually opened.

**Why it is first**: an unverified claim about a library's behavior, a protocol's guarantees, or a service's limits is cheap to fix here and expensive to fix once components have been designed around it. Recalled knowledge is a starting point for what to search, never the evidence itself.

## Protocol

1. **Search** for the domain's established patterns, the candidate technologies, and anything that would rule one out (limits, deprecations, licensing).
2. **Open the pages.** Fetch each source and read it. A search snippet is a pointer, not evidence — never cite one.
3. **Write findings from what you read.** Each finding names a choice and the reason for it, drawn from a source you opened.
4. **Cite inline.** Every factual claim ends with the id of the source that backs it: `[S1]`, `[S2]`. Phase 5 checks that every id cited is declared and every source declared is cited — an uncited source usually means you read it and forgot to use it, or kept a claim after dropping its evidence.

## Output — `research.md`

```markdown
# Technology Research

## Problem framing

[Two or three sentences: what is being built, and which technical questions actually
need deciding before the shape of the system can be drawn.]

## Findings

| Choice | Why, with evidence |
|---|---|
| `[Technology]` | [Reason, drawn from a source you opened, ending in a citation [S1].] |
| `[Pattern]` | [Reason, with its own citation [S2].] |

## Alternatives rejected

- **[Option]** — [why it lost, cited if the reason is factual rather than contextual [S2]]

## Sources

- [S1] https://example.com/first-page-you-opened
- [S2] https://example.com/second-page-you-opened
```

## Rules the validator enforces

- Sources are declared as `- [S1] <url>` under `## Sources`.
- Findings live in a table; citations are `[S1]` markers inside the rationale column.
- Every declared source is cited, and every cited id is declared.

**Gate**: "Research complete — [N] sources opened and cited, [M] findings. The stack is settled. Draw the blueprint?"
