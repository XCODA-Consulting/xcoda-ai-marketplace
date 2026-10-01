# plan-architect

Turn an agreed architecture into an **execution plan**: when to deliver each outcome
and in what dependency order, with actionable tasks and observable completion gates.

The default is a walking skeleton: an early executable path across real integration
boundaries, deepened in later milestones. Requirements and architecture remain upstream.

## Workflow

1. **Readiness** — read the design and requirements, preserve source IDs and component
   names, and agree that design decisions are sufficiently complete for planning.
2. **Milestones** — choose vertical slices with demonstrations, acceptance gates, and
   rollout/rollback considerations. Review the proposed sequence.
3. **Tasks** — name concrete work, verification, dependencies, and external prerequisites.
4. **Validation** — run the bundled validator, fix structural gaps, and review the rendered plan.

Readiness and milestone review gates honor existing authorization to run the whole
workflow. Such authorization does not resolve missing design decisions.

## Inputs and deliverables

Accept a spec-architect handoff (`design.md`, passing `validation.md`, and supporting
`requirements.md`) or another design format after an explicit readiness review. A stale
or failed spec report needs upstream revalidation. Other formats are reviewed, not
claimed as mechanically verified architecture.

Author **`plan.json`** using the documented [format](skills/plan-architect/reference/PlanFormat.md)
and [pending template](skills/plan-architect/reference/PlanTemplate.json). The validator
generates **`plan.md`** and **`plan-validation.md`**. Edit the JSON, not generated prose.
Owners, dates, and estimates remain unassigned/unknown unless supplied. Pending external
prerequisites are visible and prevent dependent tasks from beginning.

## Validator

Requires **Python 3.9+**, script execution, and filesystem access; uses only the standard
library. Resolve resources relative to the loaded `SKILL.md` (including installed caches),
and keep generated files in the user's project/output directory.

```bash
python3 "<absolute-skill-dir>/scripts/validate_plan.py" --path "<absolute-output-dir>"
```

| Check | Fails when |
|---|---|
| Format | JSON is malformed, fields/types are invalid, IDs are duplicated, or inventories are empty |
| Readiness/sources | Design readiness is pending/blocked, or source references are missing/dangling |
| Coverage | A criterion/component has no task, or a milestone has no tasks |
| References | Tasks name unknown milestones, criteria, components, or external prerequisites |
| Dependencies | Graphs have unknown/self dependencies or cycles, or task edges contradict milestone order |

Exit `0`: structural pass; `1`: validation failure; `2`: invocation/file-access error.
Identical input produces identical Markdown. Only the two Markdown outputs are replaced;
JSON and upstream sources are preserved.

A structural pass checks declarations, not source authenticity, report freshness, real
requirement satisfaction, or whether a milestone is a useful slice. Review those aspects
before declaring the plan ready. If execution is unavailable, provide the JSON and
resolved command with **validation pending**; do not manufacture a passing report.

## Installation

First add the marketplace using the [root installation instructions](../../README.md#installation).

**Claude Code**

```bash
claude plugin install plan-architect@xcoda-ai-marketplace
```

**Codex CLI**

```bash
codex plugin add plan-architect@xcoda-ai-marketplace
```

In ChatGPT desktop, select **XCODA AI Marketplace** in the Plugins Directory and install
**Plan Architect**. Workspace admins can [import the GitHub marketplace](../../README.md#chatgpt-workspace-github-import).
Start a new chat or CLI session after installation.

## Usage and examples

```text
Plan the implementation from this design.md and passing validation.md. The supporting
requirements.md is included. Use walking-skeleton milestones and break them into tasks.

Turn this agreed architecture into an execution plan. Complete the full workflow;
we have not assigned owners or dates yet.
```

The [worked example](skills/plan-architect/reference/ExampleRun.md) provides complete
source snapshots and a [runnable plan](skills/plan-architect/reference/ExamplePlan.json).
Copy the latter to an output directory as `plan.json` and run the command above.

## What's included

Paths are relative to `skills/plan-architect/`:

- `SKILL.md` — skill routing and core planning rules.
- `Workflows/` — Readiness, Milestones, Tasks, and Validation guides.
- `reference/` — format contract, pending template, worked example, and complete JSON fixture.
- `scripts/validate_plan.py` — standalone validator and Markdown renderer.
- `tests/` — behavioral and command-line tests.

Run tests from the repository root:

```bash
python3 -m unittest discover -s plugins/plan-architect/skills/plan-architect/tests -v
```

The companion [dod-architect](../dod-architect) authors what and why;
[spec-architect](../spec-architect) designs the system's shape. This plugin sequences
implementation of that shape and does not execute tasks or create tracker tickets.
