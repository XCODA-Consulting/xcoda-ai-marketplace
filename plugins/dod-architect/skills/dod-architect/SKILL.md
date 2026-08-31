---
name: dod-architect
description: Author or enrich a Definition of Done (DoD) grounded in whatever source material actually exists — arbitrary documents, transcripts, tickets, existing code, a prior PRD — not a fixed input taxonomy. USE WHEN "create a DoD", "write a DoD", "enrich the DoD", "DoD for <feature>", "scope this so an engineer can design against it", OR user wants a requirements document that gives an engineer enough context to design the architecture thoughtfully, not just a checklist to test against.
---

# DoDArchitect

A DoD produced by this skill is not just acceptance criteria. Its job is to give the engineer picking up a project **enough context to design the architecture thoughtfully around real needs** — not just a checklist to test against. The differentiator versus a plain UAC list is a **Design context** section that extracts the architecture-shaping constraints buried in the source material, each stated as a concrete *design implication*.

This skill is source-agnostic by design: point it at whatever exists — a folder of docs, a transcript, a Linear/Jira/GitHub issue, an existing codebase, a prior PRD — and it mines that material the same way regardless of format. There is no fixed source taxonomy to configure; the methodology is the constant, the sources are whatever the project actually has.

## Output

One artifact: **the DoD**, authored as Markdown in the dialect below. Optionally, two companions:
- Rendered to a Google Doc via `scripts/render_dod_to_gdoc.py` (requires the `gws` CLI, authenticated).
- A short project-tracker brief (Linear, GitHub, Jira — whatever the project uses) that **links** the DoD rather than duplicating it. Design context lives in the DoD; the brief just orients and points there.

Read `reference/ExampleRun.md` for a complete worked example, and `reference/DoDTemplate.md` for a fill-in skeleton.

## Methodology — how to build a DoD that enables good design

1. **Locate every source that bears on this feature.** There's no fixed list — read what the project actually has: a PRD, a requirements doc, a transcript of a scoping call, a Linear/GitHub/Jira issue thread, existing code (comments, docstrings, tests), a spreadsheet, a Slack thread export, a customer email. If the user hasn't pointed you at sources, ask what exists before inventing anything. Treat a prior PRD or DoD as a source like any other — read it in full, don't just skim its headings.

2. **Read every relevant source in full**, not just the paragraph that seems to apply. Narrative sources (transcripts, process docs, threads) carry context in what comes before and after the sentence that names the feature — read the neighbors. A spreadsheet row's adjacent rows, a ticket's linked issues, a code comment's surrounding function: all of it is part of the source, not just the line that happens to mention your feature.

3. **Extract the Design Context — this is the core work.** Scan every source for language that constrains architecture, not just behavior. Signals to hunt for:
   - hard prohibitions / security invariants ("**never** expose the private key", "credentials remain private", "only authorized context")
   - required execution paths ("through the audit log", "under policy enforcement", "must go through the gateway")
   - data-model shape ("multiple endpoints under one identity", "chained/ordered flows", "must be versioned")
   - cross-cutting requirements (audit, lineage, provenance, entitlement re-checks, idempotency)
   - encodings / formats / scale the system must handle
   For each, write a short paragraph: *what the source says* → **Design implication:** *what the engineer must do about it*. A DoD that stops at UACs and skips this section produces the wrong architecture — that is exactly what this section prevents. If a genuinely thorough read of the sources turns up nothing that constrains architecture (a purely additive, low-risk change against a well-understood system), say so plainly rather than padding the section — an empty Design Context with a one-line "no architecture-shaping constraints found" note is honest; invented constraints are not.

4. **Separate the MVP slice from the full ask.** Most projects are a deliberate cut of something larger. Be explicit about the boundary: it drives **Scope**, **Design seams** (where to leave room so a follow-on doesn't force a rewrite), and **Out of scope** (with pointers to what's deferred and where it lands).

5. **Label provenance by relationship, not by convenience.** A citation must say *which* relationship it carries. Three labels, and they are not interchangeable:

   | Label | Means | What the quoted clause looks like |
   |---|---|---|
   | `Source:` | Where the requirement came from — the source that actually asked for it | **asks for what the UAC asserts** |
   | `Derived from:` | Material the requirement is patterned on, which does not itself ask for it | describes the pattern |
   | `Must not break:` | An existing workflow this feature attaches to, or must not regress | describes the workflow |

   One criterion decides the label, and it is the same every time: **does the clause you cite ask for what the UAC asserts?** No source is privileged or disqualified by its type (a spreadsheet row is not more authoritative than a Slack thread, a formal PRD is not more authoritative than a transcript) — it earns `Source:` on exactly those terms.

   Two rules make the labels honest:
   - **Quote or demote.** For every source you cite, quote the specific clause you're relying on. If it asks for what the UAC asserts, it can be a `Source:`. If it does not, demote it — to `Derived from:` when you're borrowing its pattern, or to `Must not break:` when you're naming a workflow the feature attaches to or must not regress. A source that merely mentions the feature's domain is not enough; inference from proximity is how invented scope gets laundered into something that reads as requested.
   - **Capability gate.** A UAC asserting *new capability* must carry a `Source:` — a citation whose quoted clause actually asks for what that UAC asserts. `Derived from:` and `Must not break:` cannot satisfy this gate, alone or together. If nothing you can cite asks for it, the requirement was inferred: record it in §10 (Known unknowns) as proposed and unsourced, say who needs to decide, and keep it out of §7.

   `Must not break:` can carry two different relationships — *attaches to* (this feature's state surfaces on an existing dashboard) and *must not regress* (an existing test must keep passing). Say which one you mean in the parenthetical; it decides what the engineer builds.

   If something is unknown or assumed, say so plainly — the engineer needs to know where the fuzzy edges are.

## When no source addresses the feature

Some projects arrive from an escalation, a defect, or a customer thread rather than from any planning artifact. Check thoroughly before concluding this, then **say it plainly instead of manufacturing coverage.** A feature whose requirement lives only in a thread or in the code is a normal case, not a failure.

When there is no covering source:
- **Declare the gap in Section 3, before the bullets.** One short paragraph: no source describes this feature directly; here is what the related material *is* for.
- **Reframe Section 3 as integration points.** Related material still earns its place — it marks where the feature's material enters, where its state must surface, and which workflows it must not break. That's a genuinely useful constraint set; don't delete the section, and don't let it masquerade as a requirements source.
- **Name the real requirement source in Section 2 and on every UAC** — the ticket, the thread, the code, the conversation with the requester.
- **Emit Section 10 (Known unknowns).** Lead with the coverage gap, then any unresolved decisions, unstated targets, and assumptions.

## The 9-section structure (+ optional 10th)

1. **Summary** — what the user/operator can do end-to-end after this ships, in 3 sentences. State plainly if it's a slice of something larger, and name the follow-on.
2. **Why this matters** — the framing: which goal/initiative this serves, why it's needed now, what it unblocks downstream.
3. **Source material** — the sources this draws from, one bullet each, with a "read these before designing" instruction. If no source covers the feature, open with the gap declaration (see above) instead.
4. **Design context — read before designing** — the extracted constraints, grouped by sub-topic with `### ` headings, each ending in a **Design implication:**. *This section is what makes the DoD worth reading.*
5. **Persona** — primary (and secondary) users/personas, one line each.
6. **Preconditions** — deployment/access/test-data assumptions as bullets.
7. **User acceptance criteria** — grouped by capability (`### `), each UAC a `#### ` heading with a GIVEN/WHEN/THEN block and one or more provenance lines (`Source:` / `Derived from:` / `Must not break:`) per the taxonomy above.
8. **Design seams / forward-compatibility** — bullets telling the engineer where to leave room for a follow-on so this slice isn't a rewrite later. Each cites its source.
9. **Out of scope** — bullets with source pointers to what's deferred and where it lands.
10. **Known unknowns** *(optional)* — emit when source coverage is absent or provenance is soft. State plainly where the edges are: the coverage gap, unresolved decisions, unstated targets, assumptions the first slice must not bake in.

## Writing principles

- **Trace everything, but cite the *actual* origin.** A claim an engineer can't verify is a claim they'll ignore. A source earns `Source:` only when the clause you quote actually contains the thing the UAC asserts; otherwise the honest citation is whatever the real origin is, with the stronger-looking source demoted to `Must not break:`. Never upgrade a weak citation because a stronger-looking source is available — that's how invented scope gets laundered into something that reads as requested.
- **Every design-context item ends in a design implication.** Description without "so build it this way" is trivia. The implication is the payload.
- **State the MVP/full-scope boundary everywhere it matters** — Summary, Scope, seams, Out of scope. Ambiguous scope hurts design more than missing detail.
- **Be honest about unknowns.** Preserve candor ("no catalog exists", "assumed"). Provenance you can't stand behind erodes trust in the whole doc.
- **Right altitude.** The DoD frames *what and why* and the constraints; it does not design the solution. Leave the architecture to the engineer — that's a separate downstream step (an architecture/spec skill; see the companion [`spec-architect`](../spec-architect) plugin). Give the engineer what they need to do it well, not a design already made for them.
- **No version numbers in prose**, if the target release moves independently of the doc — a version in a heading or precondition line goes stale the moment a release slips; carry it in the tracker's label/field instead, where it's one edit, not a doc-wide search-and-replace.

## Producing the Google Doc (optional)

Author the DoD as Markdown (dialect below), then render:

```bash
# validate first (no changes):
python scripts/render_dod_to_gdoc.py --doc-id DOC_ID --md path/to/dod.md --dry-run
# then apply (replaces the whole doc body, atomically):
python scripts/render_dod_to_gdoc.py --doc-id DOC_ID --md path/to/dod.md
```

Requires the `gws` CLI installed and authenticated (`gws docs documents …`). The doc must already exist — create it first and grab its id from the URL (`/document/d/<DOC_ID>/edit`). If there's no Google Docs target, the Markdown file is the deliverable — don't force a render.

Markdown dialect (full details in the script header): `#`..`####` headings · `- ` bullets (render as "• " with hanging indent) · blank line = paragraph break · `**bold**` · a `GIVEN…/WHEN…/THEN…` block on consecutive lines renders as one grouped paragraph · a provenance line (`Source:` / `Derived from:` / `Must not break:`) gets extra space below, and consecutive provenance lines stay on separate lines. One line per flowing paragraph — GWT clauses and provenance labels are the only intentional line breaks.

## Producing / aligning a project-tracker brief (optional)

If the project has a tracker (Linear, GitHub, Jira, whatever), keep its description a short brief, not a second DoD:
- Lead with a `**DoD:**` link line to the rendered doc (or the Markdown file's location).
- Keep the "why it matters" narrative and scope in brief form. Do not paste the design context — that lives in the DoD.
- **Align name and summary to the DoD.** If they disagree about what the project is, resolve the scope with the user first — mismatched framing across artifacts undercuts the whole point.

## Quality checklist (before calling a DoD done)

- [ ] Every referenced source was actually read in full (not just cited).
- [ ] Design context has ≥1 item per non-trivial architecture-shaping constraint found, each with a design implication — or an explicit "none found" note if the sources genuinely carried none.
- [ ] Every UAC carries at least one provenance label.
- [ ] Every source citation on a **provenance line** reproduces the operative words of the clause it relies on — verbatim for the phrase doing the work — so a reviewer can check the claim. (§3/§4/§8/§9 pointers need no quote.) Wherever the label is `Source:`, those words ask for what the UAC asserts.
- [ ] Every capability-asserting UAC has a `Source:` whose quoted clause asks for what that UAC asserts. A UAC carrying only `Derived from:` / `Must not break:` was inferred — it belongs in §10 as proposed and unsourced, not in §7 as though someone asked for it.
- [ ] If no source covers the feature: the gap is declared in Section 3, and Section 10 exists.
- [ ] MVP/full-scope boundary is explicit in Summary, seams, and Out of scope.
- [ ] Design seams tell the engineer where to leave room for a follow-on.
- [ ] Unknowns/assumptions are stated, not hidden.
- [ ] If rendered: doc renders clean (correct outline, bold intact, no stray bullets, readable spacing).
- [ ] If a tracker brief exists: it links the DoD; name/summary aligned; no design-context duplication.

## Examples

**Example 1: create a new DoD from mixed sources**
```
User: "Create a DoD for webhook retry delivery. Here's the design brainstorm doc, and the
       customer escalation thread that started this."
-> Read both sources in full, plus any linked issues
-> Extract design context (each ending in a Design implication) — e.g. "escalation says
   retries must not duplicate side effects" -> "Design implication: delivery must be
   idempotent, keyed on a caller-supplied idempotency token"
-> Author the 9-section DoD in Markdown; render to Google Docs if a target doc exists
```

**Example 2: enrich an existing thin DoD**
```
User: "This DoD is just a UAC list, enrich it"
-> Read the current DoD plus whatever original sources still exist
-> Add Why / Source material / Design context / Design seams; relabel UAC provenance by
   relationship — don't swap a real origin out for a stronger-looking source
-> Re-render; keep any tracker brief a short link-led summary
```

**Example 3: no source material exists**
```
User: "DoD for this bug-driven feature — there's no PRD, just the bug report"
-> The bug report + any linked thread IS the source; say so in Section 3
-> Extract what constraints it implies, cite it as Source: directly
-> Emit Section 10 noting the absence of a planning artifact and any assumptions made
```
