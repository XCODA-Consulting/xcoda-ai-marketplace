"""Tests for the DoD Markdown dialect renderer.

The script is a standalone CLI rather than an installed package, so it is loaded
directly from its path.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_dod_to_gdoc.py"
_spec = importlib.util.spec_from_file_location("render_dod_to_gdoc", _SCRIPT)
assert _spec and _spec.loader
renderer = importlib.util.module_from_spec(_spec)
# @dataclass resolves its module via sys.modules, so register before executing.
sys.modules[_spec.name] = renderer
_spec.loader.exec_module(renderer)

BREAK = renderer.SOFT_BREAK


def texts(blocks):
    """The rendered text of each block, ignoring styling."""
    return [block.render()[0] for block in blocks]


def kinds(blocks):
    """The spacing kind of each block."""
    return [block.render()[3] for block in blocks]


class Utf16LengthTests(unittest.TestCase):
    def test_basic_multilingual_plane_counts_one_unit_per_char(self):
        self.assertEqual(renderer.utf16_len("abc"), 3)
        self.assertEqual(renderer.utf16_len("§ 1.0"), 5)

    def test_astral_chars_count_two_units(self):
        self.assertEqual(renderer.utf16_len("😀"), 2)

    def test_empty_string(self):
        self.assertEqual(renderer.utf16_len(""), 0)


class SplitBoldTests(unittest.TestCase):
    def test_marks_are_removed_and_span_recorded(self):
        text, spans = renderer.split_bold("a **b** c")
        self.assertEqual(text, "a b c")
        self.assertEqual(spans, [(2, 3)])

    def test_multiple_spans(self):
        text, spans = renderer.split_bold("**x** and **y**")
        self.assertEqual(text, "x and y")
        self.assertEqual(spans, [(0, 1), (6, 7)])

    def test_empty_span_is_dropped(self):
        # the Docs API rejects a zero-length range, so **** must not emit one
        text, spans = renderer.split_bold("a****b")
        self.assertEqual(text, "ab")
        self.assertEqual(spans, [])

    def test_span_offsets_are_utf16_not_codepoints(self):
        text, spans = renderer.split_bold("😀**b**")
        self.assertEqual(text, "😀b")
        self.assertEqual(spans, [(2, 3)])  # the emoji occupies two units

    def test_unbalanced_markers_raise(self):
        with self.assertRaises(ValueError):
            renderer.split_bold("a **b")


class HeadingAndBulletTests(unittest.TestCase):
    def test_hash_depth_sets_level(self):
        blocks = renderer.parse_dialect("# One\n\n## Two\n\n### Three\n\n#### Four")
        self.assertEqual([b.level for b in blocks], [1, 2, 3, 4])
        self.assertEqual(texts(blocks), ["One", "Two", "Three", "Four"])

    def test_depth_beyond_four_clamps(self):
        blocks = renderer.parse_dialect("##### Five")
        self.assertEqual(blocks[0].level, 4)

    def test_heading_uses_named_style_and_kind(self):
        block = renderer.parse_dialect("## Section")[0]
        _, _, named, kind = block.render()
        self.assertEqual(named, "HEADING_2")
        self.assertEqual(kind, "h2")

    def test_bullet_gains_glyph_and_kind(self):
        blocks = renderer.parse_dialect("- first\n- second")
        self.assertEqual(texts(blocks), ["• first", "• second"])
        self.assertEqual(kinds(blocks), ["bullet", "bullet"])

    def test_heading_interrupts_an_open_paragraph(self):
        blocks = renderer.parse_dialect("prose line\n# Heading")
        self.assertEqual(texts(blocks), ["prose line", "Heading"])


class ProseBlockTests(unittest.TestCase):
    def test_wrapped_prose_joins_with_spaces(self):
        blocks = renderer.parse_dialect("one\ntwo\nthree")
        self.assertEqual(texts(blocks), ["one two three"])

    def test_blank_line_separates_paragraphs(self):
        blocks = renderer.parse_dialect("first para\n\nsecond para")
        self.assertEqual(texts(blocks), ["first para", "second para"])

    def test_authoring_comments_are_stripped(self):
        blocks = renderer.parse_dialect("<!-- note to author -->\nFeature: x")
        self.assertEqual(texts(blocks), ["Feature: x"])

    def test_multiline_comment_is_stripped(self):
        blocks = renderer.parse_dialect("<!--\nstill a note\n-->\nkept")
        self.assertEqual(texts(blocks), ["kept"])


class ScenarioBlockTests(unittest.TestCase):
    def test_clauses_each_open_a_visual_line(self):
        md = "GIVEN a failed delivery\nWHEN it is retried\nTHEN the event ID matches."
        self.assertEqual(texts(renderer.parse_dialect(md)), [
            f"GIVEN a failed delivery{BREAK}WHEN it is retried{BREAK}"
            "THEN the event ID matches."])

    def test_wrapped_clause_folds_into_the_clause_above(self):
        md = ("GIVEN a delivery that failed\nand was retried\n"
              "WHEN the receiver inspects it\nTHEN the event ID matches.")
        self.assertEqual(texts(renderer.parse_dialect(md)), [
            f"GIVEN a delivery that failed and was retried{BREAK}"
            f"WHEN the receiver inspects it{BREAK}THEN the event ID matches."])

    def test_only_given_opens_a_scenario(self):
        # a paragraph merely starting WHEN is prose and flows into one line
        blocks = renderer.parse_dialect("WHEN the receiver acks late it\nstill counts.")
        self.assertEqual(texts(blocks), ["WHEN the receiver acks late it still counts."])
        self.assertEqual(kinds(blocks), ["prose"])

    def test_bold_clause_opener_still_groups(self):
        md = "**GIVEN** a failed delivery\n**WHEN** it is retried"
        self.assertIn(BREAK, texts(renderer.parse_dialect(md))[0])

    def test_scenario_kind(self):
        self.assertEqual(kinds(renderer.parse_dialect("GIVEN a thing")), ["scenario"])


class CitationBlockTests(unittest.TestCase):
    def test_single_citation_has_no_internal_break(self):
        blocks = renderer.parse_dialect("**Source:** brainstorm doc §2 (backoff).")
        self.assertNotIn(BREAK, texts(blocks)[0])
        self.assertEqual(kinds(blocks), ["citation"])

    def test_consecutive_citations_keep_their_breaks(self):
        # a criterion citing both an origin and a constraint must not run together
        md = ("**Source:** escalation thread #4821.\n"
              "**Must not break:** delivery telemetry (attempt count).")
        self.assertEqual(texts(renderer.parse_dialect(md)), [
            f"Source: escalation thread #4821.{BREAK}"
            "Must not break: delivery telemetry (attempt count)."])

    def test_hard_wrapped_citation_stays_one_visual_line(self):
        # regression: gating on the first line alone broke every wrapped citation
        md = ('**Source:** escalation thread #4821 ("a way for us to tell\n'
              'it is the same event").')
        rendered = texts(renderer.parse_dialect(md))[0]
        self.assertNotIn(BREAK, rendered)
        self.assertIn("tell it is the same event", rendered)

    def test_bold_continuation_is_not_promoted_to_its_own_line(self):
        md = "**Source:** the escalation thread covering\n**strong** emphasis mid-citation."
        self.assertNotIn(BREAK, texts(renderer.parse_dialect(md))[0])

    def test_wrapped_line_after_the_last_label_stays_attached(self):
        md = ("**Source:** escalation thread #4821.\n"
              "**Must not break:** delivery telemetry (attempt\ncount and timestamp).")
        parts = texts(renderer.parse_dialect(md))[0].split(BREAK)
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[1].endswith("(attempt count and timestamp)."))

    def test_all_three_labels_share_the_citation_kind(self):
        for label in renderer.CITATION_LABELS:
            with self.subTest(label=label):
                blocks = renderer.parse_dialect(f"{label} ticket #4821")
                self.assertEqual(kinds(blocks), ["citation"])

    def test_lookalike_prefix_is_not_a_citation(self):
        self.assertEqual(kinds(renderer.parse_dialect("Sourced elsewhere")), ["prose"])


class RequestBuildingTests(unittest.TestCase):
    def setUp(self):
        self.blocks = renderer.parse_dialect("# Title\n\nbody text\n\n- a bullet")

    def test_existing_body_is_cleared_before_insert(self):
        reqs = renderer.build_requests(self.blocks, current_end=50)
        self.assertIn("deleteContentRange", reqs[0])
        self.assertIn("insertText", reqs[1])

    def test_empty_document_skips_the_delete(self):
        reqs = renderer.build_requests(self.blocks, current_end=2)
        self.assertIn("insertText", reqs[0])
        self.assertNotIn("deleteContentRange", json_keys(reqs))

    def test_inherited_bullets_and_styles_are_reset(self):
        reqs = renderer.build_requests(self.blocks, current_end=2)
        keys = json_keys(reqs)
        self.assertIn("deleteParagraphBullets", keys)
        # the reset must precede the styling passes that follow it
        reset_at = next(i for i, r in enumerate(reqs) if "deleteParagraphBullets" in r)
        style_at = next(i for i, r in enumerate(reqs) if "updateParagraphStyle" in r)
        self.assertLess(reset_at, style_at)

    def test_every_block_gets_a_paragraph_style(self):
        reqs = renderer.build_requests(self.blocks, current_end=2)
        styles = [r for r in reqs if "updateParagraphStyle" in r]
        self.assertEqual(len(styles), len(self.blocks))

    def test_heading_is_re_bolded_after_the_reset(self):
        reqs = renderer.build_requests(renderer.parse_dialect("# Title"), current_end=2)
        bolds = [r for r in reqs
                 if "updateTextStyle" in r and r["updateTextStyle"]["textStyle"].get("bold")]
        self.assertEqual(len(bolds), 1)

    def test_bullet_is_indented_and_prose_is_not(self):
        reqs = renderer.build_requests(self.blocks, current_end=2)
        indents = [r["updateParagraphStyle"]["paragraphStyle"]["indentStart"]["magnitude"]
                   for r in reqs if "updateParagraphStyle" in r]
        self.assertIn(renderer.BULLET_INDENT_PT, indents)
        self.assertIn(0, indents)

    def test_inserted_text_is_the_blocks_joined_by_newlines(self):
        reqs = renderer.build_requests(self.blocks, current_end=2)
        inserted = next(r["insertText"]["text"] for r in reqs if "insertText" in r)
        self.assertEqual(inserted, "Title\nbody text\n• a bullet")


def json_keys(requests):
    return {key for request in requests for key in request}


if __name__ == "__main__":
    unittest.main()
