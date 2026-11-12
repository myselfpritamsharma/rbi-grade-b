import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf

from study_library import (
    empty_library, merge_bundle, parse_pages, publish, review_facts, scan_evidence,
    source_record, validate,
)


class StudyLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="rbi-study-library-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        pdf = self.root / "source.pdf"
        with pymupdf.open() as document:
            page = document.new_page()
            page.insert_text((40, 40), "Source evidence for locally generated study-library tests.")
            document.save(pdf)
        self.source = source_record(pdf, "source-one", "Test notes", "notes", None, self.root)
        self.refs = [{"source": "source-one", "pages": [1]}]
        self.topic = {
            "id": "topic-a", "title": "Test topic", "subject": "ESI", "summary": "Test overview",
            "tags": [], "related": [],
            "map": {"nodes": [{"id": "root", "label": "Root", "refs": self.refs}], "edges": []},
            "tables": [{"id": "comparison", "title": "Compare", "columns": ["Item", "Meaning"],
                        "rows": [{"id": "row-a", "cells": ["A", "Meaning"], "refs": self.refs}]}],
            "cards": [{"id": "card-a", "question": "Why?", "answer": "Because", "refs": self.refs}],
            "facts": [{"id": "rate", "label": "Example rate",
                       "observations": [{"id": "old", "value": "6%", "as_of": "2026-09",
                                         "refs": self.refs}]}],
            "updates": [],
        }
        self.bundle = {"schema_version": 1, "sources": [self.source], "topics": [self.topic]}

    def initial(self):
        return merge_bundle(empty_library(), self.bundle, self.root)

    def test_identical_reimport_does_not_change_data_or_history(self):
        first = self.initial()
        self.assertEqual(first, merge_bundle(first, self.bundle, self.root))

    def test_appends_preserve_unrelated_topics_and_items(self):
        first = self.initial()
        second_topic = copy.deepcopy(self.topic)
        second_topic["id"] = "topic-b"
        first = merge_bundle(first, {"schema_version": 1, "sources": [], "topics": [second_topic]},
                             self.root)
        update = copy.deepcopy(self.topic)
        update["cards"] = [{"id": "card-b", "question": "New?", "answer": "Yes", "refs": self.refs}]
        update["tables"][0]["rows"] = [
            {"id": "row-b", "cells": ["B", "Another meaning"], "refs": self.refs}
        ]
        merged = merge_bundle(first, {"schema_version": 1, "sources": [], "topics": [update]},
                              self.root)
        self.assertEqual(merged["topics"][1], first["topics"][1])
        self.assertEqual(len(merged["topics"][0]["cards"]), 2)
        self.assertEqual(len(merged["topics"][0]["tables"][0]["rows"]), 2)
        self.assertEqual(len(first["topics"][0]["cards"]), 1)

    def test_differing_fact_is_retained_and_flagged(self):
        first = self.initial()
        update = copy.deepcopy(self.topic)
        update["facts"][0]["observations"] = [
            {"id": "new", "value": "7%", "as_of": "2026-10", "refs": self.refs}
        ]
        merged = merge_bundle(first, {"schema_version": 1, "sources": [], "topics": [update]},
                              self.root)
        self.assertEqual(len(review_facts(merged["topics"][0])), 1)
        self.assertEqual([o["value"] for o in merged["topics"][0]["facts"][0]["observations"]],
                         ["6%", "7%"])

    def test_study_plan_targets_are_validated_preserved_and_immutable(self):
        data = self.initial()
        topic = copy.deepcopy(self.topic)
        topic["teaching_notes"] = [{
            "id": "mechanism", "title": "Mechanism", "paragraphs": ["Explained mechanism."],
            "refs": self.refs,
        }]
        topic["study_plan"] = [{
            "id": "target", "title": "Mechanism", "focus": "Definition and worked example",
            "priority": "P1", "section": "mechanism", "refs": self.refs,
        }]
        bundle = {"schema_version": 1, "sources": [], "topics": [topic]}
        merged = merge_bundle(data, bundle, self.root)
        self.assertEqual(merge_bundle(merged, bundle, self.root), merged)
        self.assertEqual(merged["topics"][0]["cards"], data["topics"][0]["cards"])
        invalid = copy.deepcopy(bundle)
        invalid["topics"][0]["study_plan"][0]["focus"] = "Silently replacing a target"
        with self.assertRaisesRegex(ValueError, "already exists"):
            merge_bundle(merged, invalid, self.root)
        for field, value, message in [
            ("section", "missing", "Invalid study-plan explanation"),
            ("priority", "P9", "Invalid study-plan priority"),
        ]:
            invalid = copy.deepcopy(merged)
            invalid["topics"][0]["study_plan"][0][field] = value
            with self.assertRaisesRegex(ValueError, message):
                validate(invalid, self.root)
        invalid = copy.deepcopy(merged)
        invalid["topics"][0]["study_plan"][0]["topic"] = "topic-a"
        with self.assertRaisesRegex(ValueError, "exactly one"):
            validate(invalid, self.root)
        chapter = copy.deepcopy(self.topic)
        chapter["id"] = "chapter-b"
        topic["study_plan"][0].pop("section")
        topic["study_plan"][0]["topic"] = "chapter-b"
        result = merge_bundle(data, {"schema_version": 1, "sources": [],
                                    "topics": [topic, chapter]}, self.root)
        publish(result, self.root / "site", self.root)
        html = (self.root / "site" / "index.html").read_text(encoding="utf-8")
        payload = html.split('<script id="library-data" type="application/json">')[1].split("</script>")[0]
        self.assertEqual(json.loads(payload)["topics"][0]["study_plan"], topic["study_plan"])
        topic["study_plan"][0]["topic"] = "missing"
        with self.assertRaisesRegex(ValueError, "Invalid study-plan chapter"):
            merge_bundle(data, {"schema_version": 1, "sources": [],
                                "topics": [topic, chapter]}, self.root)

    def test_no_silent_overwrite(self):
        first = self.initial()
        update = copy.deepcopy(self.topic)
        update["cards"][0]["answer"] = "Overwritten"
        with self.assertRaisesRegex(ValueError, "already exists"):
            merge_bundle(first, {"schema_version": 1, "sources": [], "topics": [update]}, self.root)

    def test_teaching_notes_append_without_losing_legacy_learning_content(self):
        first = self.initial()
        update = copy.deepcopy(self.topic)
        section = {"id": "explain-a", "title": "Understand the concept",
                   "paragraphs": ["A complete explanation.", "An illustrative example."],
                   "refs": self.refs}
        update["teaching_notes"] = [section]
        bundle = {"schema_version": 1, "sources": [], "topics": [update]}
        merged = merge_bundle(first, bundle, self.root)
        self.assertEqual(merged["topics"][0]["teaching_notes"], [section])
        for field in ("cards", "facts", "tables", "map", "updates"):
            self.assertEqual(merged["topics"][0][field], first["topics"][0][field])
        self.assertEqual(merged, merge_bundle(merged, bundle, self.root))
        old_import = {"schema_version": 1, "sources": [], "topics": [copy.deepcopy(self.topic)]}
        self.assertEqual(merged, merge_bundle(merged, old_import, self.root))
        update["teaching_notes"].append({
            "id": "explain-b", "title": "A new development",
            "paragraphs": ["An additional source-backed explanation."], "refs": self.refs})
        extended = merge_bundle(merged, bundle, self.root)
        self.assertEqual(len(extended["topics"][0]["teaching_notes"]), 2)

    def test_teaching_notes_are_validated_and_immutable(self):
        base = self.initial()
        section = {"id": "explain-a", "title": "Explanation",
                   "paragraphs": ["A source-backed explanation."], "refs": self.refs}
        for key, bad in [("paragraphs", []), ("paragraphs", "Not a paragraph list"),
                         ("paragraphs", [""]), ("refs", []),
                         ("refs", [{"source": "source-one", "pages": [2]}])]:
            invalid = copy.deepcopy(base)
            invalid["topics"][0]["teaching_notes"] = [{**section, key: bad}]
            with self.assertRaises(ValueError):
                validate(invalid, self.root)
        update = copy.deepcopy(self.topic)
        update["teaching_notes"] = [section]
        bundle = {"schema_version": 1, "sources": [], "topics": [update]}
        merged = merge_bundle(base, bundle, self.root)
        update["teaching_notes"][0]["paragraphs"] = ["Silently changed explanation."]
        with self.assertRaisesRegex(ValueError, "already exists"):
            merge_bundle(merged, bundle, self.root)

    def test_teaching_notes_publish_without_executing_user_text(self):
        data = self.initial()
        value = "</script><script>alert('not executable')</script>"
        data["topics"][0]["teaching_notes"] = [{
            "id": "explain-a", "title": "Original explanation",
            "paragraphs": [value], "refs": self.refs}]
        publish(data, self.root / "site", self.root)
        html = (self.root / "site" / "index.html").read_text(encoding="utf-8")
        embedded = json.loads(html.split('<script id="library-data" type="application/json">')[1].split("</script>")[0])
        self.assertNotIn(value, html)
        self.assertEqual(embedded["topics"][0]["teaching_notes"][0]["paragraphs"], [value])
        self.assertIn('["sources","Sources",renderNoteSources]', html)
        self.assertIn("function renderTeaching", html)

    def test_invalid_page_and_missing_references(self):
        for bad in ([{"source": "source-one", "pages": [2]}], [], [{"source": "missing", "pages": [1]}]):
            data = self.initial()
            data["topics"][0]["cards"][0]["refs"] = bad
            with self.assertRaises(ValueError):
                validate(data, self.root)

    def test_rejects_duplicate_ids_and_broken_map_edges(self):
        data = self.initial()
        data["topics"][0]["cards"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate ID"):
            validate(data, self.root)
        data = self.initial()
        data["topics"][0]["map"]["edges"] = [
            {"id": "edge", "from": "root", "to": "missing", "label": "invalid", "refs": self.refs}
        ]
        with self.assertRaisesRegex(ValueError, "endpoint"):
            validate(data, self.root)

    def test_changed_source_and_outside_path_rejected(self):
        data = self.initial()
        data["sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "PDF changed"):
            validate(data, self.root)
        data["sources"][0]["path"] = str(self.root.parent / "outside.pdf")
        with self.assertRaisesRegex(ValueError, "leaves workspace"):
            validate(data, self.root)

    def test_monthly_source_requires_edition(self):
        data = self.initial()
        data["sources"][0]["kind"] = "monthly"
        with self.assertRaisesRegex(ValueError, "edition"):
            validate(data, self.root)

    def test_old_bundle_after_exact_pdf_rename_retains_current_registered_path(self):
        data = self.initial()
        renamed = self.root / "renamed.pdf"
        (self.root / "source.pdf").rename(renamed)
        data["sources"][0]["path"] = "renamed.pdf"
        self.assertEqual(data, merge_bundle(data, self.bundle, self.root))
        invalid = copy.deepcopy(self.bundle)
        invalid["sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Source source-one changed"):
            merge_bundle(data, invalid, self.root)
        invalid = copy.deepcopy(self.bundle)
        invalid["sources"][0]["period"] = "2026-10"
        with self.assertRaisesRegex(ValueError, "Source source-one changed"):
            merge_bundle(data, invalid, self.root)

    def test_cli_relocate_requires_identical_content_and_preserves_a_snapshot(self):
        tools = self.root / "tools"
        tools.mkdir()
        for name in ("study_library.py", "study_library.html"):
            shutil.copyfile(Path(__file__).parent / name, tools / name)
        directory = self.root / "study_library"
        directory.mkdir()
        database = directory / "library.json"
        original = self.initial()
        database.write_text(json.dumps(original), encoding="utf-8")
        renamed = self.root / "renamed.pdf"
        (self.root / "source.pdf").rename(renamed)
        command = [sys.executable, str(tools / "study_library.py"), "relocate", "source-one"]
        result = subprocess.run(command + [str(renamed)], check=True,
                                capture_output=True, text=True)
        self.assertIn("Verified identical PDF", result.stdout)
        persisted = json.loads(database.read_text(encoding="utf-8"))
        self.assertEqual(persisted["sources"][0]["path"], "renamed.pdf")
        self.assertEqual(persisted["topics"], original["topics"])
        self.assertEqual(persisted["imports"], original["imports"])
        snapshots = list((directory / "history").glob("*.json"))
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(json.loads(snapshots[0].read_text(encoding="utf-8")), original)
        saved = database.read_bytes()
        changed = self.root / "changed.pdf"
        with pymupdf.open() as document:
            page = document.new_page()
            page.insert_text((40, 40), "Different evidence cannot replace an immutable source.")
            document.save(changed)
        failure = subprocess.run(command + [str(changed)], capture_output=True, text=True)
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn("byte-identical PDF", failure.stderr)
        self.assertEqual(saved, database.read_bytes())

    def test_page_selection(self):
        self.assertEqual(parse_pages("1,3-5,3", 5), [1, 3, 4, 5])
        for value in ("0", "6", "4-2"):
            with self.assertRaises(ValueError):
                parse_pages(value, 5)

    def test_offline_render_embeds_safe_json(self):
        data = self.initial()
        data["topics"][0]["summary"] = "</script><script>alert('not executable')</script>"
        publish(data, self.root / "site", self.root)
        html = (self.root / "site" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn(data["topics"][0]["summary"], html)
        self.assertNotIn("STUDY_DATA_PLACEHOLDER", html)
        payload = html.split('<script id="library-data" type="application/json">')[1].split("</script>")[0]
        embedded = json.loads(payload)
        self.assertEqual(embedded["topics"][0]["summary"], data["topics"][0]["summary"])
        self.assertEqual(embedded["sources"][0]["href"], "../source.pdf")
        self.assertNotIn("<script src=", html)
        self.assertIn('id="priority"', html)
        self.assertIn('id="source-list"', html)
        self.assertIn('id="collection"', html)
        self.assertIn('id="collection-coverage"', html)
        self.assertIn("StaticGK background", html)
        self.assertIn("Evidence links", html)
        self.assertIn("Reference only", html)
        self.assertIn('id="ga-library"', html)
        self.assertIn('id="ga-rows"', html)
        self.assertIn('id="ga-scan-summary"', html)
        self.assertIn('window.addEventListener("beforeprint"', html)
        self.assertIn('window.addEventListener("afterprint"', html)
        self.assertIn('activeTab="notes"', html)
        self.assertIn('["notes","Read notes",renderNotes]', html)
        self.assertIn('id="ga-format"', html)
        self.assertIn('id="ga-notes"', html)
        self.assertIn("Source pages (optional verification)", html)

    def evidence_pdf(self, collection="StaticGK"):
        folder = self.root / "SubjectNotesForPhase2" / collection
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "evidence.pdf"
        shutil.copyfile(self.root / "source.pdf", path)
        return path

    def test_scan_reads_all_four_collections_and_caches_every_page(self):
        for collection in ("CurrentAffairs-Monthly", "Reports_NationalAndInternational",
                           "SchemesAndGovernmentPortals", "StaticGK"):
            self.evidence_pdf(collection)
        site = self.root / "site"
        first = scan_evidence(self.initial(), site, self.root)
        self.assertEqual(len(first["files"]), 4)
        self.assertEqual(first["missing_collections"], [])
        self.assertTrue(all(item["pages"][0]["change"] == "new" for item in first["files"]))
        second = scan_evidence(self.initial(), site, self.root)
        self.assertTrue(all(item["pages"][0]["change"] == "unchanged" for item in second["files"]))
        for item in second["files"]:
            extracted = json.loads((site / item["text_file"]).read_text(encoding="utf-8"))
            self.assertEqual(extracted["path"], item["path"])
            self.assertEqual(len(extracted["pages"]), 1)
            self.assertIn("Source evidence", extracted["pages"][0]["text"])

    def test_scan_reports_changed_new_removed_and_low_text_pages(self):
        path = self.evidence_pdf()
        site = self.root / "site"
        data = self.initial()
        scan_evidence(data, site, self.root)
        with pymupdf.open() as document:
            page = document.new_page()
            page.insert_text((40, 40), "Changed content that must be found on a repeated evidence scan.")
            document.new_page()
            document.save(path)
        changed = scan_evidence(data, site, self.root)
        pages = changed["files"][0]["pages"]
        self.assertEqual([page["change"] for page in pages], ["changed", "new"])
        self.assertTrue(pages[1]["needs_ocr"])
        self.assertIn("Reports_NationalAndInternational", changed["missing_collections"])
        path.unlink()
        removed = scan_evidence(data, site, self.root)
        self.assertEqual(removed["removed_paths"], [str(path.relative_to(self.root))])

    def test_scan_only_counts_current_version_citations_as_ga_coverage(self):
        path = self.evidence_pdf()
        data = self.initial()
        data["sources"][0] = source_record(path, "source-one", "Evidence", "notes", None, self.root)
        data["topics"][0]["subject"] = "GA"
        site = self.root / "site"
        first = scan_evidence(data, site, self.root)
        self.assertTrue(first["files"][0]["pages"][0]["ga_cited"])
        with pymupdf.open() as document:
            page = document.new_page()
            page.insert_text((40, 40), "A revised source with a different value and an old stored citation.")
            document.save(path)
        changed = scan_evidence(data, site, self.root)
        self.assertEqual(changed["files"][0]["registration"], "changed PDF")
        self.assertFalse(changed["files"][0]["pages"][0]["ga_cited"])

    def test_scan_detects_changed_image_content_without_text(self):
        path = self.root / "SubjectNotesForPhase2" / "StaticGK" / "image.pdf"
        path.parent.mkdir(parents=True)

        def image_pdf(color):
            with pymupdf.open() as document:
                page = document.new_page()
                image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 10, 10))
                image.clear_with(color)
                page.insert_image(pymupdf.Rect(20, 20, 100, 100), pixmap=image)
                document.save(path)

        image_pdf(255)
        scan_evidence(self.initial(), self.root / "site", self.root)
        image_pdf(0)
        changed = scan_evidence(self.initial(), self.root / "site", self.root)
        self.assertEqual(changed["files"][0]["pages"][0]["change"], "changed")
        self.assertTrue(changed["files"][0]["pages"][0]["needs_ocr"])

    def test_scan_manifest_is_published_without_changing_the_database(self):
        self.evidence_pdf()
        data = self.initial()
        original = copy.deepcopy(data)
        site = self.root / "site"
        manifest = scan_evidence(data, site, self.root)
        publish(data, site, self.root)
        html = (site / "index.html").read_text(encoding="utf-8")
        embedded = json.loads(html.split('<script id="library-data" type="application/json">')[1].split("</script>")[0])
        self.assertEqual(embedded["evidence_scan"], manifest)
        self.assertEqual(data, original)

    def test_new_month_is_detected_and_appended_without_losing_old_observations(self):
        october = self.evidence_pdf("CurrentAffairs-Monthly")
        data = self.initial()
        data["sources"][0] = source_record(
            october, "source-one", "October", "monthly", "2026-10", self.root)
        data["topics"][0]["subject"] = "GA"
        site = self.root / "site"
        scan_evidence(data, site, self.root)
        november = october.with_name("november.pdf")
        shutil.copyfile(october, november)
        new_source = source_record(
            november, "source-november", "November", "monthly", "2026-11", self.root)
        update = copy.deepcopy(data["topics"][0])
        update["facts"][0]["observations"] = [{
            "id": "november", "value": "7%", "as_of": "2026-11",
            "refs": [{"source": "source-november", "pages": [1]}],
        }]
        merged = merge_bundle(data, {"schema_version": 1, "sources": [new_source],
                                     "topics": [update]}, self.root)
        scan = scan_evidence(merged, site, self.root)
        self.assertEqual(len(scan["files"]), 2)
        self.assertEqual({item["change"] for item in scan["files"]}, {"new", "unchanged"})
        self.assertTrue(all(item["pages"][0]["ga_cited"] for item in scan["files"]))
        self.assertEqual(len(merged["topics"][0]["facts"][0]["observations"]), 2)
        self.assertEqual(len(review_facts(merged["topics"][0])), 1)
        self.assertEqual(merged, merge_bundle(
            merged, {"schema_version": 1, "sources": [new_source], "topics": [update]}, self.root))

    def test_priority_and_reference_notes_survive_publishing(self):
        data = self.initial()
        data["topics"][0]["tags"] = ["P1 - Core depth"]
        data["sources"][0]["coverage_note"] = "Selected pages only"
        publish(data, self.root / "site", self.root)
        html = (self.root / "site" / "index.html").read_text(encoding="utf-8")
        payload = html.split('<script id="library-data" type="application/json">')[1].split("</script>")[0]
        embedded = json.loads(payload)
        self.assertEqual(embedded["topics"][0]["tags"], ["P1 - Core depth"])
        self.assertEqual(embedded["sources"][0]["coverage_note"], "Selected pages only")

    def test_four_collection_reference_paths_are_preserved(self):
        data = self.initial()
        collections = ("CurrentAffairs-Monthly", "Reports_NationalAndInternational",
                       "SchemesAndGovernmentPortals", "StaticGK")
        for index, collection in enumerate(collections):
            folder = self.root / "SubjectNotesForPhase2" / collection
            folder.mkdir(parents=True)
            shutil.copyfile(self.root / "source.pdf", folder / "evidence.pdf")
            source = source_record(folder / "evidence.pdf", f"evidence-{index}",
                                   collection, "notes", None, self.root)
            data["sources"].append(source)
            data["topics"][0]["cards"].append({
                "id": f"evidence-card-{index}", "question": "Connection?",
                "answer": "Source-linked evidence", "refs": [{"source": source["id"], "pages": [1]}],
            })
        publish(data, self.root / "site", self.root)
        html = (self.root / "site" / "index.html").read_text(encoding="utf-8")
        payload = html.split('<script id="library-data" type="application/json">')[1].split("</script>")[0]
        embedded = json.loads(payload)
        for source, collection in zip(embedded["sources"][1:], collections):
            self.assertEqual(source["href"], f"../SubjectNotesForPhase2/{collection}/evidence.pdf")
        self.assertEqual(len(embedded["topics"][0]["cards"]), 5)

    def test_cli_append_persists_snapshot_and_rebuilds_html(self):
        tools = self.root / "tools"
        tools.mkdir()
        for name in ("study_library.py", "study_library.html"):
            shutil.copyfile(Path(__file__).parent / name, tools / name)
        bundle_path = self.root / "bundle.json"

        def run(bundle):
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(tools / "study_library.py"), "merge", str(bundle_path)],
                check=True, capture_output=True, text=True,
            )

        run(self.bundle)
        database = self.root / "study_library" / "library.json"
        initial = database.read_bytes()
        run(self.bundle)
        self.assertEqual(database.read_bytes(), initial)
        self.assertFalse((database.parent / "history").exists())
        update = copy.deepcopy(self.bundle)
        update["topics"][0]["facts"][0]["observations"] = [
            {"id": "new-release", "value": "7%", "as_of": "2026-10", "refs": self.refs}
        ]
        result = run(update)
        self.assertIn("1 differing facts", result.stdout)
        snapshots = list((database.parent / "history").glob("*.json"))
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(json.loads(snapshots[0].read_text()), json.loads(initial))
        persisted = json.loads(database.read_text())
        self.assertEqual(len(persisted["topics"][0]["facts"][0]["observations"]), 2)
        self.assertIn("new-release", (database.parent / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
