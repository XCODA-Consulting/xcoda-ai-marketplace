# Readiness — Stage 1

Read the architecture, supporting requirements, source validation, and relevant current
code in full. Find implementation constraints such as existing deployment paths,
migrations, external access, and integration environments without changing the design.

## Spec-architect handoff

Start with `design.md` and `validation.md`. Read `requirements.md` for the acceptance
criterion text; read blueprint/research when boundaries or decisions require context.
Require a passing report and agreement that it covers the current design. If the design
changed after validation, return to spec validation before declaring readiness.

Declare all source locations, preserve `R1.1`-style IDs and exact component names, and
map each inventory item to a source/section. Set readiness kind to `spec-architect` and
`validation_source` to the declared report source ID. The plan validator checks that
reference exists; it does not rerun spec validation or prove the report is current.

## Other architecture formats

Read the actual design and requirements, regardless of format. Review whether:

- Scope and observable acceptance criteria are agreed.
- Component boundaries, interfaces, and relevant failure behavior are specified.
- Data changes, integrations, and compatibility constraints are decided where needed.
- Remaining uncertainty affects execution logistics rather than architecture.

Preserve existing IDs; assign stable local criterion IDs such as `C1` if absent.
Use exact component names as IDs; when a source name contains spaces, use a stable
local token and retain the exact name in its description/source mapping.
Record readiness kind `reviewed`, with the review evidence and agreement. Describe this
as a readiness review, not a mechanically verified architecture.

## Record the outcome

Use `reference/PlanFormat.md` and `reference/PlanTemplate.json` to begin `plan.json`.
Record the source, criteria, and component inventories without adding requirements.
Set status `pending` until reviewed, `blocked` for unresolved design decisions, and
`ready` only after the applicable review. Evidence states what was reviewed, by whom
when known, and what agreement or existing authorization allows planning to proceed.
Do not fabricate approval.

External logistics (for example, staging credentials) belong in external prerequisites.
A decision about authentication behavior belongs in design blockers. Retain blockers
and ask the design owner; a blocked draft cannot receive a structural pass.

**Gate:** agree that these inputs are ready for planning, or record concrete design gaps.
