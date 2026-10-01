#!/usr/bin/env python3
"""Validate plan.json; generate plan.md and plan-validation.md using only stdlib.

python3 validate_plan.py --path <output-directory>
Exit 0: structural pass; 1: invalid plan; 2: invocation or file-access error.
The validator checks declarations, not the truth of design/readiness reviews.
See reference/PlanFormat.md for the authoring contract.
"""
from __future__ import annotations

import argparse
import heapq
import json
import re
import sys
from pathlib import Path


class InvalidJSON(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidJSON(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise InvalidJSON(f"non-JSON number: {value}")


def text_value(value):
    return isinstance(value, str) and bool(value.strip())


def identifier(value):
    return text_value(value) and value == value.strip() and not any(c.isspace() for c in value)


def strings(value):
    return isinstance(value, list) and all(text_value(item) for item in value)


def nonempty_strings(value):
    return strings(value) and bool(value)


def references(value):
    return isinstance(value, list) and all(identifier(item) for item in value) and len(value) == len(set(value))


def object_fields(value, required, optional, path, errors):
    if not isinstance(value, dict):
        errors.append(f"{path}: expected an object")
        return False
    for key, check in required.items():
        if key not in value:
            errors.append(f"{path}.{key}: required field missing")
        elif not check(value[key]):
            errors.append(f"{path}.{key}: invalid type or value")
    for key, check in optional.items():
        if key in value and not check(value[key]):
            errors.append(f"{path}.{key}: invalid type or value")
    for key in sorted(value.keys() - required.keys() - optional.keys()):
        errors.append(f"{path}.{key}: unknown field")
    return True


def schema_errors(plan):
    errors = []
    is_list = lambda v: isinstance(v, list)
    root = {
        "title": text_value, "summary": text_value,
        "strategy": lambda v: v in ("walking-skeleton", "alternative"),
        "strategy_rationale": text_value, "sources": is_list,
        "readiness": lambda v: isinstance(v, dict), "criteria": is_list,
        "components": is_list, "milestones": is_list, "tasks": is_list,
        "risks": strings, "external_prerequisites": is_list,
    }
    if not object_fields(plan, root, {}, "plan", errors):
        return errors
    readiness = plan.get("readiness")
    if isinstance(readiness, dict):
        object_fields(readiness, {
            "kind": lambda v: v in ("spec-architect", "reviewed"),
            "status": lambda v: v in ("ready", "pending", "blocked"),
            "evidence": text_value, "blockers": strings,
        }, {"validation_source": identifier}, "readiness", errors)
        if readiness.get("kind") == "spec-architect" and "validation_source" not in readiness:
            errors.append("readiness.validation_source: required for spec-architect input")
    specs = {
        "sources": {"id": identifier, "location": text_value, "description": text_value},
        "criteria": {"id": identifier, "text": text_value, "source_refs": is_list},
        "components": {"id": identifier, "description": text_value, "source_refs": is_list},
        "milestones": {
            "id": identifier, "title": text_value, "outcome": text_value,
            "depends_on": references, "demo": text_value,
            "acceptance": nonempty_strings, "rollout": text_value, "rollback": text_value,
        },
        "tasks": {
            "id": identifier, "title": text_value, "milestone": identifier,
            "work": text_value, "depends_on": references, "criteria": references,
            "components": references, "prerequisites": references,
            "verification": nonempty_strings,
        },
        "external_prerequisites": {
            "id": identifier, "description": text_value,
            "status": lambda v: v in ("available", "pending"),
        },
    }
    schedule = {key: lambda v: v is None or text_value(v) for key in ("owner", "estimate", "date")}
    for collection, required in specs.items():
        items = plan.get(collection)
        if not isinstance(items, list):
            continue
        if not items and collection != "external_prerequisites":
            errors.append(f"{collection}: inventory must not be empty")
        for i, item in enumerate(items):
            path = f"{collection}[{i}]"
            optional = schedule if collection in ("tasks", "milestones", "external_prerequisites") else {}
            if not object_fields(item, required, optional, path, errors):
                continue
            if collection in ("criteria", "components") and isinstance(item.get("source_refs"), list):
                if not item["source_refs"]:
                    errors.append(f"{path}.source_refs: at least one source mapping required")
                for j, ref in enumerate(item["source_refs"]):
                    object_fields(ref, {"source": identifier, "locator": text_value}, {},
                                  f"{path}.source_refs[{j}]", errors)
    return errors


def topological_order(items):
    """Stable order preserving declaration order among simultaneously ready nodes."""
    position = {item["id"]: i for i, item in enumerate(items)}
    remaining = {item["id"]: set(item["depends_on"]) for item in items}
    children = {item["id"]: [] for item in items}
    for node, dependencies in remaining.items():
        for dependency in dependencies:
            children[dependency].append(node)
    ready = [(position[node], node) for node, dependencies in remaining.items() if not dependencies]
    heapq.heapify(ready)
    order = []
    while ready:
        _, node = heapq.heappop(ready)
        order.append(node)
        for child in children[node]:
            remaining[child].remove(node)
            if not remaining[child]:
                heapq.heappush(ready, (position[child], child))
    return order


def audit(plan):
    errors = schema_errors(plan)
    if errors:
        return errors
    collections = ("sources", "criteria", "components", "milestones", "tasks", "external_prerequisites")
    indices = {}
    for collection in collections:
        indices[collection] = {}
        for item in plan[collection]:
            if item["id"] in indices[collection]:
                errors.append(f"{collection}: duplicate ID {item['id']}")
            indices[collection][item["id"]] = item
    if errors:
        return errors

    def check_refs(refs, target, context):
        for ref in refs:
            if ref not in indices[target]:
                errors.append(f"{context}: unknown {target} reference {ref}")

    for collection in ("criteria", "components"):
        for item in plan[collection]:
            check_refs([ref["source"] for ref in item["source_refs"]], "sources", item["id"])
    readiness = plan["readiness"]
    if readiness["status"] != "ready" or readiness["blockers"]:
        errors.append("readiness: status must be ready with no unresolved design blockers")
    if "validation_source" in readiness:
        check_refs([readiness["validation_source"]], "sources", "readiness.validation_source")

    graph_valid = {}
    for collection in ("milestones", "tasks"):
        graph_valid[collection] = True
        for item in plan[collection]:
            for dependency in item["depends_on"]:
                if dependency == item["id"]:
                    errors.append(f"{item['id']}: self-dependency")
                    graph_valid[collection] = False
                elif dependency not in indices[collection]:
                    errors.append(f"{item['id']}: unknown {collection} dependency {dependency}")
                    graph_valid[collection] = False
        if graph_valid[collection]:
            if len(topological_order(plan[collection])) != len(plan[collection]):
                errors.append(f"{collection}: dependency cycle")
                graph_valid[collection] = False

    for task in plan["tasks"]:
        for field, target in (("milestone", "milestones"), ("criteria", "criteria"),
                              ("components", "components"), ("prerequisites", "external_prerequisites")):
            check_refs([task[field]] if field == "milestone" else task[field], target, task["id"])
    for collection in ("criteria", "components"):
        covered = {ref for task in plan["tasks"] for ref in task[collection]}
        for missing in sorted(indices[collection].keys() - covered):
            errors.append(f"{collection}: uncovered {missing}")
    used_milestones = {task["milestone"] for task in plan["tasks"]}
    for missing in sorted(indices["milestones"].keys() - used_milestones):
        errors.append(f"milestones: {missing} has no tasks")

    if graph_valid["milestones"]:
        ancestors = {}
        for mid in topological_order(plan["milestones"]):
            ancestors[mid] = set()
            for dependency in indices["milestones"][mid]["depends_on"]:
                ancestors[mid].add(dependency)
                ancestors[mid].update(ancestors[dependency])
        for task in plan["tasks"]:
            mid = task["milestone"]
            if mid not in ancestors:
                continue
            for dependency in task["depends_on"]:
                previous = indices["tasks"].get(dependency)
                if previous and previous["milestone"] != mid and previous["milestone"] not in ancestors[mid]:
                    errors.append(f"{task['id']}: dependency {dependency} contradicts milestone order; "
                                  f"{mid} must depend on {previous['milestone']}")
    return errors


def prose(value):
    # Values are plain text, not authored Markdown. Prevent embedded headings/tables.
    value = " ".join(str(value).split())
    for char in ("\\", "`", "*", "_", "[", "]", "<", ">", "|", "#", "&", "~"):
        value = value.replace(char, "\\" + char)
    # Paragraph-leading punctuation can create lists or thematic breaks. Escape
    # only the marker; keep periods/hyphens in identifiers and URLs readable.
    if value.startswith(("-", "+", "=")):
        value = "\\" + value
    value = re.sub(r"^(\d+)([.)])(?=\s|$)",
                   lambda match: match[1] + "\\" + match[2], value, count=1)
    return value


def refs(values):
    return ", ".join(prose(value) for value in values) or "none"


def schedule(item):
    return (f"Owner: {prose(item.get('owner') or 'unassigned')}; "
            f"estimate: {prose(item.get('estimate') or 'unknown')}; "
            f"date: {prose(item.get('date') or 'unknown')}")


def report_markdown(plan, errors):
    lines = ["# Plan Validation Report", "", "Generated from plan.json; do not edit.", "",
             "## Verdict", "", "**FAIL** — structural validation failed." if errors else
             "**PASS** — structural validation passed; semantic readiness requires review.", "",
             "Checks declarations and dependency consistency, not implementation correctness, "
             "source completeness, or the truth of the recorded readiness review."]
    if errors:
        lines += ["", "## Diagnostics", ""] + [f"- {prose(error)}" for error in errors]
    if not schema_errors(plan):
        for collection in ("criteria", "components"):
            lines += ["", f"## {collection.title()} coverage", "",
                      "| ID | Tasks | Milestones |", "|---|---|---|"]
            for item in plan[collection]:
                tasks = [task for task in plan["tasks"] if item["id"] in task[collection]]
                lines.append(f"| {prose(item['id'])} | {refs([t['id'] for t in tasks])} | "
                             f"{refs(sorted({t['milestone'] for t in tasks}))} |")
        lines += ["", "## Dependencies", ""]
        for collection in ("milestones", "tasks"):
            lines += [f"- {prose(item['id'])} depends on: {refs(item['depends_on'])}" for item in plan[collection]]
        lines += ["", "## External prerequisites", ""]
        lines += [f"- {prose(p['id'])}: {prose(p['status'])} — {prose(p['description'])}"
                  for p in plan["external_prerequisites"]] or ["- none"]
    return "\n".join(lines) + "\n"


def plan_markdown(plan, errors):
    if schema_errors(plan):
        return ("# Execution Plan — invalid input\n\nGenerated from plan.json; do not edit.\n\n"
                "The input cannot be rendered as a plan. See plan-validation.md for diagnostics.\n")
    lines = [f"# {prose(plan['title'])}", "", "Generated from plan.json; edit that file and rerun validation.", "",
             "**Status:** " + ("structural validation failed; draft only" if errors else
                                "structural validation passed; review gates still apply"), "",
             prose(plan["summary"]), "", "## Planning approach", "",
             f"{prose(plan['strategy'])}: {prose(plan['strategy_rationale'])}", "",
             "## Design readiness", "",
             f"- Kind: {prose(plan['readiness']['kind'])}",
             f"- Status: {prose(plan['readiness']['status'])}",
             f"- Review evidence: {prose(plan['readiness']['evidence'])}",
             f"- Design blockers: {refs(plan['readiness']['blockers'])}"]
    if "validation_source" in plan["readiness"]:
        lines.append(f"- Validation source: {prose(plan['readiness']['validation_source'])}")
    lines += ["", "## Sources", ""]
    lines += [f"- {prose(s['id'])}: {prose(s['location'])} — {prose(s['description'])}" for s in plan["sources"]]
    for collection in ("criteria", "components"):
        lines += ["", f"## {collection.title()} inventory", ""]
        for item in plan[collection]:
            mapping = "; ".join(f"{prose(r['source'])}: {prose(r['locator'])}" for r in item["source_refs"])
            lines.append(f"- {prose(item['id'])}: {prose(item.get('text', item.get('description')))} ({mapping})")
    lines += ["", "## Risks", ""] + ([f"- {prose(r)}" for r in plan["risks"]] or ["- none recorded"])
    lines += ["", "## External prerequisites", ""]
    for prerequisite in plan["external_prerequisites"]:
        lines += [f"- {prose(prerequisite['id'])}: {prose(prerequisite['description'])} "
                  f"({prose(prerequisite['status'])}); {schedule(prerequisite)}"]
    if not plan["external_prerequisites"]:
        lines.append("- none")
    milestones = plan["milestones"]
    tasks = plan["tasks"]
    # Failed graphs render in declaration order, never suggest a verified execution order.
    if not errors:
        milestone_index = {m["id"]: m for m in milestones}
        task_index = {t["id"]: t for t in tasks}
        milestones = [milestone_index[mid] for mid in topological_order(milestones)]
        tasks = [task_index[tid] for tid in topological_order(tasks)]
    for milestone in milestones:
        lines += ["", f"## {prose(milestone['id'])} — {prose(milestone['title'])}", "",
                  prose(milestone["outcome"]), "",
                  f"**Depends on:** {refs(milestone['depends_on'])}", "", schedule(milestone), "",
                  f"**Demonstration:** {prose(milestone['demo'])}", "", "**Acceptance gates:**", ""]
        lines += [f"- {prose(check)}" for check in milestone["acceptance"]]
        lines += ["", f"**Rollout:** {prose(milestone['rollout'])}", "",
                  f"**Rollback:** {prose(milestone['rollback'])}"]
        for task in tasks:
            if task["milestone"] != milestone["id"]:
                continue
            lines += ["", f"### {prose(task['id'])} — {prose(task['title'])}", "", prose(task["work"]), "",
                      f"- Depends on: {refs(task['depends_on'])}",
                      f"- Criteria: {refs(task['criteria'])}", f"- Components: {refs(task['components'])}",
                      f"- External prerequisites: {refs(task['prerequisites'])}", f"- {schedule(task)}", "",
                      "**Verification:**", ""]
            lines += [f"- {prose(check)}" for check in task["verification"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=".", help="directory containing plan.json; receives both Markdown outputs")
    args = parser.parse_args(argv)
    root = Path(args.path).resolve()
    input_path = root / "plan.json"
    outputs = [root / "plan.md", root / "plan-validation.md"]
    try:
        raw = input_path.read_text(encoding="utf-8")
        # Refuse aliases before writing so symlinks/hardlinks cannot overwrite upstream inputs.
        for output in outputs:
            if output.is_symlink() or (output.exists() and output.stat().st_nlink > 1):
                raise OSError(f"refusing linked output: {output}")
        try:
            plan = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
            errors = audit(plan)
        except (ValueError, RecursionError) as exc:
            plan, errors = None, [f"invalid JSON: {exc}"]
        rendered_plan = plan_markdown(plan, errors)
        rendered_report = report_markdown(plan, errors)
        outputs[0].write_text(rendered_plan, encoding="utf-8")
        outputs[1].write_text(rendered_report, encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"File-access error: {exc}", file=sys.stderr)
        return 2
    print(rendered_report, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
