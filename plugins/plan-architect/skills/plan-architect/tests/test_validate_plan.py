"""Behavioral and CLI tests for the standalone plan validator/renderer."""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "validate_plan.py"
spec = importlib.util.spec_from_file_location("validate_plan", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
EXAMPLE = json.loads((SKILL / "reference" / "ExamplePlan.json").read_text(encoding="utf-8"))


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.plan = copy.deepcopy(EXAMPLE)

    def assert_error(self, fragment):
        errors = validator.audit(self.plan)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_example_has_complete_coverage_and_allows_pending_logistics(self):
        self.assertEqual(validator.audit(self.plan), [])
        report = validator.report_markdown(self.plan, [])
        self.assertIn("**PASS**", report)
        self.assertIn("P1: pending", report)
        self.assertIn("T2, T3, T5", report)

    def test_spec_handoff_requires_declared_validation_source(self):
        self.plan["readiness"]["kind"] = "spec-architect"
        self.assert_error("required for spec-architect")
        self.plan["readiness"]["validation_source"] = "missing"
        self.assert_error("unknown sources reference missing")
        self.plan["readiness"]["validation_source"] = "S3"
        self.assertEqual(validator.audit(self.plan), [])

    def test_pending_blocked_and_ready_with_blockers_cannot_pass(self):
        for status in ("pending", "blocked"):
            with self.subTest(status=status):
                self.plan["readiness"]["status"] = status
                self.assert_error("status must be ready")
        self.plan["readiness"]["status"] = "ready"
        self.plan["readiness"]["blockers"] = ["Authentication behavior undecided"]
        self.assert_error("no unresolved design blockers")

    def test_duplicate_ids_in_each_namespace(self):
        for collection in ("sources", "criteria", "components", "milestones", "tasks", "external_prerequisites"):
            with self.subTest(collection=collection):
                self.plan = copy.deepcopy(EXAMPLE)
                self.plan[collection].append(copy.deepcopy(self.plan[collection][0]))
                self.assert_error("duplicate ID")

    def test_missing_fields_unknown_fields_and_types_fail_closed(self):
        for mutation in (lambda p: p.pop("criteria"),
                         lambda p: p.update(taskz=[]),
                         lambda p: p["tasks"][0].update(verification=[]),
                         lambda p: p["tasks"][0].update(criteria=[{}]),
                         lambda p: p["milestones"][0].update(depends_on="M2"),
                         lambda p: p["readiness"].update(evidence=" "),
                         lambda p: p["tasks"][0].update(owner=12),
                         lambda p: p["components"][0].update(source_refs=[None])):
            self.plan = copy.deepcopy(EXAMPLE)
            mutation(self.plan)
            self.assertTrue(validator.audit(self.plan))
        for root in (None, [], False, 42, "plan"):
            self.assertTrue(validator.audit(root))
            self.assertIn("**FAIL**", validator.report_markdown(root, validator.audit(root)))

    def test_empty_inventories_and_empty_milestones_fail(self):
        for collection in ("sources", "criteria", "components", "milestones", "tasks"):
            with self.subTest(collection=collection):
                self.plan = copy.deepcopy(EXAMPLE)
                self.plan[collection] = []
                self.assert_error("inventory must not be empty")
        self.plan = copy.deepcopy(EXAMPLE)
        self.plan["tasks"] = self.plan["tasks"][:-1]
        self.assert_error("M3 has no tasks")

    def test_source_mappings_must_be_declared_and_nonempty(self):
        self.plan["criteria"][0]["source_refs"][0]["source"] = "S9"
        self.assert_error("unknown sources reference S9")
        self.plan["criteria"][0]["source_refs"] = []
        self.assert_error("at least one source mapping")

    def test_uncovered_criterion_and_component_fail(self):
        for task in self.plan["tasks"]:
            task["criteria"] = [ref for ref in task["criteria"] if ref != "R1.2"]
            task["components"] = [ref for ref in task["components"] if ref != "RedisStore"]
        self.assert_error("uncovered R1.2")
        self.assert_error("uncovered RedisStore")

    def test_task_references_are_checked_by_namespace(self):
        for field, value in (("milestone", "M9"), ("criteria", ["R9.1"]),
                             ("components", ["Imaginary"]), ("prerequisites", ["P9"])):
            with self.subTest(field=field):
                self.plan = copy.deepcopy(EXAMPLE)
                self.plan["tasks"][0][field] = value
                self.assert_error("unknown")

    def test_unknown_and_self_dependencies_fail_on_both_graphs(self):
        for collection in ("tasks", "milestones"):
            for dependency in ("missing", EXAMPLE[collection][0]["id"]):
                with self.subTest(collection=collection, dependency=dependency):
                    self.plan = copy.deepcopy(EXAMPLE)
                    self.plan[collection][0]["depends_on"] = [dependency]
                    self.assert_error("unknown" if dependency == "missing" else "self-dependency")

    def test_task_and_milestone_cycles_fail(self):
        self.plan["tasks"][0]["depends_on"] = ["T5"]
        self.assert_error("tasks: dependency cycle")
        self.plan = copy.deepcopy(EXAMPLE)
        self.plan["milestones"][0]["depends_on"] = ["M3"]
        self.assert_error("milestones: dependency cycle")

    def test_cross_milestone_edge_needs_ancestry_not_declaration_order(self):
        self.plan["milestones"][1]["depends_on"] = []
        self.assert_error("contradicts milestone order")

    def test_transitive_milestone_dependencies_are_valid(self):
        self.plan["tasks"][-1]["depends_on"].append("T2")
        self.assertEqual(validator.audit(self.plan), [])

    def test_intra_milestone_parallelism_and_empty_enabling_refs(self):
        self.plan["tasks"][0]["components"] = []
        self.assertEqual(validator.audit(self.plan), [])
        self.assertEqual(self.plan["tasks"][2]["depends_on"], self.plan["tasks"][3]["depends_on"])

    def test_duplicate_refs_and_whitespace_ids_fail(self):
        self.plan["tasks"][1]["depends_on"] = ["T1", "T1"]
        self.assert_error("invalid type or value")
        self.plan["tasks"][0]["id"] = "T 1"
        self.assert_error("invalid type or value")

    def test_schedule_is_optional_and_supplied_values_are_preserved(self):
        self.plan["tasks"][0].update(owner="Alex", estimate="2 days", date="2026-10-15")
        self.assertEqual(validator.audit(self.plan), [])
        rendered = validator.plan_markdown(self.plan, [])
        self.assertIn("Owner: Alex; estimate: 2 days; date: 2026-10-15", rendered)
        self.assertIn("Owner: unassigned; estimate: unknown; date: unknown", rendered)

    def test_render_uses_topological_order_and_is_deterministic(self):
        self.plan["milestones"].reverse()
        self.plan["tasks"].reverse()
        self.assertEqual(validator.audit(self.plan), [])
        rendered = validator.plan_markdown(self.plan, [])
        self.assertLess(rendered.index("## M1"), rendered.index("## M2"))
        self.assertLess(rendered.index("### T1"), rendered.index("### T2"))
        self.assertEqual(rendered, validator.plan_markdown(self.plan, []))

    def test_plain_text_cannot_inject_markdown_structure(self):
        self.plan["title"] = "Project\n\n## Forged heading"
        self.plan["criteria"][0]["id"] = "R1|fake"
        rendered = validator.plan_markdown(self.plan, validator.audit(self.plan))
        self.assertNotIn("\n## Forged heading", rendered)
        report = validator.report_markdown(self.plan, validator.audit(self.plan))
        self.assertIn("R1\\|fake", report)

    def test_plain_text_paragraphs_preserve_markers_entities_and_strikethrough(self):
        cases = {
            "---": "\\---", "- literal bullet": "\\- literal bullet",
            "+ literal bullet": "\\+ literal bullet", "===": "\\===",
            "1. literal numbering": "1\\. literal numbering",
            "2) literal numbering": "2\\) literal numbering",
            "&copy; is a literal entity": "\\&copy; is a literal entity",
            "~~keep this wording~~": "\\~\\~keep this wording\\~\\~",
        }
        for text, escaped in cases.items():
            with self.subTest(text=text):
                self.plan["summary"] = text
                self.plan["tasks"][0]["work"] = text
                self.assertEqual(validator.audit(self.plan), [])
                rendered = validator.plan_markdown(self.plan, [])
                self.assertIn("\n\n" + escaped + "\n\n", rendered)
                self.assertNotIn("\n\n" + text + "\n\n", rendered)


class CLITests(unittest.TestCase):
    def run_cli(self, root, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--path", str(root), *args],
                              cwd=root.parent, capture_output=True, text=True)

    def test_example_cli_preserves_inputs_and_writes_only_requested_outputs(self):
        with tempfile.TemporaryDirectory(prefix="plan test ") as temp:
            root = Path(temp) / "output with spaces"
            root.mkdir()
            source = root / "design.md"
            source.write_text("Agreed upstream design\n", encoding="utf-8")
            input_path = root / "plan.json"
            raw = json.dumps(EXAMPLE, indent=2) + "\n"
            input_path.write_text(raw, encoding="utf-8")
            result = self.run_cli(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(input_path.read_text(), raw)
            self.assertEqual(source.read_text(), "Agreed upstream design\n")
            self.assertEqual({p.name for p in root.iterdir()},
                             {"plan.json", "design.md", "plan.md", "plan-validation.md"})
            outputs = [(root / name).read_bytes() for name in ("plan.md", "plan-validation.md")]
            self.assertEqual(self.run_cli(root).returncode, 0)
            self.assertEqual(outputs, [(root / name).read_bytes() for name in ("plan.md", "plan-validation.md")])
            self.assertIn("P1: pending", (root / "plan-validation.md").read_text())

    def test_invalid_json_content_generates_failure_not_traceback(self):
        for raw in ('{"title":', '{"title":"one","title":"two"}', '{"x":NaN}', "null", '[]'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "plan.json").write_text(raw, encoding="utf-8")
                result = self.run_cli(root)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("**FAIL**", (root / "plan-validation.md").read_text())
                self.assertIn("invalid input", (root / "plan.md").read_text())
                self.assertNotIn("Traceback", result.stderr)

    def test_structural_failure_overwrites_stale_pass_with_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "plan.json").write_text(json.dumps(EXAMPLE), encoding="utf-8")
            self.assertEqual(self.run_cli(root).returncode, 0)
            plan = copy.deepcopy(EXAMPLE)
            plan["tasks"][0]["depends_on"] = ["T5"]
            (root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
            result = self.run_cli(root)
            self.assertEqual(result.returncode, 1)
            report = (root / "plan-validation.md").read_text()
            self.assertNotIn("**PASS**", report)
            self.assertIn("dependency cycle", report)
            self.assertIn("draft only", (root / "plan.md").read_text())

    def test_template_intentionally_fails_until_completed(self):
        plan = json.loads((SKILL / "reference" / "PlanTemplate.json").read_text())
        self.assertTrue(validator.audit(plan))

    def test_missing_input_bad_utf8_and_invocation_errors_exit_two(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(self.run_cli(root).returncode, 2)
            (root / "plan.json").write_bytes(b"\xff")
            self.assertEqual(self.run_cli(root).returncode, 2)
            self.assertEqual(self.run_cli(root, "--unknown").returncode, 2)
            self.assertFalse((root / "plan-validation.md").exists())

    def test_output_file_access_error_does_not_claim_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "plan.json").write_text(json.dumps(EXAMPLE), encoding="utf-8")
            (root / "plan.md").mkdir()
            result = self.run_cli(root)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("**PASS**", result.stdout)

    def test_output_aliases_cannot_overwrite_upstream_source(self):
        for link_type in ("symlink", "hardlink"):
            with self.subTest(link_type=link_type), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "plan.json").write_text(json.dumps(EXAMPLE), encoding="utf-8")
                source = root / "design.md"
                source.write_text("upstream", encoding="utf-8")
                output = root / "plan-validation.md"
                if link_type == "symlink":
                    output.symlink_to(source)
                else:
                    import os
                    os.link(source, output)
                result = self.run_cli(root)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(source.read_text(), "upstream")
                self.assertFalse((root / "plan.md").exists())


if __name__ == "__main__":
    unittest.main()
