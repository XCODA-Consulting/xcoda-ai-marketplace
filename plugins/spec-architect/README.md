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

Available for Claude, Codex CLI, and ChatGPT. First add the marketplace using the
[installation instructions](../../README.md#installation), then install this plugin:

**Claude Code**

```bash
claude plugin install spec-architect@xcoda-ai-marketplace
```

**Codex CLI**

```bash
codex plugin add spec-architect@xcoda-ai-marketplace
```

In ChatGPT desktop, choose **XCODA AI Marketplace** in the Plugins Directory and install
**Spec Architect**. Workspace admins can also [import the GitHub marketplace](../../README.md#chatgpt-workspace-github-import).
Start a new chat or CLI session after installation.

## What's included

Paths below are relative to `skills/spec-architect/`, the directory containing `SKILL.md`.
Installed hosts may copy that directory into a cache; resolve resources from the loaded
skill's location rather than the current working directory.

- **Skill** — `spec-architect`, routing across the five phase workflows.
- **Workflows** — `Research.md`, `Blueprint.md`, `Requirements.md`, `Design.md`, `Validation.md`, each with its output template and gate.
- **Reference** — `reference/ExampleRun.md`, a complete two-component worked example (Redis-backed rate limiter), validated to pass.
- **Tool** — `scripts/validate_spec.py`:

  ```bash
  python3 "<absolute-skill-dir>/scripts/validate_spec.py" --path "<absolute-output-dir>"
  ```

  Replace the placeholders with the installed skill directory and the project's output
  directory. The report is written to the output directory, including when run elsewhere.

  | Check | Fails when |
  |---|---|
  | coverage | a criterion is claimed by no component |
  | references | a `Satisfies` line names a criterion that does not exist |
  | naming | the blueprint roster and the design's sections disagree |
  | evidence | a finding cites an undeclared source, or a source is never cited |

## Prerequisites

- Access to the requirements and sources, plus a target directory for the generated documents.
- **Python 3** and script execution for mechanical validation. The validator uses the standard library.
- If the host cannot execute Python or access the bundled script, author the documents and
  provide the resolved validation command. Report **validation pending**; the design is
  ready for planning only after the script runs successfully and generates a passing report.

## Usage

```
"Spec the architecture for webhook retry delivery. Here's the DoD: @webhook-retry-dod.md"
"I need an architecture spec for a rate limiter service, Redis-backed"
```

When validation passes, `design.md` and `validation.md` are the handoff pair for
the companion [plan-architect](../plan-architect), with `requirements.md` providing
the criterion text. It creates walking-skeleton milestones and actionable tasks, then
checks plan coverage and dependency consistency. This skill's output is that step's input.

## Relationship to `dod-architect`

The companion [`dod-architect`](../dod-architect) plugin produces the DoD that Phase 3 mines. Both share a source-citation style (`[S1]`-style ids declared once and referenced inline), so the documents read as one system.
