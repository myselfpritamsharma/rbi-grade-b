import json
import html
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from unittest.mock import patch

from phase2_chapter_roadmap import ESI as CHAPTER_ESI, FINANCE, MANAGEMENT, parse
from phase2_evidence_inventory import ESI, FM, ESSAYS, TASKS, catalog, parse_refs
from phase2_topic_tasks import chapter_key, load_tasks, make_prompt


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "PYP_Analysis"


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.classes = []
        self.prompts = {}
        self._prompt_id = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs["href"])
        self.classes.extend(attrs.get("class", "").split())
        if tag == "textarea" and "prompt-text" in attrs.get("class", "").split():
            self._prompt_id = attrs["id"]
            self.prompts[self._prompt_id] = ""

    def handle_data(self, data):
        if self._prompt_id is not None:
            self.prompts[self._prompt_id] += data

    def handle_endtag(self, tag):
        if tag == "textarea":
            self._prompt_id = None


class Phase2EvidenceTests(unittest.TestCase):
    def test_reference_ranges_keep_question_kind(self):
        self.assertEqual(parse_refs("2021:O1-2,O4,D3;2022:D1", "ESI"), {
            ("ESI", 2021, "O", 1), ("ESI", 2021, "O", 2),
            ("ESI", 2021, "O", 4), ("ESI", 2021, "D", 3), ("ESI", 2022, "D", 1),
        })

    def test_invalid_reference_is_not_silently_ignored(self):
        for value in ("2021:1", "2021:O4-2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_refs(value, "ESI")

    def test_all_360_questions_have_named_inventory_coverage(self):
        entries = catalog(ESI, "ESI") + catalog(FM, "FM")
        covered = set().union(*(row["keys"] for row in entries))
        expected = {(subject, year, kind, q) for subject in ("ESI", "FM")
                    for year in range(2021, 2026) for kind, n in (("O", 30), ("D", 6))
                    for q in range(1, n + 1)}
        self.assertEqual(covered, expected)
        for row in entries:
            for field in ("asked", "study", "task"):
                self.assertTrue(row[field].strip(), (row["name"], field))

    def test_every_supplied_chapter_has_explicit_static_and_current_targets(self):
        for subject, raw in (("ESI", CHAPTER_ESI), ("Finance", FINANCE), ("Management", MANAGEMENT)):
            rows = parse(raw)
            supplied = {p.name for p in (ROOT / "SubjectNotesForPhase2" / subject).iterdir() if p.is_dir()}
            self.assertEqual({row["folder"] for row in rows}, supplied)
            self.assertEqual(len(rows), len(supplied))
            for row in rows:
                self.assertGreaterEqual(len(row["static"]), 3, row["folder"])
                self.assertGreaterEqual(len(row["current"]), 2, row["folder"])

    def test_all_english_options_and_tasks_are_present(self):
        self.assertEqual({(r[0], r[1]) for r in ESSAYS},
                         {(y, q) for y in range(2021, 2026) for q in range(1, 5)})
        self.assertEqual({(r[0], r[1]) for r in TASKS},
                         {(y, t) for y in range(2021, 2026) for t in ("Precis", "RC")})

    def test_published_report_has_original_analysis_and_new_sections(self):
        parser = ReportParser()
        parser.feed((OUTPUT / "phase2_deep_analysis.html").read_text(encoding="utf-8"))
        self.assertEqual(len(parser.ids), len(set(parser.ids)), "Duplicate navigation IDs")
        for target in ("ESI", "FM", "English", "weightage", "chapter-roadmap",
                       "what-ESI", "what-FM", "what-English", "inventory-method"):
            self.assertIn(target, parser.ids)
        self.assertEqual(parser.classes.count("chapter-card"), 93)
        self.assertEqual(parser.classes.count("essay-card"), 20)
        self.assertEqual(parser.classes.count("language-task"), 10)
        for link in parser.links:
            self.assertNotIn("phase2_notes_graph.html", link)
            if link.startswith("#"):
                self.assertIn(link[1:], parser.ids, link)

    def test_all_report_file_and_topic_links_resolve(self):
        parser = ReportParser()
        parser.feed((OUTPUT / "phase2_deep_analysis.html").read_text(encoding="utf-8"))
        data = json.loads((ROOT / "study_library" / "library.json").read_text(encoding="utf-8"))
        topic_ids = {t["id"] for t in data["topics"]}
        for link in parser.links:
            url = urlsplit(link)
            if not url.path:
                continue
            if url.scheme == "file":
                path = Path(unquote(url.path).lstrip("/"))
            elif not url.scheme:
                path = OUTPUT / unquote(url.path)
            else:
                continue
            self.assertTrue(path.exists(), link)
            if url.fragment.startswith("topic="):
                self.assertIn(url.fragment.removeprefix("topic="), topic_ids, link)

    def test_machine_readable_exports_match_html(self):
        coverage = json.loads((OUTPUT / "phase2_inventory_coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(coverage["covered_questions"], 360)
        self.assertEqual(coverage["missing_questions"], [])
        chapters = json.loads((OUTPUT / "phase2_chapter_study_roadmap.json").read_text(encoding="utf-8"))
        self.assertEqual(len(chapters), 93)
        for row in chapters:
            for path in row.get("source_notes", []):
                self.assertTrue((ROOT / path).is_file(), path)

    def test_accessible_reader_controls_are_published_offline(self):
        source = (OUTPUT / "phase2_deep_analysis.html").read_text(encoding="utf-8")
        parser = ReportParser()
        parser.feed(source)
        for control in ("main-content", "chapter-search", "subject-filter", "chapter-results",
                        "open-navigation", "close-navigation", "smaller-text", "larger-text",
                        "focus-reading", "print-report", "search-status"):
            self.assertIn(control, parser.ids)
        self.assertIn('href="#main-content">Skip to study content', source)
        self.assertIn('for="chapter-search"', source)
        self.assertIn('aria-live="polite"', source)
        self.assertIn("function renderSearch()", source)
        self.assertIn("@media print", source)
        self.assertNotIn("<script src=", source)

    def test_every_chapter_has_specific_independent_tasks(self):
        tasks = load_tasks()
        expected = {(subject, chapter_key(subject, row["folder"]))
                    for subject, raw in (("ESI", CHAPTER_ESI), ("Finance", FINANCE),
                                         ("Management", MANAGEMENT))
                    for row in parse(raw)}
        expected.update(("English", str(i)) for i in range(1, 6))
        self.assertEqual(set(tasks), expected)
        self.assertEqual(len(expected), 93)
        self.assertNotEqual(chapter_key("Management", "Communication-11"),
                            chapter_key("Management", "Emotional Intelligence-11"))
        for key, group in tasks.items():
            with self.subTest(chapter=key):
                self.assertGreaterEqual(sum(t["kind"] == "S" for t in group), 3)
                self.assertGreaterEqual(sum(t["kind"] != "S" for t in group), 2)
                self.assertEqual(len({t["demand"] for t in group}), len(group))
                for task in group:
                    self.assertTrue(task["title"].strip())
                    self.assertTrue(task["demand"].strip())
                    prompt = make_prompt(key[0], f"Chapter {key[1]}", task)
                    for required in (f"Subject: {key[0]}", f"Chapter: Chapter {key[1]}",
                                     task["title"], task["demand"], "fully revealed answers"):
                        self.assertIn(required, prompt)
                    for required in ("Check whether any current affairs", "explained notes",
                                     "even for a static or applied-practice topic",
                                     "if you cannot check", "mind map, infographic",
                                     "actual visual or table content", "image rendering is unavailable",
                                     "do not invent statistics", "as-of date", "unverified", "source URL",
                                     "never invent", "Do not assume a 2027 rule",
                                     "CurrentAffairs-Monthly", "Reports_NationalAndInternational",
                                     "SchemesAndGovernmentPortals", "StaticGK"):
                        self.assertIn(required, prompt)

    def test_topic_task_parser_rejects_bad_records(self):
        for value in ("ESI|1|S|Missing demand", "ESI|1|X|Title|Demand",
                      "ESI|1|S||Demand", "ESI|1|S|Title|Demand\nESI|1|S|Title|Other"):
            with self.subTest(value=value), patch("phase2_topic_tasks.TASK_DATA", value):
                with self.assertRaises(ValueError):
                    load_tasks()

    def test_topper_findings_are_embedded_with_evidence_limits(self):
        source = (OUTPUT / "phase2_deep_analysis.html").read_text(encoding="utf-8")
        text = html.unescape(source)
        parser = ReportParser()
        parser.feed(source)
        data = json.loads((OUTPUT / "rbi_topper_tips_traps_evidence.json").read_text(encoding="utf-8"))
        for target in ("topper-insights", "topper-coverage", "topper-conflicting-advice",
                       "topper-study-workflow", "topper-evidence-bias", "topper-source-register"):
            self.assertIn(target, parser.ids)
        self.assertIn('href="#topper-insights"', source)
        self.assertIn("Preparation / topper tips & traps", text)
        self.assertEqual(parser.classes.count("topper-card"), len(data["findings"]))
        for item in data["findings"]:
            self.assertIn(f"topper-{item['id']}", parser.ids)
            for field in ("title", "action", "trap"):
                self.assertIn(item[field], text)
            for key, seconds, statement in item["evidence"]:
                self.assertIn(statement, text)
                url = data["sources"][key]["url"]
                if seconds is not None:
                    url += f"&t={seconds}s"
                self.assertIn(url, parser.links)
        for row in data["conflicts"] + data["suggested_workflow"]:
            for value in row:
                self.assertIn(value, text)
        for item in data["sources"].values():
            self.assertIn(item["name"], text)
            self.assertIn(item["url"], parser.links)
        for caveat in ("partial content review", "not a claim to have watched every video",
                       "Upload years are not selection years",
                       "Further playlist-wide content review remains incomplete"):
            self.assertIn(caveat, text)

    def test_every_exported_prompt_is_identical_in_offline_html(self):
        source = (OUTPUT / "phase2_deep_analysis.html").read_text(encoding="utf-8")
        parser = ReportParser()
        parser.feed(source)
        chapters = json.loads((OUTPUT / "phase2_chapter_study_roadmap.json").read_text(encoding="utf-8"))
        authored = load_tasks()
        exported = {}
        for row in chapters:
            key = (row["subject"], chapter_key(row["subject"], row["folder"])
                   if "folder" in row else str(row["chapter_number"]))
            self.assertEqual(len(row["tasks"]), len(authored[key]))
            title = row.get("title") or row["folder"].rsplit("-", 1)[0]
            for task, original in zip(row["tasks"], authored[key]):
                for field in ("kind", "title", "demand"):
                    self.assertEqual(task[field], original[field])
                self.assertIn(task["id"], parser.ids)
                self.assertIn(f"href='#{task['id']}'", source)
                self.assertIn(f"data-copy-prompt='{task['id']}-prompt'", source)
                self.assertIn(f"data-select-prompt='{task['id']}-prompt'", source)
                self.assertIn(f"id='{task['id']}-status'", source)
                self.assertEqual(task["prompt"], make_prompt(row["subject"], title, original))
                exported[f"{task['id']}-prompt"] = task["prompt"]
        self.assertEqual(len(exported), 480)
        self.assertEqual(parser.prompts, exported)
        self.assertEqual(parser.classes.count("study-task"), len(exported))
        self.assertIn("The browser blocked automatic copying.", source)
        self.assertIn("Automatic clipboard access is unavailable", source)
        self.assertIn("Complete prompt selected.", source)


if __name__ == "__main__":
    unittest.main()
