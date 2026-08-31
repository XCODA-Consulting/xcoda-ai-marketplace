# DoD Template — fill-in skeleton

Authoring notes are inline as `<!-- -->` comments; strip them from the final doc.

```markdown
# {Feature Name} — Definition of Done

## 1. Summary
{3 sentences: what the user/operator can do end-to-end after this ships. State plainly
if this is a slice of something larger, and name the follow-on.}

## 2. Why this matters
{Which goal/initiative this serves. Why it's needed now. What it unblocks downstream.}

## 3. Source material
<!-- If a source genuinely covers this feature, list it. If none does, open with a
     one-paragraph gap declaration instead — see SKILL.md "When no source addresses
     the feature" — and reframe this list as integration points, not a requirements
     source. -->
- {Source 1 — file/thread/ticket/transcript} — read in full before designing.
- {Source 2} — read in full before designing.

## 4. Design context — read before designing
<!-- The core section. Group by sub-topic. Every item ends in a Design implication.
     If a thorough read turned up no architecture-shaping constraints, say so plainly
     instead of padding this section. -->

### {Sub-topic 1}
{What the source says, quoted or closely paraphrased.}

**Design implication:** {What the engineer must do about it.}

### {Sub-topic 2}
{...}

**Design implication:** {...}

## 5. Persona
- **{Primary persona}**: {one line}
- **{Secondary persona, if any}**: {one line}

## 6. Preconditions
- {Deployment/access/test-data assumption}
- {...}

## 7. User acceptance criteria

### {Capability group 1}

#### {UAC title}
GIVEN {context}
WHEN {action}
THEN {observable outcome}

**Source:** {citation, quoting the operative clause}

#### {Another UAC in this group}
GIVEN {context}
WHEN {action}
THEN {observable outcome}

**Source:** {citation}
**Must not break:** {citation} (attaches-to: {what surfaces where} / regression guard: {what must keep passing})

## 8. Design seams / forward-compatibility
- {Where to leave room so the follow-on doesn't force a rewrite} — {source pointer}
- {...}

## 9. Out of scope
- {Deferred item} — deferred to {follow-on}, {source pointer}
- {...}

## 10. Known unknowns (optional — emit when coverage is absent or provenance is soft)
- {Coverage gap, unresolved decision, unstated target, or assumption, stated plainly}
```
