#!/usr/bin/env python3
"""Render a DoD written in the dod-architect Markdown dialect into a Google Doc.

Drives the `gws` CLI (googleworkspace/cli), which must be installed and authenticated.

    python render_dod_to_gdoc.py --doc-id DOC_ID --md dod.md            # apply
    python render_dod_to_gdoc.py --doc-id DOC_ID --md dod.md --dry-run  # validate only
    python render_dod_to_gdoc.py --doc-id DOC_ID --md dod.md --json-out requests.json

The target doc must already exist; its entire body is replaced. The update is atomic
(one invalid request aborts the whole batch) and is pinned to the revision read at
fetch time, so a concurrent edit between read and write fails rather than clobbering.

Dialect
-------
    #, ##, ###, ####    headings 1-4
    - text              bullet, rendered "• text" with a hanging indent
    **text**            bold run
    blank line          paragraph break

Two block kinds keep their internal line breaks instead of flowing into one line:

    scenario    opens with `GIVEN `; WHEN/THEN each start a fresh visual line
    citation    opens with a provenance label (see CITATION_LABELS), and gets extra
                space beneath so the criterion it belongs to separates cleanly

Inside those blocks a hard-wrapped line folds back into the line above it, so only
clause openers actually break. Every other block joins its lines with spaces.

Notes
-----
* Markdown links stay literal — they are not converted to Doc hyperlinks. Put
  shareable links in the tracker brief rather than the DoD body.
* insertText inherits list membership and character styling from the paragraph it
  lands in, so the inserted range is stripped of bullets and reset to plain before
  intended styles go on. Re-rendering a doc that carried direct formatting is clean.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass

# Vertical tab is what the Docs API treats as an in-paragraph line break (Shift+Enter).
SOFT_BREAK = "\v"

# Authoring notes in the template are HTML comments and never reach the doc.
COMMENT_SPAN = re.compile(r"<!--.*?-->", re.S)

# Provenance labels opening a citation block. The three carry different meanings
# (origin / pattern borrowed / workflow touched) but render identically — the
# distinction is editorial. Tuple so it can feed str.startswith directly.
CITATION_LABELS = ("Source:", "Derived from:", "Must not break:")

# Clause openers inside a scenario. Only GIVEN opens the block; WHEN/THEN appear
# here so they are not mistaken for wrapped continuations of the clause above.
CLAUSE_OPENERS = ("GIVEN ", "WHEN ", "THEN ")

BULLET_GLYPH = "• "
BULLET_INDENT_PT = 18
LINE_SPACING_PCT = 115

HEADING_STYLES = {1: "HEADING_1", 2: "HEADING_2", 3: "HEADING_3", 4: "HEADING_4"}
BODY_STYLE = "NORMAL_TEXT"

# (space above, space below) in points, per block kind.
SPACING = {
    "h1": (0, 10), "h2": (20, 8), "h3": (14, 6), "h4": (12, 6),
    "bullet": (0, 6), "scenario": (0, 3), "citation": (2, 14), "prose": (0, 10),
}

# Character styling cleared across the inserted range before restyling. Fields named
# but absent from the payload (link, colors) reset to their defaults.
CLEARED_FIELDS = "bold,italic,underline,strikethrough,foregroundColor,backgroundColor,link"


def utf16_len(text: str) -> int:
    """Length in UTF-16 code units — the unit the Docs API indexes by."""
    return len(text.encode("utf-16-le")) // 2


def split_bold(markdown: str) -> tuple[str, list[tuple[int, int]]]:
    """Strip ** markers, returning the clean text and the bold ranges within it."""
    segments = markdown.split("**")
    if len(segments) % 2 == 0:
        raise ValueError("unbalanced ** in: " + markdown[:80])
    text, spans, emphasized = "", [], False
    for segment in segments:
        if emphasized:
            start = utf16_len(text)
            text += segment
            stop = utf16_len(text)
            if stop > start:  # the API rejects zero-length ranges, so skip ****
                spans.append((start, stop))
        else:
            text += segment
        emphasized = not emphasized
    return text, spans


@dataclass
class Block:
    """One rendered paragraph. `level` is 1-4 for headings, 0 for body, -1 for a bullet."""

    level: int
    markdown: str

    @property
    def is_heading(self) -> bool:
        return self.level >= 1

    @property
    def is_bullet(self) -> bool:
        return self.level == -1

    def kind(self, text: str) -> str:
        """Spacing key for this block, given its bold-stripped text."""
        if self.is_heading:
            return "h%d" % self.level
        if self.is_bullet:
            return "bullet"
        if text.startswith("GIVEN "):
            return "scenario"
        if text.startswith(CITATION_LABELS):
            return "citation"
        return "prose"

    def render(self) -> tuple[str, list[tuple[int, int]], str, str]:
        """Return (text, bold spans, named style, spacing key)."""
        source = BULLET_GLYPH + self.markdown if self.is_bullet else self.markdown
        text, spans = split_bold(source)
        named = HEADING_STYLES[self.level] if self.is_heading else BODY_STYLE
        return text, spans, named, self.kind(text)


def _opens_visual_line(line: str) -> bool:
    """True when the line starts its own visual line inside a break-preserving block.

    Tested against bold-stripped text so `**GIVEN** ...` groups like `GIVEN ...`.
    """
    bare = line.replace("**", "")
    return bare.startswith(CLAUSE_OPENERS) or bare.startswith(CITATION_LABELS)


def _preserves_breaks(first_line: str) -> bool:
    """True for scenario and citation blocks, which keep their internal breaks.

    Only GIVEN opens a scenario — a paragraph merely starting WHEN/THEN is prose.
    """
    bare = first_line.replace("**", "")
    return bare.startswith("GIVEN ") or bare.startswith(CITATION_LABELS)


def _fold(lines: list[str]) -> str:
    """Join a break-preserving block, folding hard-wrapped lines into the line above."""
    visual: list[str] = [lines[0]]
    for line in lines[1:]:
        if _opens_visual_line(line):
            visual.append(line)
        else:
            visual[-1] += " " + line
    return SOFT_BREAK.join(visual)


class DialectParser:
    """Turns dialect Markdown into an ordered list of Blocks."""

    def __init__(self) -> None:
        self.blocks: list[Block] = []
        self._pending: list[str] = []

    def parse(self, markdown: str) -> list[Block]:
        for raw in COMMENT_SPAN.sub("", markdown).splitlines():
            line = raw.strip()
            if not line:
                self._flush()
            elif line.startswith("#"):
                self._emit_heading(line)
            elif line.startswith("- "):
                self._emit_bullet(line)
            else:
                self._pending.append(line)
        self._flush()
        return self.blocks

    def _flush(self) -> None:
        if not self._pending:
            return
        lines, self._pending = self._pending, []
        text = _fold(lines) if _preserves_breaks(lines[0]) else " ".join(lines)
        self.blocks.append(Block(0, text))

    def _emit_heading(self, line: str) -> None:
        self._flush()
        depth = len(line) - len(line.lstrip("#"))
        self.blocks.append(Block(min(max(depth, 1), 4), line.lstrip("#").strip()))

    def _emit_bullet(self, line: str) -> None:
        self._flush()
        self.blocks.append(Block(-1, line[2:].strip()))


def parse_dialect(markdown: str) -> list[Block]:
    return DialectParser().parse(markdown)


def _points(value: int) -> dict:
    return {"magnitude": value, "unit": "PT"}


class BatchBuilder:
    """Accumulates the batchUpdate requests that replace a document body."""

    def __init__(self, blocks: list[Block]) -> None:
        self.rendered = [block.render() for block in blocks]
        self.body = "\n".join(text for text, _, _, _ in self.rendered)

    def paragraph_styles(self) -> list[dict]:
        reqs, cursor = [], 1
        for text, _, named, kind in self.rendered:
            above, below = SPACING[kind]
            length = utf16_len(text)
            reqs.append({"updateParagraphStyle": {
                "range": {"startIndex": cursor, "endIndex": cursor + length + 1},
                "paragraphStyle": {
                    "namedStyleType": named,
                    "lineSpacing": LINE_SPACING_PCT,
                    "spaceAbove": _points(above),
                    "spaceBelow": _points(below),
                    "indentStart": _points(BULLET_INDENT_PT if kind == "bullet" else 0),
                    "indentFirstLine": _points(0),
                },
                "fields": ("namedStyleType,lineSpacing,spaceAbove,spaceBelow,"
                           "indentStart,indentFirstLine"),
            }})
            cursor += length + 1
        return reqs

    def text_styles(self) -> list[dict]:
        reqs, cursor = [], 1
        for text, spans, named, _ in self.rendered:
            length = utf16_len(text)
            if named != BODY_STYLE:  # the range reset cleared the heading's own bold
                reqs.append(_bold(cursor, cursor + length))
            reqs.extend(_bold(cursor + a, cursor + b) for a, b in spans)
            cursor += length + 1
        return reqs


def _bold(start: int, stop: int) -> dict:
    return {"updateTextStyle": {"range": {"startIndex": start, "endIndex": stop},
                                "textStyle": {"bold": True}, "fields": "bold"}}


def _clear_styles(start: int, stop: int) -> dict:
    return {"updateTextStyle": {
        "range": {"startIndex": start, "endIndex": stop},
        "textStyle": {"bold": False, "italic": False,
                      "underline": False, "strikethrough": False},
        "fields": CLEARED_FIELDS}}


def build_requests(blocks: list[Block], current_end: int) -> list[dict]:
    """Full batch: clear the old body, insert the new one, then style it."""
    builder = BatchBuilder(blocks)
    inserted_end = 1 + utf16_len(builder.body)

    reqs: list[dict] = []
    if current_end - 1 > 1:
        reqs.append({"deleteContentRange":
                     {"range": {"startIndex": 1, "endIndex": current_end - 1}}})
    reqs.append({"insertText": {"location": {"index": 1}, "text": builder.body}})
    if inserted_end > 1:
        reqs.append({"deleteParagraphBullets":
                     {"range": {"startIndex": 1, "endIndex": inserted_end}}})
        reqs.append(_clear_styles(1, inserted_end))

    return reqs + builder.paragraph_styles() + builder.text_styles()


class GwsClient:
    """Thin wrapper over the `gws` CLI's Docs subcommands."""

    def __init__(self, binary: str = "gws") -> None:
        self.binary = binary

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([self.binary, "docs", "documents", *args],
                              capture_output=True, text=True)

    @staticmethod
    def _payload(result: subprocess.CompletedProcess) -> str:
        return "\n".join(line for line in result.stdout.splitlines()
                         if not line.startswith("Using keyring"))

    def read_extent(self, doc_id: str) -> tuple[int, str | None]:
        """Return (end index of the body, revision id) for the target document."""
        result = self._run("get", "--params", json.dumps({"documentId": doc_id}))
        out = self._payload(result)
        if not out.strip():
            sys.exit("gws get returned no output:\n" + result.stderr)
        try:
            document = json.loads(out)
        except json.JSONDecodeError:
            sys.exit("gws get did not return JSON (valid doc id? authenticated?):\n"
                     + out[:500])
        if "error" in document:  # valid JSON, no body — e.g. 401 reauth or 404
            sys.exit("gws get returned an error: " + json.dumps(document["error"])[:400])
        try:
            return document["body"]["content"][-1]["endIndex"], document.get("revisionId")
        except (KeyError, IndexError):
            sys.exit("gws get response has no body content:\n" + out[:300])

    def apply(self, doc_id: str, body: dict, dry_run: bool = False) -> None:
        args = ["batchUpdate", "--params", json.dumps({"documentId": doc_id}),
                "--json", json.dumps(body, ensure_ascii=False)]
        if dry_run:
            args.insert(0, "--dry-run")
        result = self._run(*args)
        out = self._payload(result)
        if result.returncode != 0:
            sys.exit(f"gws batchUpdate failed:\n{result.stderr}\n{out}")
        try:
            parsed = json.loads(out)
        except json.JSONDecodeError:
            print(out[:500])
            return
        if "error" in parsed:
            sys.exit("ERROR: " + json.dumps(parsed["error"]))
        print("dry-run OK" if dry_run
              else f"applied OK — {len(parsed.get('replies', []))} replies")


def compose_body(blocks: list[Block], doc_id: str, client: GwsClient) -> dict:
    end, revision = client.read_extent(doc_id)
    body: dict = {"requests": build_requests(blocks, end)}
    if revision:
        body["writeControl"] = {"requiredRevisionId": revision}
    else:
        print("warning: gws returned no revisionId — applying without "
              "concurrent-edit protection", file=sys.stderr)
    return body


def summarize(blocks: list[Block]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for block in blocks:
        kind = block.render()[3]
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def read_source(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError as err:
        sys.exit(f"cannot read --md file {path!r}: {err}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--doc-id", required=True)
    parser.add_argument("--md", required=True, help="path to the DoD markdown source")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate locally, do not send")
    parser.add_argument("--json-out", help="also write the batchUpdate requests here")
    parser.add_argument("--gws", default="gws", help="path to the gws binary")
    args = parser.parse_args()

    blocks = parse_dialect(read_source(args.md))
    client = GwsClient(args.gws)
    body = compose_body(blocks, args.doc_id, client)

    print(f"blocks={len(blocks)} requests={len(body['requests'])} "
          f"kinds={summarize(blocks)}", file=sys.stderr)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(body, handle, ensure_ascii=False)
    client.apply(args.doc_id, body, args.dry_run)


if __name__ == "__main__":
    main()
