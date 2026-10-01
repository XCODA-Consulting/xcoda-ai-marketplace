# Validation — Stage 4

**Prerequisite:** `plan.json` contains the source inventories, readiness outcome,
milestones, tasks, risks, and prerequisites defined in `reference/PlanFormat.md`.

Resolve the script from the loaded skill directory, and the output directory from the
user's project. Do not assume execution starts in the skill or output directory.

```bash
python3 "<absolute-skill-dir>/scripts/validate_plan.py" --path "<absolute-output-dir>"
```

The script reads `plan.json`, generates `plan.md` and `plan-validation.md`, and leaves
the JSON and upstream sources unchanged. Exit `0` means a structural pass; `1` means
invalid JSON or a failed structural check; `2` means invocation/file-access failure.
Invalid inputs generate failing diagnostics when file access permits it. An access
failure may leave previous artifacts; inspect the exit code and do not cite them as new.

| Check | Failure |
|---|---|
| Format | Missing/unknown fields, wrong types, duplicate JSON keys or IDs, empty inventories |
| Sources | Criterion/component source mapping or validation-source reference is missing/dangling |
| Readiness | Pending/blocked readiness or unresolved design blockers |
| Coverage | A criterion/component has no task, or a milestone has no tasks |
| References | A task names an unknown milestone, criterion, component, or prerequisite |
| Dependencies | Unknown dependency, self-dependency, cycle, or task edge contradicting milestone order |

Fix the plan, not the requirements, to resolve coverage problems. Do not remove real
requirements or blockers to obtain a pass. Unknown design decisions go upstream.

## Review the generated plan

After a pass, confirm the sources/readiness evidence are honest, the first slice crosses
real integration boundaries, demonstrations prove the outcomes, tasks are actionable,
and rollout/rollback considerations fit the project. Confirm the review gates were
satisfied or explicitly authorized as part of a full workflow request.

**Gate:** structural validation passed and semantic review complete. Hand off the
JSON, readable plan, and report, with pending external prerequisites and unassigned
scheduling information called out. This does not authorize executing the tasks.

If Python/script/filesystem access is unavailable, deliver the JSON and resolved command
with **validation pending**. Do not author substitute generated Markdown or a passing
report; provide a brief chat description if needed for review.
