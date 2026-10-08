#!/usr/bin/env python3
"""Regression test: tracked artifact names with spaces and non-ASCII bytes
must survive gallery discovery intact.

`git ls-files` used to be parsed by splitting stdout on whitespace, so a
committed `out/mix-彩 图 one.png` fell apart into three unrelated tokens, the
membership check missed it, and the gallery preferred an uncommitted render —
exactly what a fresh clone must never show. The fixture below commits one
such PNG and leaves a same-stem SVG untracked: the PNG has to win and be the
path the generated page links.

Stdlib only; runs against a throwaway Git fixture, no build, no browser.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gallery  # noqa: E402: test lives beside the module it covers

GIT = ["git", "-c", "user.email=gallery@example.com", "-c", "user.name=gallery test"]

TRACKED_ARTIFACT = "out/mix-彩 图 one.png"
UNTRACKED_ARTIFACT = "out/mix-彩 图 one.svg"


class TrackedSpacedUnicodeNames(unittest.TestCase):
    def setUp(self):
        self._saved = (gallery.ROOT, gallery.OUTPUT, gallery.CONFIG, gallery.TRACKED)
        self.tmp = tempfile.TemporaryDirectory()
        repo = Path(self.tmp.name)
        (repo / "src").mkdir()
        (repo / "out").mkdir()
        (repo / "gallery.json").write_text(
            '{"title": "fixture", "tagline": "spaced names", "sources": "src/*.ts"}',
            encoding="utf-8",
        )
        (repo / "src" / "mix.ts").write_text(
            "export function mix(): number { return 1; }\n", encoding="utf-8")
        for rel in (TRACKED_ARTIFACT, UNTRACKED_ARTIFACT):
            (repo / rel).write_bytes(b"fixture render")
        subprocess.run(GIT + ["init", "-q", "-b", "main", str(repo)], check=True)
        subprocess.run(
            GIT + ["-C", str(repo), "add", "--", "gallery.json", "src/mix.ts", TRACKED_ARTIFACT],
            check=True,
        )
        subprocess.run(
            GIT + ["-C", str(repo), "commit", "-q", "--no-verify", "-m", "fixture"],
            check=True,
        )
        self.repo = repo
        gallery.ROOT = repo
        gallery.OUTPUT = repo / "gallery.html"
        gallery.CONFIG = repo / "gallery.json"

    def tearDown(self):
        gallery.ROOT, gallery.OUTPUT, gallery.CONFIG, gallery.TRACKED = self._saved
        self.tmp.cleanup()

    def test_discovery_returns_exact_paths(self):
        # whitespace splitting would yield "out/mix-彩", "图", "one.png" here
        self.assertEqual(
            gallery.tracked_files(),
            {"gallery.json", "src/mix.ts", TRACKED_ARTIFACT},
        )

    def test_gallery_links_the_committed_render(self):
        self.assertEqual(gallery.build(), 0, "the one demo must count as rendered")
        page = (self.repo / "gallery.html").read_text(encoding="utf-8")
        self.assertIn(f'src="{TRACKED_ARTIFACT}"', page)
        self.assertNotIn(UNTRACKED_ARTIFACT, page)
        # the link resolves: the exact referenced path exists in the checkout
        self.assertTrue((self.repo / TRACKED_ARTIFACT).is_file())


if __name__ == "__main__":
    unittest.main()
