"""Tests for the execution-plan validator.

The script is a standalone CLI rather than an installed package, so it is loaded
directly from its path.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_plan.py"
_spec = importlib.util.spec_from_file_location("validate_plan", _SCRIPT)
assert _spec and _spec.loader
validator = importlib.util.module_from_spec(_spec)
# @dataclass resolves its module via sys.modules, so register before executing.
sys.modules[_spec.name] = validator
_spec.loader.exec_module(validator)

INVENTORY = """# Delivery Inventory

## Components

| Component | Responsibility | Exists |
|---|---|---|
| `RateLimiter` | Enforces per-key request rates | no |
| `RedisStore` | Persists counters with TTL | no |

## Criteria

## R1 — Rate limiting

1. WHEN a request arrives, the **`RateLimiter`** SHALL compare the count to the limit.
2. WHEN the limit is exceeded, the **`RateLimiter`** SHALL reject with 429.

## R2 — Outage handling

1. WHEN Redis is unreachable, the **`RedisStore`** SHALL fail open.

## Risks

- [K1] Fail-open is specified but unexercised.
"""

SPINE = """# Walking Skeleton

## The thinnest path

One request, one key, one counter.

## Spine

| Component | Role on the path |
|---|---|
| `RateLimiter` | entry — receives the request |
| `RedisStore` | exit — the counter it reads |

## First demo

Send one request and watch the counter appear.
"""

PLAN = """# Execution Plan

## Approach

Skeleton first, then thicken.

## M1 — End-to-end limit decision for one key

**Delivers**: R1.1
**Touches**: `RateLimiter`, `RedisStore`
**Depends on**: none
**Demo**: Send one request; observe a counter in Redis and an allowed response.
**Risk retired**: Proves the round trip before any window logic exists.

## M2 — Rejection at the limit

**Delivers**: R1.2
**Touches**: `RateLimiter`
**Depends on**: M1
**Demo**: Send requests past the limit; observe a 429.
**Risk retired**: Confirms the comparison on a path known to reach Redis.

## M3 — Fail open when Redis is unreachable

**Delivers**: R2.1
**Touches**: `RedisStore`
**Depends on**: M1
**Demo**: Stop Redis, send a request; observe it allowed.
**Risk retired**: Retires the outage behaviour nothing exercised.
"""


class DocumentSetTestCase(unittest.TestCase):
    """Writes a three-document set into a temp directory and audits it."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def audit(self, inventory: str | None = INVENTORY, spine: str | None = SPINE,
              plan: str | None = PLAN):
        """Write the given documents and return (report, plan_set)."""
        for name, text in (("inventory.md", inventory), ("spine.md", spine), ("plan.md", plan)):
            if text is not None:
                (self.root / name).write_text(text, encoding="utf-8")
        plan_set = validator.PlanSet(self.root)
        report, _, _, _ = validator.audit(plan_set)
        return report, plan_set

    def report_text(self, **kwargs) -> str:
        for name, text in (("inventory.md", kwargs.get("inventory", INVENTORY)),
                           ("spine.md", kwargs.get("spine", SPINE)),
                           ("plan.md", kwargs.get("plan", PLAN))):
            if text is not None:
                (self.root / name).write_text(text, encoding="utf-8")
        plan_set = validator.PlanSet(self.root)
        report, criteria, milestones, owner = validator.audit(plan_set)
        return validator.render(report, plan_set, criteria, milestones, owner)


class HelperTests(unittest.TestCase):
    def test_criterion_order_sorts_numerically_not_lexically(self):
        ids = ["R2.10", "R2.9", "R1.1"]
        self.assertEqual(sorted(ids, key=validator.criterion_order),
                         ["R1.1", "R2.9", "R2.10"])

    def test_section_returns_body_up_to_next_heading(self):
        text = "## One\n\nalpha\n\n## Two\n\nbeta\n"
        self.assertIn("alpha", validator.section(text, "One"))
        self.assertNotIn("beta", validator.section(text, "One"))

    def test_section_is_case_insensitive(self):
        self.assertIn("alpha", validator.section("## Spine\n\nalpha\n", "spine"))

    def test_section_returns_empty_string_when_absent(self):
        self.assertEqual(validator.section("## One\n\nalpha\n", "Missing"), "")

    def test_none_words_are_recognised(self):
        for word in ("none", "None", "—", "-", "N/A", "  none  "):
            self.assertTrue(validator.is_none(word), word)

    def test_real_content_is_not_a_none_word(self):
        self.assertFalse(validator.is_none("M1"))


class InventoryParsingTests(DocumentSetTestCase):
    def test_roster_comes_from_the_components_table(self):
        _, plan_set = self.audit()
        self.assertEqual(plan_set.roster(), {"RateLimiter", "RedisStore"})

    def test_criteria_are_keyed_by_requirement_and_line_number(self):
        _, plan_set = self.audit()
        self.assertEqual(sorted(plan_set.criteria()), ["R1.1", "R1.2", "R2.1"])

    def test_criterion_body_stops_at_the_next_heading(self):
        _, plan_set = self.audit()
        # The Risks section follows R2 and must not contribute criteria.
        self.assertNotIn("R2.2", plan_set.criteria())

    def test_requirement_titles_are_captured(self):
        _, plan_set = self.audit()
        self.assertEqual(plan_set.requirement_titles()["1"], "Rate limiting")

    def test_en_dash_and_hyphen_headings_parse(self):
        inventory = INVENTORY.replace("## R1 — Rate limiting", "## R1 - Rate limiting")
        _, plan_set = self.audit(inventory=inventory)
        self.assertIn("R1.1", plan_set.criteria())


class SpineParsingTests(DocumentSetTestCase):
    def test_spine_is_read_in_row_order(self):
        _, plan_set = self.audit()
        self.assertEqual(plan_set.spine_path(), ["RateLimiter", "RedisStore"])

    def test_spine_ignores_components_outside_the_spine_table(self):
        spine = SPINE.replace("Send one request and watch the counter appear.",
                              "| `Unrelated` | not on the path |")
        _, plan_set = self.audit(spine=spine)
        self.assertEqual(plan_set.spine_path(), ["RateLimiter", "RedisStore"])

    def test_repeated_component_appears_once(self):
        spine = SPINE.replace("| `RedisStore` | exit — the counter it reads |",
                              "| `RedisStore` | exit |\n| `RateLimiter` | returns |")
        _, plan_set = self.audit(spine=spine)
        self.assertEqual(plan_set.spine_path(), ["RateLimiter", "RedisStore"])


class MilestoneParsingTests(DocumentSetTestCase):
    def test_all_milestones_are_found_in_order(self):
        _, plan_set = self.audit()
        self.assertEqual([m.number for m in plan_set.milestones()], [1, 2, 3])

    def test_delivers_touches_and_depends_are_parsed(self):
        _, plan_set = self.audit()
        first, second = plan_set.milestones()[0], plan_set.milestones()[1]
        self.assertEqual(first.delivers, ["R1.1"])
        self.assertEqual(first.touches, ["RateLimiter", "RedisStore"])
        self.assertEqual(first.depends, [])
        self.assertEqual(second.depends, [1])

    def test_demo_and_risk_are_captured(self):
        _, plan_set = self.audit()
        first = plan_set.milestones()[0]
        self.assertTrue(first.demo.startswith("Send one request"))
        self.assertTrue(first.risk.startswith("Proves the round trip"))

    def test_milestones_are_sorted_even_when_written_out_of_order(self):
        blocks = PLAN.split("## M")
        reordered = blocks[0] + "## M" + blocks[3] + "## M" + blocks[1] + "## M" + blocks[2]
        _, plan_set = self.audit(plan=reordered)
        self.assertEqual([m.number for m in plan_set.milestones()], [1, 2, 3])


class CoverageCheckTests(DocumentSetTestCase):
    def test_complete_plan_covers_every_criterion(self):
        report, _ = self.audit()
        self.assertEqual(report.uncovered, [])
        self.assertEqual(report.total_criteria, 3)
        self.assertEqual(report.delivered_criteria, 3)
        self.assertTrue(report.ok)

    def test_undelivered_criterion_is_reported(self):
        plan = PLAN.replace("**Delivers**: R2.1", "**Delivers**: none")
        report, _ = self.audit(plan=plan)
        self.assertEqual(report.uncovered, ["R2.1"])
        self.assertFalse(report.ok)

    def test_criterion_claimed_by_two_milestones_fails(self):
        plan = PLAN.replace("**Delivers**: R1.2", "**Delivers**: R1.1")
        report, _ = self.audit(plan=plan)
        self.assertTrue(any(entry.startswith("R1.1") for entry in report.double_claimed))
        self.assertFalse(report.ok)

    def test_double_claim_names_both_milestones(self):
        plan = PLAN.replace("**Delivers**: R1.2", "**Delivers**: R1.1")
        report, _ = self.audit(plan=plan)
        self.assertIn("M1, M2", report.double_claimed[0])

    def test_coverage_percentage_reflects_singly_delivered_criteria(self):
        plan = PLAN.replace("**Delivers**: R2.1", "**Delivers**: none")
        report, _ = self.audit(plan=plan)
        self.assertAlmostEqual(report.coverage, 200 / 3)

    def test_empty_criteria_cannot_pass(self):
        inventory = INVENTORY.split("## Criteria")[0]
        report, _ = self.audit(inventory=inventory)
        self.assertEqual(report.total_criteria, 0)
        self.assertFalse(report.ok)


class ReferenceCheckTests(DocumentSetTestCase):
    def test_delivering_an_unknown_criterion_is_dangling(self):
        plan = PLAN.replace("**Delivers**: R2.1", "**Delivers**: R9.9")
        report, _ = self.audit(plan=plan)
        self.assertTrue(any("R9.9" in entry for entry in report.dangling))
        self.assertFalse(report.ok)

    def test_dependency_on_a_later_milestone_fails(self):
        plan = PLAN.replace("## M2 — Rejection at the limit\n\n**Delivers**: R1.2\n"
                            "**Touches**: `RateLimiter`\n**Depends on**: M1",
                            "## M2 — Rejection at the limit\n\n**Delivers**: R1.2\n"
                            "**Touches**: `RateLimiter`\n**Depends on**: M3")
        report, _ = self.audit(plan=plan)
        self.assertTrue(any("not an earlier milestone" in entry for entry in report.out_of_order))
        self.assertFalse(report.ok)

    def test_self_dependency_fails(self):
        plan = PLAN.replace("**Depends on**: M1\n**Demo**: Send requests past the limit",
                            "**Depends on**: M2\n**Demo**: Send requests past the limit")
        report, _ = self.audit(plan=plan)
        self.assertTrue(report.out_of_order)
        self.assertFalse(report.ok)

    def test_dependency_on_a_nonexistent_milestone_fails(self):
        plan = PLAN.replace("**Depends on**: M1\n**Demo**: Stop Redis",
                            "**Depends on**: M7\n**Demo**: Stop Redis")
        report, _ = self.audit(plan=plan)
        self.assertTrue(any("does not exist" in entry for entry in report.out_of_order))


class NamingCheckTests(DocumentSetTestCase):
    def test_touching_an_unknown_component_fails(self):
        plan = PLAN.replace("**Touches**: `RateLimiter`\n**Depends on**: M1",
                            "**Touches**: `RateLimitter`\n**Depends on**: M1")
        report, _ = self.audit(plan=plan)
        self.assertTrue(any("RateLimitter" in entry for entry in report.unknown_components))
        self.assertFalse(report.ok)

    def test_component_built_by_no_milestone_fails(self):
        inventory = INVENTORY.replace(
            "| `RedisStore` | Persists counters with TTL | no |",
            "| `RedisStore` | Persists counters with TTL | no |\n"
            "| `MetricsSink` | Records decisions | no |")
        report, _ = self.audit(inventory=inventory)
        self.assertEqual(report.unbuilt_components, ["MetricsSink"])
        self.assertFalse(report.ok)

    def test_matching_rosters_pass(self):
        report, _ = self.audit()
        self.assertEqual(report.unknown_components, [])
        self.assertEqual(report.unbuilt_components, [])


class SkeletonCheckTests(DocumentSetTestCase):
    def test_m1_covering_the_spine_passes(self):
        report, _ = self.audit()
        self.assertEqual(report.skeleton_gaps, [])

    def test_horizontally_sliced_plan_fails(self):
        """The anti-pattern: M1 builds one layer, M2 builds the next."""
        plan = PLAN.replace("**Touches**: `RateLimiter`, `RedisStore`",
                            "**Touches**: `RedisStore`")
        report, _ = self.audit(plan=plan)
        self.assertTrue(any("RateLimiter" in gap and "on the spine" in gap
                            for gap in report.skeleton_gaps))
        self.assertFalse(report.ok)

    def test_single_component_spine_fails(self):
        spine = SPINE.replace("| `RedisStore` | exit — the counter it reads |\n", "")
        report, _ = self.audit(spine=spine)
        self.assertTrue(any("at least two" in gap for gap in report.skeleton_gaps))
        self.assertFalse(report.ok)

    def test_missing_spine_table_fails(self):
        spine = SPINE.replace("## Spine", "## Not the spine")
        report, _ = self.audit(spine=spine)
        self.assertTrue(any("no spine declared" in gap for gap in report.skeleton_gaps))

    def test_plan_with_no_milestones_fails(self):
        report, _ = self.audit(plan="# Execution Plan\n\n## Approach\n\nNothing yet.\n")
        self.assertTrue(any("no milestones" in gap for gap in report.skeleton_gaps))
        self.assertFalse(report.ok)

    def test_numbering_that_does_not_start_at_one_fails(self):
        plan = PLAN.replace("## M1 — End-to-end", "## M0 — End-to-end")
        report, _ = self.audit(plan=plan)
        self.assertTrue(any("not M1" in gap for gap in report.skeleton_gaps))


class DemonstrabilityCheckTests(DocumentSetTestCase):
    def test_missing_demo_line_fails(self):
        plan = PLAN.replace("**Demo**: Stop Redis, send a request; observe it allowed.\n", "")
        report, _ = self.audit(plan=plan)
        self.assertIn("M3 has no Demo line", report.incomplete)
        self.assertFalse(report.ok)

    def test_empty_demo_line_fails(self):
        plan = PLAN.replace("**Demo**: Stop Redis, send a request; observe it allowed.",
                            "**Demo**:")
        report, _ = self.audit(plan=plan)
        self.assertIn("M3 has no Demo line", report.incomplete)

    def test_missing_risk_line_fails(self):
        plan = PLAN.replace("**Risk retired**: Retires the outage behaviour nothing exercised.\n",
                            "")
        report, _ = self.audit(plan=plan)
        self.assertIn("M3 has no Risk retired line", report.incomplete)

    def test_complete_milestones_pass(self):
        report, _ = self.audit()
        self.assertEqual(report.incomplete, [])


class MissingDocumentTests(DocumentSetTestCase):
    def test_absent_plan_is_reported_not_raised(self):
        report, _ = self.audit(plan=None)
        self.assertIn("plan.md", report.missing_files)
        self.assertFalse(report.ok)

    def test_absent_spine_is_reported(self):
        report, _ = self.audit(spine=None)
        self.assertIn("spine.md", report.missing_files)

    def test_empty_directory_fails_without_crashing(self):
        report, _ = self.audit(inventory=None, spine=None, plan=None)
        self.assertEqual(sorted(report.missing_files),
                         ["inventory.md", "plan.md", "spine.md"])
        self.assertFalse(report.ok)


class WorkedExampleTests(DocumentSetTestCase):
    """The documents published in reference/ExampleRun.md must actually pass.

    The README and the reference both claim this; without a test the claim rots the
    first time a convention changes.
    """

    DOCUMENT_BLOCK = re.compile(
        r"^##\s+([A-Za-z0-9_.-]+\.md)(?:\s+—[^\n]*)?\s*\n+```markdown\n(.*?)\n```",
        re.M | re.S)

    def setUp(self) -> None:
        super().setUp()
        source = Path(__file__).resolve().parents[1] / "reference" / "ExampleRun.md"
        self.example = source.read_text(encoding="utf-8")
        self.documents = {name: body for name, body in self.DOCUMENT_BLOCK.findall(self.example)
                          if not name.startswith("plan-validation")}

    def test_example_publishes_all_three_input_documents(self):
        self.assertEqual(sorted(self.documents), ["inventory.md", "plan.md", "spine.md"])

    def test_published_documents_pass_validation(self):
        report, _ = self.audit(inventory=self.documents["inventory.md"],
                               spine=self.documents["spine.md"],
                               plan=self.documents["plan.md"])
        self.assertTrue(report.ok, f"worked example does not validate: {report}")

    def test_published_report_matches_what_the_validator_produces(self):
        text = self.report_text(inventory=self.documents["inventory.md"],
                                spine=self.documents["spine.md"],
                                plan=self.documents["plan.md"])
        claimed = self.DOCUMENT_BLOCK.search(
            self.example[self.example.index("## plan-validation.md"):]).group(2)
        # The published copy is hard-wrapped for readability; compare on unwrapped lines.
        for line in claimed.replace("end\nto end", "end to end").splitlines():
            if line.strip():
                self.assertIn(line, text)


class ReportRenderingTests(DocumentSetTestCase):
    def test_passing_set_renders_a_pass_verdict(self):
        text = self.report_text()
        self.assertIn("**PASS**", text)
        self.assertNotIn("**FAIL**", text)

    def test_report_lists_the_spine_as_a_path(self):
        self.assertIn("RateLimiter -> RedisStore", self.report_text())

    def test_traceability_table_names_the_delivering_milestone(self):
        self.assertIn("| R1.1 | R1 Rate limiting | M1 | ok |", self.report_text())

    def test_uncovered_criterion_is_marked_in_the_table(self):
        plan = PLAN.replace("**Delivers**: R2.1", "**Delivers**: none")
        self.assertIn("UNCOVERED", self.report_text(plan=plan))

    def test_double_claim_is_marked_in_the_table(self):
        plan = PLAN.replace("**Delivers**: R1.2", "**Delivers**: R1.1")
        self.assertIn("CLAIMED TWICE", self.report_text(plan=plan))

    def test_failure_verdict_names_the_reason(self):
        plan = PLAN.replace("**Touches**: `RateLimiter`, `RedisStore`",
                            "**Touches**: `RedisStore`")
        text = self.report_text(plan=plan)
        self.assertIn("**FAIL**", text)
        self.assertIn("M1 does not walk the spine", text)

    def test_missing_documents_get_their_own_section(self):
        self.assertIn("## Missing documents", self.report_text(plan=None))


if __name__ == "__main__":
    unittest.main()
