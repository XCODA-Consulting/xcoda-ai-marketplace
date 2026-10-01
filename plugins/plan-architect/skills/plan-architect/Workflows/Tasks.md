# Tasks — Stage 3

**Prerequisite:** milestone sequence agreed, or authorization to draft the whole workflow.

Break milestones into work an implementer can pick up without re-deciding architecture.
Keep interface signatures and behaviors anchored to the design, and describe code,
configuration, migration, and verification work at the level the project needs.

## Record in plan.json

Each task has an ID, title, one milestone, concrete `work`, task `depends_on` IDs,
criterion/component references, external `prerequisites`, and observable `verification`.
Use empty reference arrays explicitly for enabling tasks that implement no criterion or
component themselves. Every inventory criterion and component still needs task coverage.

References indicate work toward a requirement; they do not establish that the task
satisfies it. Include tests or other verification that substantiate each claimed behavior.
Do not pad the plan with tests that merely mirror low-impact implementation details.

Model real prerequisites. Tasks can run in parallel inside a milestone. If a task needs
work from another milestone, that milestone must be an ancestor of its own milestone.
Do not create a dependency from an earlier slice to a later slice merely to make coverage
complete; move the work or fix the sequence.

Declare external prerequisites separately, with `available` or `pending` status. Tasks
reference their prerequisite IDs rather than disguising them as missing task IDs. A
pending prerequisite does not invalidate the graph but prevents its tasks from starting.

Carry supplied scheduling fields only. Record risks and mitigations, including integration
access or release constraints, without reopening architecture or adding unasked scope.

Before validation, review that every milestone is demonstrable, its gates are sufficient,
and the tasks cover real behavior rather than just naming each component.
