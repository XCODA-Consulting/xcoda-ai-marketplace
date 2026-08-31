# dod-architect

Author a **Definition of Done (DoD)** grounded in whatever source material actually exists — so an engineer picking up a project has enough context to design the architecture around real needs, not just a checklist to test against.

## Overview

Point it at whatever exists — a folder of docs, a transcript, a tracker ticket, existing code, a prior PRD — and it mines that material the same way regardless of format. No fixed source taxonomy to configure; the methodology is the constant.

The differentiator versus a plain acceptance-criteria list is a **Design context** section that extracts the architecture-shaping constraints buried in the source material, each stated as a concrete *design implication*, with every requirement labeled by provenance relationship (`Source:` / `Derived from:` / `Must not break:`) — not just tagged to a source, but honest about whether that source actually asked for what's being claimed. The skill produces:

1. **The DoD** — Markdown in a fixed 9(+1)-section structure, optionally rendered to a Google Doc with clean headings, bold emphasis, and readable spacing.
2. *(Optional)* **A project-tracker brief** — a short orientation note that links the DoD (design context lives in the DoD, not duplicated into the tracker).

## Installation

```bash
claude plugin install dod-architect@xcoda-ai-marketplace
```

## What's included

### Skill

- **dod-architect** — the authoring playbook: a 5-step methodology (locate every source that bears on the feature → read each in full → extract design context → separate the MVP slice from the full ask → label provenance by relationship), the 9-section structure, writing principles, and the optional render/align mechanics.

### Reference

- `reference/DoDTemplate.md` — fill-in skeleton of the 9 sections (plus the optional §10) with inline authoring notes.
- `reference/ExampleRun.md` — a complete worked example (webhook retry delivery) built from a brainstorm doc and a customer escalation thread — deliberately informal, mixed sources, not a formal PRD.

### Tool

- `scripts/render_dod_to_gdoc.py` — renders a DoD authored in a small Markdown dialect into a Google Doc (headings, bold, hanging-indent bullets, grouped GIVEN/WHEN/THEN, auto-stripped inherited list bullets). Supports `--dry-run`. Purely a Markdown-dialect renderer — no dependency on any particular source taxonomy.

## Prerequisites

- Nothing is required to author the DoD itself — it's a Markdown document produced from whatever sources you point at.
- **`gws` CLI** ([googleworkspace/cli](https://github.com/googleworkspace/cli)), authenticated — only needed if rendering to Google Docs.
- A tracker MCP or API access — only needed if aligning a project-tracker brief.

## Usage

```
"Create a DoD for webhook retry delivery — here's the brainstorm doc and the customer escalation thread"
"Enrich this DoD, it's currently just a UAC list"
"DoD for this bug-driven feature, there's no PRD, just the bug report"
```

The skill reads whatever sources exist (asking what's available if none are given), extracts design context with provenance labels, authors the DoD, and — only if a target exists — renders it and aligns a tracker brief.

## Relationship to `spec-architect`

Once a DoD exists, hand it to the companion [`spec-architect`](../spec-architect) plugin to produce a verified architecture/design specification (components, interfaces, requirements traceability). This skill deliberately stops at "what and why, with constraints" — it does not design the solution.
