#!/usr/bin/env python3
"""Check a spec-architect document set for traceability and evidence gaps.

    python3 validate_spec.py --path <dir> [--out validation.md]

Reads blueprint.md, requirements.md, design.md and research.md from <dir>, writes a
validation report, and exits non-zero when anything is unproven. Four checks:

    coverage    every acceptance criterion is claimed by some component
    references  every claim points at a criterion that exists
    naming      blueprint and design agree on the component roster
    evidence    every research finding cites a listed source

Formats it reads (see the Workflows/ docs for the authoring templates):

    blueprint.md    | `ComponentName` | responsibility |
    requirements.md ## R1 — Title, then numbered criteria -> R1.1, R1.2, ...
    design.md       ## ComponentName, then **Satisfies**: R1.1, R2.3
    research.md     - [S1] https://...   with [S1] cited in the findings table
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

COMPONENT_CELL = re.compile(r"\|\s*`([A-Za-z0-9_.]+)`\s*\|")
REQUIREMENT_HEAD = re.compile(r"^##\s+R(\d+)\s*[—–-]\s*(.+)$", re.M)
CRITERION_LINE = re.compile(r"^\s*(\d+)\.\s+(\S.*)$", re.M)
DESIGN_SECTION = re.compile(r"^##\s+([A-Za-z0-9_.]+)\s*$", re.M)
SATISFIES_LINE = re.compile(r"^\*\*Satisfies\*\*:\s*(.+)$", re.M)
CRITERION_REF = re.compile(r"R(\d+)\.(\d+)")
SOURCE_ENTRY = re.compile(r"^-\s*\[(S\d+)\]\s*(\S+)", re.M)
SOURCE_REF = re.compile(r"\[(S\d+)\]")
FINDING_ROW = re.compile(r"^\|(?!\s*[-: ]+\|)([^|\n]+)\|([^|\n]+)\|", re.M)


@dataclass
class Requirement:
    number: str
    title: str
    criteria: dict[str, str] = field(default_factory=dict)


@dataclass
class Report:
    uncovered: list[str] = field(default_factory=list)
    dangling: list[str] = field(default_factory=list)
    undesigned: list[str] = field(default_factory=list)
    unplanned: list[str] = field(default_factory=list)
    evidence_gaps: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    total_criteria: int = 0
    covered_criteria: int = 0
    sources: int = 0
    citations: int = 0

    @property
    def coverage(self) -> float:
        if not self.total_criteria:
            return 0.0
        return self.covered_criteria / self.total_criteria * 100

    @property
    def ok(self) -> bool:
        return not any([self.uncovered, self.dangling, self.undesigned,
                        self.unplanned, self.evidence_gaps, self.missing_files]) \
            and self.total_criteria > 0


class SpecSet:
    """The four authored documents, loaded from a directory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.missing: list[str] = []
        self.blueprint = self._load("blueprint.md")
        self.requirements = self._load("requirements.md")
        self.design = self._load("design.md")
        self.research = self._load("research.md")

    def _load(self, name: str) -> str:
        path = self.root / name
        if not path.exists():
            self.missing.append(name)
            return ""
        return path.read_text(encoding="utf-8")

    def planned_components(self) -> set[str]:
        return set(COMPONENT_CELL.findall(self.blueprint))

    def specified_components(self) -> set[str]:
        return set(DESIGN_SECTION.findall(self.design))

    def requirements_index(self) -> dict[str, Requirement]:
        found: dict[str, Requirement] = {}
        heads = list(REQUIREMENT_HEAD.finditer(self.requirements))
        for i, head in enumerate(heads):
            number, title = head.group(1), head.group(2).strip()
            stop = heads[i + 1].start() if i + 1 < len(heads) else len(self.requirements)
            body = self.requirements[head.end():stop]
            entry = Requirement(number=number, title=title)
            for index, text in CRITERION_LINE.findall(body):
                entry.criteria[f"R{number}.{index}"] = text.strip()
            if entry.criteria:
                found[number] = entry
        return found

    def claims(self) -> dict[str, set[str]]:
        """Component -> the criteria its **Satisfies** line claims."""
        staked: dict[str, set[str]] = {}
        sections = list(DESIGN_SECTION.finditer(self.design))
        for i, section in enumerate(sections):
            name = section.group(1)
            stop = sections[i + 1].start() if i + 1 < len(sections) else len(self.design)
            body = self.design[section.end():stop]
            refs = {f"R{major}.{minor}"
                    for line in SATISFIES_LINE.findall(body)
                    for major, minor in CRITERION_REF.findall(line)}
            if refs:
                staked.setdefault(name, set()).update(refs)
        return staked

    def evidence(self) -> tuple[set[str], set[str], int]:
        """Return (declared source ids, ids cited in findings, citation count)."""
        declared = {sid for sid, _ in SOURCE_ENTRY.findall(self.research)}
        cited: set[str] = set()
        count = 0
        for _finding, rationale in FINDING_ROW.findall(self.research):
            refs = SOURCE_REF.findall(rationale)
            count += len(refs)
            cited.update(refs)
        return declared, cited, count


def audit(spec: SpecSet) -> tuple[Report, dict[str, Requirement], dict[str, set[str]]]:
    report = Report(missing_files=list(spec.missing))
    requirements = spec.requirements_index()
    claims = spec.claims()

    all_criteria = {cid for req in requirements.values() for cid in req.criteria}
    claimed = {cid for refs in claims.values() for cid in refs}

    report.total_criteria = len(all_criteria)
    report.covered_criteria = len(claimed & all_criteria)
    report.uncovered = sorted(all_criteria - claimed, key=criterion_order)
    report.dangling = sorted(claimed - all_criteria, key=criterion_order)

    planned, specified = spec.planned_components(), spec.specified_components()
    report.undesigned = sorted(planned - specified)
    report.unplanned = sorted(specified - planned) if planned else []

    declared, cited, count = spec.evidence()
    report.sources, report.citations = len(declared), count
    if spec.research:
        if not declared:
            report.evidence_gaps.append("no sources listed under '## Sources'")
        if not cited:
            report.evidence_gaps.append("no findings cite a source")
        for orphan in sorted(cited - declared):
            report.evidence_gaps.append(f"{orphan} is cited but not listed as a source")
        for unused in sorted(declared - cited):
            report.evidence_gaps.append(f"{unused} is listed but never cited")

    return report, requirements, claims


def criterion_order(criterion_id: str) -> tuple[int, int]:
    major, minor = criterion_id.lstrip("R").split(".")
    return int(major), int(minor)


def render(report: Report, requirements: dict[str, Requirement],
           claims: dict[str, set[str]]) -> str:
    owner: dict[str, set[str]] = {}
    for component, refs in claims.items():
        for ref in refs:
            owner.setdefault(ref, set()).add(component)

    lines = ["# Validation Report", "",
             "## Traceability", "",
             "| Requirement | Criterion | Satisfied by | Status |",
             "|---|---|---|---|"]
    for number in sorted(requirements, key=int):
        requirement = requirements[number]
        for cid in sorted(requirement.criteria, key=criterion_order):
            components = owner.get(cid)
            lines.append(f"| R{number} {requirement.title} | {cid} | "
                         f"{', '.join(sorted(components)) if components else '—'} | "
                         f"{'ok' if components else 'UNCOVERED'} |")

    lines += ["", "## Coverage", "",
              f"- Criteria: {report.total_criteria}",
              f"- Satisfied: {report.covered_criteria} ({report.coverage:.0f}%)",
              f"- Uncovered: {', '.join(report.uncovered) or 'none'}",
              f"- Dangling references: {', '.join(report.dangling) or 'none'}",
              "", "## Component roster", "",
              f"- In blueprint, absent from design: {', '.join(report.undesigned) or 'none'}",
              f"- In design, absent from blueprint: {', '.join(report.unplanned) or 'none'}",
              "", "## Evidence", "",
              f"- Sources listed: {report.sources}",
              f"- Citations in findings: {report.citations}"]
    if report.evidence_gaps:
        lines += [""] + [f"- {gap}" for gap in report.evidence_gaps]
    if report.missing_files:
        lines += ["", "## Missing documents", ""] + \
                 [f"- {name}" for name in report.missing_files]

    lines += ["", "## Verdict", ""]
    if report.ok:
        lines.append(f"**PASS** — {report.total_criteria} criteria all satisfied by a named "
                     "component, rosters agree, evidence cited. Ready for planning.")
    else:
        why = []
        if report.missing_files:
            why.append(f"{len(report.missing_files)} document(s) missing")
        if not report.total_criteria and "requirements.md" not in report.missing_files:
            why.append("no requirements found")
        if report.uncovered:
            why.append(f"{len(report.uncovered)} criteria uncovered")
        if report.dangling:
            why.append(f"{len(report.dangling)} dangling reference(s)")
        if report.undesigned or report.unplanned:
            why.append("component rosters disagree")
        if report.evidence_gaps:
            why.append(f"{len(report.evidence_gaps)} evidence gap(s)")
        lines.append(f"**FAIL** — {'; '.join(why)}.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a spec-architect document set")
    parser.add_argument("--path", default=".", help="directory holding the documents")
    parser.add_argument("--out", default="validation.md", help="report filename")
    args = parser.parse_args()

    root = Path(args.path)
    spec = SpecSet(root)
    report, requirements, claims = audit(spec)
    text = render(report, requirements, claims)
    (root / args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
