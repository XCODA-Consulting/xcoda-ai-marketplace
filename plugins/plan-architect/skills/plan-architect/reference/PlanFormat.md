# Plan JSON format

`plan.json` is authoritative. The validator reads UTF-8 JSON and rejects duplicate keys,
non-JSON numbers, unknown fields, and incorrect types. All fields below are required
unless marked optional. Text is plain text, not Markdown; the renderer escapes it.

IDs are nonempty strings with no whitespace and are unique within their collection.
Preserve native IDs and exact component names where representable. An ID with spaces
needs a local token and the exact original name in its description/source mapping.
Reference lists contain unique IDs. Arrays preserve authoring order; successful rendering
orders milestones/tasks by their dependency graphs, preserving declaration order among
simultaneously ready items. A failed graph renders in declaration order as a draft.

## Root fields

| Field | Type / meaning |
|---|---|
| `title`, `summary` | Nonempty strings; feature and intended delivered outcome |
| `strategy` | `walking-skeleton` or `alternative` |
| `strategy_rationale` | Nonempty explanation of the actual slice or justified departure |
| `sources` | Nonempty source array |
| `readiness` | Readiness object |
| `criteria`, `components` | Nonempty inventories mined from the agreed inputs |
| `milestones`, `tasks` | Nonempty arrays |
| `risks` | String array; can be empty; include mitigation in each risk's text |
| `external_prerequisites` | Prerequisite array; can be empty |

## Sources and inventories

Each source: `id`, `location`, `description` (nonempty strings). Location may be a file
path, URL, or host resource identifier. The validator does not fetch sources, verify
their completeness, or establish that they were read; the readiness review does that.

Each criterion: `id`, `text`, `source_refs`.
Each component: `id`, `description`, `source_refs`.
`source_refs` is a nonempty array of objects with `source` (declared source ID) and
`locator` (nonempty heading, section, line range, or native item reference). Preserve
the acceptance meaning. Local IDs bridge formats; they do not permit inferred scope.

## Readiness

| Field | Meaning |
|---|---|
| `kind` | `spec-architect` or `reviewed` |
| `status` | `ready`, `pending`, or `blocked` |
| `evidence` | Nonempty review record: inputs reviewed, relevant agreement, and limitations |
| `blockers` | String array of unresolved design decisions; must be empty for a pass |
| `validation_source` | Declared report source ID; required for `spec-architect`, optional otherwise |

For spec-architect inputs, a passing current report plus readiness agreement is required
by the workflow. For other formats, explicit review covers scope, acceptance, interfaces,
and unresolved design decisions. The script checks the declarations, not the review's
truth or report freshness. A structural pass is not an architecture validation pass.

## Milestones

Each object: `id`, `title`, `outcome`, `depends_on`, `demo`, `acceptance`, `rollout`,
`rollback`. All except arrays are nonempty strings. `depends_on` is an array of milestone
IDs; it may be empty. `acceptance` is a nonempty string array of checkable gates.
`demo` describes an end-to-end demonstration. `rollout` and `rollback` specify relevant
release considerations or explicitly explain why they do not apply.

## Tasks

Each object: `id`, `title`, `milestone`, `work`, `depends_on`, `criteria`, `components`,
`prerequisites`, `verification`. Text fields are nonempty strings. `milestone` names one
milestone. `depends_on` contains task IDs. `criteria`, `components`, and `prerequisites`
contain IDs from their respective inventories. Those arrays may be empty for enabling
work. `verification` is a nonempty string array of observable completion checks.

Every criterion and component must be referenced by a task; every milestone must have
tasks. Graphs reject cycles, unknown dependencies, and self-dependencies. A task edge
across milestones requires the prerequisite milestone to be a direct or transitive
ancestor of the dependent milestone. JSON position alone is not a prerequisite.

## External prerequisites and scheduling

Each prerequisite: `id`, `description`, `status` (`available` or `pending`). Pending
external logistics are allowed in a structural pass but must be resolved before dependent
tasks begin. Unresolved architecture decisions belong in readiness blockers instead.

Milestones, tasks, and prerequisites may optionally carry `owner`, `estimate`, and `date`:
nonempty strings or null. Preserve supplied values; no scheduling syntax or feasibility
is mechanically validated. Absent/null owners render as unassigned, estimates/dates as
unknown. Do not fabricate dates, people, effort, or capacity.

## Outputs and limits

The command takes `--path` (default current directory), reads only `plan.json`, and
overwrites only `plan.md` and `plan-validation.md` there. Input and sources are preserved.
Linked output files are refused to prevent overwriting a different input through an alias.
Missing/unreadable files are access errors (`2`), invalid content is validation failure
(`1`), and structural success is `0`. Generated Markdown does not contain a timestamp,
so identical inputs produce identical output.

The template starts pending with empty inventories and intentionally fails validation.
The worked example is complete and passes. Passing checks cannot establish semantic
requirement coverage, good slicing, source authenticity, or implementation correctness.
