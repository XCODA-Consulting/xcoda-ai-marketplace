---
name: plan-architect
description: Turn an agreed architecture into a structurally validated execution plan with walking-skeleton milestones, actionable tasks, dependencies, acceptance gates, and rollout considerations. Use for "plan the implementation", "sequence the rollout", "break this design into milestones", or an execution plan from a validated spec. Requirements authoring and architecture design belong upstream.
---

# PlanArchitect

Answer **when, and in what order** from a design that is ready to implement. Preserve
its requirements, component names, interfaces, and scope; surface missing design
decisions as blockers instead of solving them inside the plan.

## Workflow

| Stage | Read | Result |
|---|---|---|
| 1. Readiness | `Workflows/Readiness.md` | Source inventory, traceable criteria/components, explicit design readiness |
| 2. Milestones | `Workflows/Milestones.md` | Demonstrable vertical slices and milestone dependency graph |
| 3. Tasks | `Workflows/Tasks.md` | Buildable tasks, verification, dependencies, external prerequisites |
| 4. Validation | `Workflows/Validation.md` | Generated readable plan and structural validation report |

Request agreement after readiness and milestone design. Respect an explicit request
to complete the whole workflow; it authorizes advancing those gates with recorded
assumptions, but does not resolve a missing architecture decision. Ask about a blocker
when needed, and keep independent draft work moving.

## Artifacts

- **`plan.json`** is the authoritative editable plan. Read `reference/PlanFormat.md`
  before authoring; `reference/PlanTemplate.json` is a deliberately pending starting point.
- **`plan.md`** is generated for review, including coverage inventories, milestones,
  tasks, risks, and scheduling information.
- **`plan-validation.md`** is generated with coverage tables, dependency diagnostics,
  and a structural verdict.

Read `reference/ExampleRun.md` for a complete reviewed-design example and
`reference/ExamplePlan.json` for its runnable plan. Other design formats are supported
through a readiness review; the companion `spec-architect` is not a runtime dependency.

## Planning rules

1. **Mine the design.** Read the supplied architecture and supporting requirements in
   full. Preserve criterion IDs and exact component names. Assign local IDs only when
   the source lacks them, with source locators making the mapping reviewable.
2. **Integrate early.** Default to the smallest executable path across real integration
   boundaries, then deepen behavior and failure handling. A stub can unblock work but
   is not proof of the real integration. Explain a justified departure from vertical slicing.
3. **Make completion observable.** Each milestone has an end-to-end demonstration and
   acceptance gates; each task names concrete work and verification. Mechanical coverage
   alone does not establish that a slice is useful or implementable.
4. **Keep the graph honest.** Distinguish task dependencies from milestone dependencies
   and external prerequisites. Parallel work is permitted when prerequisites allow it.
5. **Keep scheduling factual.** Include supplied owners, estimates, and dates; otherwise
   leave them null or absent. Never infer a commitment from an estimate or invent capacity.

The plugin plans work; it does not implement tasks, change upstream documents, publish
tracker tickets, or redesign architecture. Refer requirements gaps to `dod-architect` and
design gaps to `spec-architect` or the project's design owner.

## Paths and execution

Resolve workflows, references, and scripts relative to the directory containing this
loaded `SKILL.md`, including installed caches. Use the host's resource reader for URI
resources. For shell execution, resolve and quote absolute script and output paths.
Generated artifacts belong in the user's project/output directory, defaulting to the
project's current directory; never write them into the installed plugin directory.

```bash
python3 "<absolute-skill-dir>/scripts/validate_plan.py" --path "<absolute-output-dir>"
```

Python 3.9+ and filesystem access are required for the standard-library validator.
It overwrites only `plan.md` and `plan-validation.md`; edit `plan.json`, not generated prose.
If execution or access is unavailable, report **validation pending**, provide the resolved
command, and do not claim a pass or author a substitute passing report.

A passing report establishes structural consistency. Readiness still depends on the
recorded design review and agreement on the milestones; pending external prerequisites
must be satisfied before dependent tasks begin.
