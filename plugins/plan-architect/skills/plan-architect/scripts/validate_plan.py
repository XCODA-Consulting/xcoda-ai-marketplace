#!/usr/bin/env python3
"""Check a plan-architect document set for coverage, sequencing and skeleton gaps.

    python3 validate_plan.py --path <dir> [--out plan-validation.md]

Reads inventory.md, spine.md and plan.md from <dir>, writes a validation report, and
exits non-zero when the plan is unsound. Five checks:

    coverage         every criterion is delivered by exactly one milestone
    references       every id points at a criterion, and every dependency points backwards
    naming           the inventory roster and the touched components agree
    skeleton         M1 walks the whole spine, and the spine is genuinely end to end
    demonstrability  every milestone says what you will see and what risk it retires

Formats it reads (see the Workflows/ docs for the authoring templates):

    inventory.md    | `ComponentName` | responsibility | exists |
                    ## R1 — Title, then numbered criteria -> R1.1, R1.2, ...
    spine.md        | `ComponentName` | role on the path |   (row order is path order)
    plan.md         ## M1 — Title, then **Delivers**: / **Touches**: /
                    **Depends on**: / **Demo**: / **Risk retired**:

The skeleton check is the opinionated one. Requiring M1 to touch every component on the
spine is what makes a horizontally sliced plan — "build the store first, wire it up last" —
fail mechanically rather than in review.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

COMPONENT_CELL = re.compile(r"\|\s*`([A-Za-z0-9_.]+)`\s*\|")
REQUIREMENT_HEAD = re.compile(r"^##\s+R(\d+)\s*[—–-]\s*(.+)$", re.M)
MILESTONE_HEAD = re.compile(r"^##\s+M(\d+)\s*[—–-]\s*(.+)$", re.M)
CRITERION_LINE = re.compile(r"^\s*(\d+)\.\s+(\S.*)$", re.M)
CRITERION_REF = re.compile(r"R(\d+)\.(\d+)")
MILESTONE_REF = re.compile(r"M(\d+)")
ANY_HEAD = re.compile(r"^##\s+\S.*$", re.M)
SECTION_HEAD = re.compile(r"^##\s+(.+?)\s*$", re.M)
BACKTICKED = re.compile(r"`([A-Za-z0-9_.]+)`")

# Horizontal whitespace only: `\s*` would cross the newline and let an empty label
# silently absorb the line beneath it.
DELIVERS_LINE = re.compile(r"^\*\*Delivers\*\*:[ \t]*(.*)$", re.M)
TOUCHES_LINE = re.compile(r"^\*\*Touches\*\*:[ \t]*(.*)$", re.M)
DEPENDS_LINE = re.compile(r"^\*\*Depends on\*\*:[ \t]*(.*)$", re.M)
DEMO_LINE = re.compile(r"^\*\*Demo\*\*:[ \t]*(.*)$", re.M)
RISK_LINE = re.compile(r"^\*\*Risk retired\*\*:[ \t]*(.*)$", re.M)

NONE_WORDS = {"none", "—", "-", "n/a"}


def criterion_order(cid: str) -> tuple[int, int]:
    """Sort key putting R2.10 after R2.9 rather than after R2.1."""
    major, minor = cid.lstrip("R").split(".")
    return int(major), int(minor)


def section(text: str, title: str) -> str:
    """The body under a `## Title` heading, stopping at the next heading of any kind."""
    for head in SECTION_HEAD.finditer(text):
        if head.group(1).strip().casefold() != title.casefold():
            continue
        nxt = ANY_HEAD.search(text, head.end())
        return text[head.end():nxt.start() if nxt else len(text)]
    return ""


def body_after(text: str, head: re.Match[str]) -> str:
    """Everything under a heading, up to the next `## ` heading."""
    nxt = ANY_HEAD.search(text, head.end())
    return text[head.end():nxt.start() if nxt else len(text)]


def is_none(value: str) -> bool:
    return value.strip().casefold() in NONE_WORDS


@dataclass
class Milestone:
    number: int
    title: str
    delivers: list[str] = field(default_factory=list)
    touches: list[str] = field(default_factory=list)
    depends: list[int] = field(default_factory=list)
    demo: str = ""
    risk: str = ""

    @property
    def mid(self) -> str:
        return f"M{self.number}"


@dataclass
class Report:
    uncovered: list[str] = field(default_factory=list)
    double_claimed: list[str] = field(default_factory=list)
    dangling: list[str] = field(default_factory=list)
    out_of_order: list[str] = field(default_factory=list)
    unknown_components: list[str] = field(default_factory=list)
    unbuilt_components: list[str] = field(default_factory=list)
    skeleton_gaps: list[str] = field(default_factory=list)
    incomplete: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    total_criteria: int = 0
    delivered_criteria: int = 0

    @property
    def coverage(self) -> float:
        if not self.total_criteria:
            return 0.0
        return self.delivered_criteria / self.total_criteria * 100

    @property
    def ok(self) -> bool:
        return not any([self.uncovered, self.double_claimed, self.dangling,
                        self.out_of_order, self.unknown_components,
                        self.unbuilt_components, self.skeleton_gaps,
                        self.incomplete, self.missing_files]) \
            and self.total_criteria > 0


class PlanSet:
    """The three authored documents, loaded from a directory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.missing: list[str] = []
        self.inventory = self._load("inventory.md")
        self.spine = self._load("spine.md")
        self.plan = self._load("plan.md")

    def _load(self, name: str) -> str:
        path = self.root / name
        if not path.exists():
            self.missing.append(name)
            return ""
        return path.read_text(encoding="utf-8")

    def roster(self) -> set[str]:
        """Components declared in the inventory's Components table."""
        return set(COMPONENT_CELL.findall(section(self.inventory, "Components")))

    def spine_path(self) -> list[str]:
        """Spine components in path order — row order is the order of the walk."""
        seen: list[str] = []
        for name in COMPONENT_CELL.findall(section(self.spine, "Spine")):
            if name not in seen:
                seen.append(name)
        return seen

    def criteria(self) -> dict[str, str]:
        """Every criterion in the inventory, keyed R<major>.<minor>."""
        found: dict[str, str] = {}
        for head in REQUIREMENT_HEAD.finditer(self.inventory):
            number = head.group(1)
            for index, text in CRITERION_LINE.findall(body_after(self.inventory, head)):
                found[f"R{number}.{index}"] = text.strip()
        return found

    def requirement_titles(self) -> dict[str, str]:
        return {m.group(1): m.group(2).strip() for m in REQUIREMENT_HEAD.finditer(self.inventory)}

    def milestones(self) -> list[Milestone]:
        found: list[Milestone] = []
        for head in MILESTONE_HEAD.finditer(self.plan):
            body = body_after(self.plan, head)
            stone = Milestone(number=int(head.group(1)), title=head.group(2).strip())

            delivers = DELIVERS_LINE.search(body)
            if delivers and not is_none(delivers.group(1)):
                stone.delivers = [f"R{a}.{b}" for a, b in CRITERION_REF.findall(delivers.group(1))]

            touches = TOUCHES_LINE.search(body)
            if touches:
                stone.touches = BACKTICKED.findall(touches.group(1))

            depends = DEPENDS_LINE.search(body)
            if depends and not is_none(depends.group(1)):
                stone.depends = [int(n) for n in MILESTONE_REF.findall(depends.group(1))]

            demo = DEMO_LINE.search(body)
            stone.demo = demo.group(1).strip() if demo else ""
            risk = RISK_LINE.search(body)
            stone.risk = risk.group(1).strip() if risk else ""

            found.append(stone)
        return sorted(found, key=lambda s: s.number)


def audit(plan: PlanSet) -> tuple[Report, dict[str, str], list[Milestone], dict[str, list[str]]]:
    report = Report(missing_files=list(plan.missing))
    criteria = plan.criteria()
    milestones = plan.milestones()
    roster = plan.roster()
    spine = plan.spine_path()

    report.total_criteria = len(criteria)

    # coverage + references — who delivers each criterion
    owner: dict[str, list[str]] = {}
    for stone in milestones:
        for cid in stone.delivers:
            owner.setdefault(cid, []).append(stone.mid)
            if cid not in criteria:
                report.dangling.append(f"{stone.mid} delivers {cid}, which is not in the inventory")

    report.uncovered = sorted((c for c in criteria if c not in owner), key=criterion_order)
    report.double_claimed = sorted(
        (f"{cid} ({', '.join(mids)})" for cid, mids in owner.items()
         if len(mids) > 1 and cid in criteria),
        key=lambda s: criterion_order(s.split(" ")[0]))
    report.delivered_criteria = sum(1 for c in criteria if len(owner.get(c, [])) == 1)

    # references — dependencies point strictly backwards, which also rules out cycles
    numbers = {s.number for s in milestones}
    for stone in milestones:
        for dep in stone.depends:
            if dep not in numbers:
                report.out_of_order.append(f"{stone.mid} depends on M{dep}, which does not exist")
            elif dep >= stone.number:
                report.out_of_order.append(
                    f"{stone.mid} depends on M{dep}, which is not an earlier milestone")

    # naming — the roster and the touched components agree, in both directions
    touched: set[str] = set()
    for stone in milestones:
        for name in stone.touches:
            touched.add(name)
            if roster and name not in roster:
                report.unknown_components.append(
                    f"{stone.mid} touches {name}, absent from the inventory roster")
    report.unbuilt_components = sorted(roster - touched)

    # skeleton — M1 walks the whole spine
    if not spine:
        report.skeleton_gaps.append("no spine declared under '## Spine' in spine.md")
    elif len(spine) < 2:
        report.skeleton_gaps.append(
            f"the spine has only {len(spine)} component; an end-to-end path needs at least two")
    if milestones and spine:
        first = milestones[0]
        if first.number != 1:
            report.skeleton_gaps.append(f"the first milestone is {first.mid}, not M1")
        for name in spine:
            if name not in first.touches:
                report.skeleton_gaps.append(
                    f"{first.mid} does not touch {name}, which is on the spine")
    if not milestones:
        report.skeleton_gaps.append("no milestones found in plan.md")

    # demonstrability
    for stone in milestones:
        if not stone.demo:
            report.incomplete.append(f"{stone.mid} has no Demo line")
        if not stone.risk:
            report.incomplete.append(f"{stone.mid} has no Risk retired line")

    return report, criteria, milestones, owner


def render(report: Report, plan: PlanSet, criteria: dict[str, str],
           milestones: list[Milestone], owner: dict[str, list[str]]) -> str:
    spine = plan.spine_path()
    titles = plan.requirement_titles()

    lines = ["# Plan Validation Report", "",
             "## Delivery order", "",
             "| Milestone | Delivers | Touches | Depends on |",
             "|---|---|---|---|"]
    for stone in milestones:
        lines.append(
            f"| {stone.mid} {stone.title} | {', '.join(stone.delivers) or '—'} | "
            f"{', '.join(stone.touches) or '—'} | "
            f"{', '.join(f'M{d}' for d in stone.depends) or '—'} |")

    lines += ["", "## Traceability", "",
              "| Criterion | Requirement | Delivered by | Status |",
              "|---|---|---|---|"]
    for cid in sorted(criteria, key=criterion_order):
        mids = owner.get(cid, [])
        status = "ok" if len(mids) == 1 else ("UNCOVERED" if not mids else "CLAIMED TWICE")
        lines.append(f"| {cid} | R{cid.lstrip('R').split('.')[0]} "
                     f"{titles.get(cid.lstrip('R').split('.')[0], '')} | "
                     f"{', '.join(mids) or '—'} | {status} |")

    lines += ["", "## Coverage", "",
              f"- Criteria: {report.total_criteria}",
              f"- Delivered exactly once: {report.delivered_criteria} ({report.coverage:.0f}%)",
              f"- Uncovered: {', '.join(report.uncovered) or 'none'}",
              f"- Claimed by more than one milestone: {', '.join(report.double_claimed) or 'none'}",
              f"- Dangling references: {', '.join(report.dangling) or 'none'}",
              "", "## Skeleton", "",
              f"- Spine: {' -> '.join(spine) or 'none declared'}",
              f"- M1 touches: {', '.join(milestones[0].touches) if milestones else 'no milestones'}",
              f"- Walks the spine end to end: {'yes' if not report.skeleton_gaps else 'NO'}"]
    if report.skeleton_gaps:
        lines += [""] + [f"- {gap}" for gap in report.skeleton_gaps]

    lines += ["", "## Component roster", "",
              f"- In inventory, built by no milestone: {', '.join(report.unbuilt_components) or 'none'}",
              f"- Touched but absent from inventory: {', '.join(report.unknown_components) or 'none'}",
              "", "## Sequencing", "",
              f"- Out-of-order dependencies: {', '.join(report.out_of_order) or 'none'}"]

    if report.incomplete:
        lines += ["", "## Demonstrability", ""] + [f"- {gap}" for gap in report.incomplete]
    if report.missing_files:
        lines += ["", "## Missing documents", ""] + [f"- {name}" for name in report.missing_files]

    lines += ["", "## Verdict", ""]
    if report.ok:
        lines.append(f"**PASS** — {report.total_criteria} criteria each delivered by exactly one "
                     f"of {len(milestones)} milestones, M1 walks the spine end to end, every "
                     "milestone demonstrable. Ready to build.")
    else:
        why = []
        if report.missing_files:
            why.append(f"{len(report.missing_files)} document(s) missing")
        if not report.total_criteria and "inventory.md" not in report.missing_files:
            why.append("no criteria found")
        if report.uncovered:
            why.append(f"{len(report.uncovered)} criteria uncovered")
        if report.double_claimed:
            why.append(f"{len(report.double_claimed)} criteria claimed by more than one milestone")
        if report.dangling:
            why.append(f"{len(report.dangling)} dangling reference(s)")
        if report.out_of_order:
            why.append(f"{len(report.out_of_order)} out-of-order dependency(ies)")
        if report.unknown_components or report.unbuilt_components:
            why.append("component rosters disagree")
        if report.skeleton_gaps:
            why.append("M1 does not walk the spine")
        if report.incomplete:
            why.append(f"{len(report.incomplete)} demonstrability gap(s)")
        lines.append(f"**FAIL** — {'; '.join(why)}.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a plan-architect document set")
    parser.add_argument("--path", default=".", help="directory holding the documents")
    parser.add_argument("--out", default="plan-validation.md", help="report filename")
    args = parser.parse_args()

    root = Path(args.path)
    plan = PlanSet(root)
    report, criteria, milestones, owner = audit(plan)
    text = render(report, plan, criteria, milestones, owner)
    (root / args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
