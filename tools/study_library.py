"""Local, source-checked storage and HTML publishing for Copilot study packets.

Published readers accept #topic=<topic-id> links to open the Read notes view and
#ga-library for the GA library. Unknown topic links show an explicit reader error.
"""

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "study_library"
SUBJECTS = {"ESI", "Finance", "Management", "GA"}
CATEGORIES = {"General", "Finance", "Economy"}
EVIDENCE_COLLECTIONS = (
    "CurrentAffairs-Monthly", "Reports_NationalAndInternational",
    "SchemesAndGovernmentPortals", "StaticGK",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value),
            f"Invalid ID: {value!r}")


def text(value):
    require(isinstance(value, str) and value.strip(), f"Expected nonempty text: {value!r}")


def unique(items, label):
    require(isinstance(items, list), f"{label} must be a list")
    seen = set()
    for item in items:
        require(isinstance(item, dict), f"{label}: expected an object")
        identifier(item["id"])
        require(item["id"] not in seen, f"{label}: duplicate ID {item['id']}")
        seen.add(item["id"])
    return seen


def workspace_path(value, root=ROOT):
    path = (root / value).resolve()
    require(path.is_relative_to(root.resolve()), f"Path leaves workspace: {value}")
    return path


def fingerprint(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_record(path, source_id, title, kind, period, root=ROOT):
    identifier(source_id)
    root = root.resolve()
    path = path.resolve()
    require(path.is_relative_to(root.resolve()), "PDF must be inside this workspace")
    require(path.suffix.lower() == ".pdf", "Expected a PDF")
    with pymupdf.open(path) as document:
        require(not document.needs_pass, "Password-protected PDF: supply an unlocked copy")
        pages = len(document)
    return dict(id=source_id, title=title, path=str(path.relative_to(root)),
                sha256=fingerprint(path), pages=pages, kind=kind, period=period)


def validate(data, root=ROOT):
    require(data["schema_version"] == 1, "Unsupported library schema")
    unique(data["sources"], "Sources")
    topic_ids = unique(data["topics"], "Topics")
    sources = {}
    for source in data["sources"]:
        text(source["title"])
        require(source["kind"] in {"notes", "monthly"}, "Source kind must be notes or monthly")
        period = source["period"]
        require(period is None or bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period)),
                "Source period must be YYYY-MM or null")
        require(source["kind"] != "monthly" or period, "Monthly PDFs need an edition month")
        path = workspace_path(source["path"], root)
        require(path.suffix.lower() == ".pdf", "Source is not a PDF")
        require(fingerprint(path) == source["sha256"],
                f"PDF changed: {source['id']}. Register the new version under a new source ID.")
        with pymupdf.open(path) as document:
            require(len(document) == source["pages"], f"Wrong page count: {source['id']}")
        sources[source["id"]] = source

    def refs(items):
        require(isinstance(items, list) and items, "Every learning item needs PDF references")
        for ref in items:
            require(ref["source"] in sources, f"Unknown source: {ref['source']}")
            require(isinstance(ref["pages"], list) and ref["pages"], "Reference needs pages")
            for page in ref["pages"]:
                require(type(page) is int and 1 <= page <= sources[ref["source"]]["pages"],
                        f"Invalid PDF page: {ref}")

    for topic in data["topics"]:
        text(topic["title"])
        text(topic["summary"])
        require(topic["subject"] in SUBJECTS, f"Unknown subject: {topic['subject']}")
        require(isinstance(topic["tags"], list), "Tags must be a list")
        for tag in topic["tags"]:
            text(tag)
        for related in topic["related"]:
            require(related in topic_ids and related != topic["id"], "Invalid related topic")
        unique(topic.get("teaching_notes", []), "Teaching-note sections")
        for section in topic.get("teaching_notes", []):
            text(section["title"])
            require(isinstance(section["paragraphs"], list) and section["paragraphs"],
                    "Teaching-note sections need explanatory paragraphs")
            for value in section["paragraphs"]:
                text(value)
            refs(section["refs"])
        unique(topic.get("study_plan", []), "Study-plan entries")
        for entry in topic.get("study_plan", []):
            text(entry["title"])
            text(entry["focus"])
            require(entry["priority"] in {"P1", "P2", "P3"}, "Invalid study-plan priority")
            require(("topic" in entry) != ("section" in entry),
                    "Study-plan entry needs exactly one topic or section target")
            if "topic" in entry:
                require(entry["topic"] in topic_ids and entry["topic"] != topic["id"],
                        "Invalid study-plan chapter")
            else:
                require(entry["section"] in {
                    section["id"] for section in topic.get("teaching_notes", [])
                }, "Invalid study-plan explanation")
            refs(entry["refs"])
        nodes = unique(topic["map"]["nodes"], "Map nodes")
        require(1 <= len(nodes) <= 12, "Use small topic maps: 1 to 12 nodes")
        for node in topic["map"]["nodes"]:
            text(node["label"])
            require(len(node["label"]) <= 140, "Map node is too long; split the topic")
            refs(node["refs"])
        unique(topic["map"]["edges"], "Map connections")
        for edge in topic["map"]["edges"]:
            require(edge["from"] in nodes and edge["to"] in nodes, "Unknown connection endpoint")
            text(edge["label"])
            refs(edge["refs"])
        unique(topic["tables"], "Tables")
        for table in topic["tables"]:
            text(table["title"])
            require(isinstance(table["columns"], list) and 1 <= len(table["columns"]) <= 8,
                    "Tables need 1 to 8 columns")
            for column in table["columns"]:
                text(column)
            unique(table["rows"], "Table rows")
            for row in table["rows"]:
                require(len(row["cells"]) == len(table["columns"]), "Table row width mismatch")
                for cell in row["cells"]:
                    text(cell)
                refs(row["refs"])
        unique(topic["cards"], "Recall cards")
        for card in topic["cards"]:
            text(card["question"])
            text(card["answer"])
            refs(card["refs"])
        unique(topic["facts"], "Facts")
        for fact in topic["facts"]:
            text(fact["label"])
            unique(fact["observations"], "Fact observations")
            require(fact["observations"], "Fact needs at least one observation")
            for observation in fact["observations"]:
                text(observation["value"])
                text(observation["as_of"])
                refs(observation["refs"])
        unique(topic["updates"], "Current-affairs updates")
        for update in topic["updates"]:
            require(update["category"] in CATEGORIES, "Unknown current-affairs category")
            require(bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])(?:-(0[1-9]|[12]\d|3[01]))?",
                                      update["date"])), "Update date must be YYYY-MM[-DD]")
            text(update["title"])
            text(update["body"])
            refs(update["refs"])
    require(isinstance(data["imports"], list), "Imports must be a list")


def empty_library():
    return {"schema_version": 1, "sources": [], "topics": [], "imports": []}


def merge_list(old, new, merge_item=None):
    unique(new, "Incoming items")
    result = copy.deepcopy(old)
    positions = {item["id"]: index for index, item in enumerate(result)}
    for item in new:
        key = item["id"]
        if key not in positions:
            positions[key] = len(result)
            result.append(copy.deepcopy(item))
        elif merge_item:
            index = positions[key]
            result[index] = merge_item(result[index], item)
        else:
            require(result[positions[key]] == item,
                    f"ID {key} already exists with different content. Use a new ID; history is immutable.")
    return result


def merge_table(old, new):
    require(old["title"] == new["title"] and old["columns"] == new["columns"],
            "Changed table structure: use a new table ID")
    return {**old, "rows": merge_list(old["rows"], new["rows"])}


def merge_fact(old, new):
    require(old["label"] == new["label"], "Changed fact definition: use a new fact ID")
    return {**old, "observations": merge_list(old["observations"], new["observations"])}


def merge_source(old, new):
    require({key: value for key, value in old.items() if key != "path"} ==
            {key: value for key, value in new.items() if key != "path"},
            f"Source {old['id']} changed: only a byte-identical PDF relocation is permitted")
    return copy.deepcopy(old)


def merge_topic(old, new):
    require(old["title"] == new["title"] and old["subject"] == new["subject"],
            "Changed topic identity: retain the original title/subject or use a new topic ID")
    # Summary is retained; additions belong to dated updates or source-linked learning items.
    require(old["summary"] == new["summary"], "Keep the topic summary; add a dated update instead")
    result = copy.deepcopy(old)
    for key in ("tags", "related"):
        result[key] = list(dict.fromkeys(old[key] + new[key]))
    result["map"] = {
        key: merge_list(old["map"][key], new["map"][key]) for key in ("nodes", "edges")
    }
    for key, merger in (("tables", merge_table), ("cards", None),
                        ("facts", merge_fact), ("updates", None)):
        result[key] = merge_list(old[key], new[key], merger)
    if "teaching_notes" in old or "teaching_notes" in new:
        result["teaching_notes"] = merge_list(
            old.get("teaching_notes", []), new.get("teaching_notes", []))
    if "study_plan" in old or "study_plan" in new:
        result["study_plan"] = merge_list(old.get("study_plan", []), new.get("study_plan", []))
    return result


def merge_bundle(data, bundle, root=ROOT):
    require(bundle["schema_version"] == 1, "Unsupported bundle schema")
    require(set(bundle) <= {"schema_version", "sources", "topics"}, "Unexpected bundle fields")
    unique(bundle["sources"], "Bundle sources")
    unique(bundle["topics"], "Bundle topics")
    result = copy.deepcopy(data)
    result["sources"] = merge_list(data["sources"], bundle["sources"], merge_source)
    result["topics"] = merge_list(data["topics"], bundle["topics"], merge_topic)
    validate(result, root)
    if result != data:
        result["imports"].append({
            "at": datetime.now(timezone.utc).isoformat(),
            "bundle_sha256": hashlib.sha256(json.dumps(bundle, sort_keys=True).encode()).hexdigest(),
            "topics": [topic["id"] for topic in bundle["topics"]],
        })
    return result


def review_facts(topic):
    return [fact for fact in topic["facts"]
            if len({item["value"].strip().casefold() for item in fact["observations"]}) > 1]


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(name, path)
    finally:
        if Path(name).exists():
            Path(name).unlink()


def cited_pages(topics):
    result = {}

    def collect(value):
        if isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, dict):
            if "source" in value and "pages" in value:
                result.setdefault(value["source"], set()).update(value["pages"])
            else:
                for item in value.values():
                    collect(item)

    collect(topics)
    return result


def scan_evidence(data, directory=LIBRARY, root=ROOT):
    """Read every evidence PDF page, including previously scanned/cited pages."""
    manifest_path = directory / "evidence_scan.json"
    previous = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    old_files = {item["path"]: item for item in previous.get("files", [])}
    sources_by_path = {}
    for source in data["sources"]:
        sources_by_path.setdefault(source["path"], []).append(source)
    ga_pages = cited_pages([topic for topic in data["topics"] if topic["subject"] == "GA"])
    all_pages = cited_pages(data["topics"])
    now = datetime.now(timezone.utc).isoformat()
    files = []
    missing_collections = []
    for collection in EVIDENCE_COLLECTIONS:
        folder = root / "SubjectNotesForPhase2" / collection
        if not folder.is_dir():
            missing_collections.append(collection)
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix.lower() != ".pdf":
                continue
            workspace_path(path, root)
            relative = str(path.relative_to(root))
            sha = fingerprint(path)
            known = sources_by_path.get(relative, [])
            current = [source for source in known if source["sha256"] == sha]
            old = old_files.get(relative, {})
            old_pages = {page["page"]: page for page in old.get("pages", [])}
            page_records, extracted = [], []
            with pymupdf.open(path) as document:
                require(not document.needs_pass, f"Unlock evidence PDF before scanning: {relative}")
                stream_hashes = {}
                for number, page in enumerate(document, 1):
                    content = page.get_text(sort=True)
                    digest = hashlib.sha256(content.encode("utf-8"))
                    xrefs = set(page.get_contents())
                    xrefs.update(image[0] for image in page.get_images(full=True) if image[0])
                    xrefs.update(obj[0] for obj in page.get_xobjects())
                    for xref in sorted(xrefs):
                        if xref not in stream_hashes:
                            stream = document.xref_stream(xref)
                            stream_hashes[xref] = hashlib.sha256(
                                document.xref_object(xref).encode("utf-8") +
                                (stream if stream is not None else b"")).digest()
                        digest.update(stream_hashes[xref])
                    page_hash = digest.hexdigest()
                    old_page = old_pages.get(number)
                    change = "new" if not old_page else (
                        "unchanged" if old_page["sha256"] == page_hash else "changed")
                    page_records.append({
                        "page": number, "sha256": page_hash, "characters": len(content.strip()),
                        "needs_ocr": len(content.strip()) < 50, "change": change,
                        "last_changed_at": now if change != "unchanged" else old_page["last_changed_at"],
                        "cited": any(number in all_pages.get(s["id"], set()) for s in current),
                        "ga_cited": any(number in ga_pages.get(s["id"], set()) for s in current),
                    })
                    extracted.append({"page": number, "text": content})
            path_key = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:16]
            text_file = Path("scan_text") / f"{path_key}_{sha}.json"
            atomic_write(directory / text_file, json.dumps(
                {"path": relative, "sha256": sha, "pages": extracted}, ensure_ascii=True) + "\n")
            files.append({
                "path": relative, "collection": collection, "sha256": sha,
                "source_ids": [source["id"] for source in current],
                "registration": "registered" if current else ("changed PDF" if known else "not registered"),
                "change": "new" if not old else ("unchanged" if old["sha256"] == sha else "changed"),
                "pages": page_records, "text_file": str(text_file),
            })
    removed = sorted(set(old_files) - {item["path"] for item in files})
    manifest = {"schema_version": 1, "scanned_at": now, "files": files,
                "missing_collections": missing_collections, "removed_paths": removed}
    atomic_write(manifest_path, json.dumps(manifest, indent=2) + "\n")
    return manifest


def publish(data, directory=LIBRARY, root=ROOT):
    validate(data, root)
    view = copy.deepcopy(data)
    for source in view["sources"]:
        source["href"] = Path(os.path.relpath(
            workspace_path(source["path"], root), directory.resolve())).as_posix()
    scan_path = directory / "evidence_scan.json"
    if scan_path.exists():
        view["evidence_scan"] = json.loads(scan_path.read_text(encoding="utf-8"))
    template = Path(__file__).with_suffix(".html").read_text(encoding="utf-8")
    payload = json.dumps(view, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e")
    require(template.count("STUDY_DATA_PLACEHOLDER") == 1, "Invalid HTML template")
    atomic_write(directory / "index.html", template.replace("STUDY_DATA_PLACEHOLDER", payload))


def parse_pages(value, count):
    if not value:
        return list(range(1, count + 1))
    result = set()
    for part in value.split(","):
        bounds = [int(item) for item in part.split("-")]
        require(len(bounds) in {1, 2}, "Use page lists such as 2,5-8")
        first, last = bounds[0], bounds[-1]
        require(1 <= first <= last <= count, f"Invalid page range: {part}")
        result.update(range(first, last + 1))
    return sorted(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="Extract local PDF pages for Copilot review; not AI generation")
    extract.add_argument("pdf", type=Path)
    extract.add_argument("--id", required=True)
    extract.add_argument("--title", required=True)
    extract.add_argument("--kind", choices=("notes", "monthly"), default="notes")
    extract.add_argument("--period", help="Monthly edition YYYY-MM")
    extract.add_argument("--pages", help="One-based PDF pages, e.g. 2,5-8")
    extract.add_argument("--output", required=True, type=Path)
    merge = commands.add_parser("merge", help="Validate and append an AI-curated JSON bundle")
    merge.add_argument("bundle", type=Path)
    relocate = commands.add_parser("relocate", help="Repair a renamed PDF path after verifying identical bytes")
    relocate.add_argument("source_id")
    relocate.add_argument("pdf", type=Path)
    for name in ("build", "check", "scan"):
        commands.add_parser(name)
    args = parser.parse_args()
    if args.command == "extract":
        source = source_record(args.pdf, args.id, args.title, args.kind, args.period)
        validate({**empty_library(), "sources": [source]})
        with pymupdf.open(args.pdf) as document:
            pages = [{"page": n, "text": document[n - 1].get_text(sort=True)}
                     for n in parse_pages(args.pages, len(document))]
        unreadable = [page["page"] for page in pages if len(page["text"].strip()) < 50]
        require(not unreadable,
                f"Pages {unreadable} have too little text. OCR or visually review them; extraction not saved.")
        atomic_write(args.output, json.dumps({"source": source, "pages": pages}, indent=2))
        print(f"Extracted {len(pages)} pages to {args.output}. Copilot must read and curate them.")
        return
    data_path = LIBRARY / "library.json"
    data = json.loads(data_path.read_text(encoding="utf-8")) if data_path.exists() else empty_library()
    if args.command == "relocate":
        source = next((source for source in data["sources"] if source["id"] == args.source_id), None)
        require(source is not None, f"Unknown source ID: {args.source_id}")
        candidate = source_record(args.pdf, source["id"], source["title"],
                                  source["kind"], source["period"])
        require(candidate["sha256"] == source["sha256"] and candidate["pages"] == source["pages"],
                "Relocation requires byte-identical PDF content; register changed content separately")
        require(not any(item["id"] != source["id"] and
                        workspace_path(item["path"]) == workspace_path(candidate["path"])
                        for item in data["sources"]),
                "Another source ID already registers the destination PDF")
        # Other missing paths may need independent relocation before a complete build is possible.
        if source["path"] != candidate["path"]:
            digest = hashlib.sha256(data_path.read_bytes()).hexdigest()[:16]
            atomic_write(LIBRARY / "history" / f"{digest}.json",
                         json.dumps(data, ensure_ascii=True, indent=2) + "\n")
            source["path"] = candidate["path"]
            atomic_write(data_path, json.dumps(data, ensure_ascii=True, indent=2) + "\n")
        print(f"Verified identical PDF and repaired path: {source['id']} -> {source['path']}")
        print("Run build after all renamed source paths have been repaired.")
        return
    if args.command == "scan":
        manifest = scan_evidence(data)
        pages = [page for item in manifest["files"] for page in item["pages"]]
        print(f"Scanned {len(manifest['files'])} PDFs / {len(pages)} pages; "
              f"{sum(p['needs_ocr'] for p in pages)} low-text pages need OCR/visual review; "
              f"{sum(not p['ga_cited'] for p in pages)} pages not yet cited in GA.")
        print(f"Missing collections: {manifest['missing_collections']}; removed files: {manifest['removed_paths']}")
        print("Machine scan is not semantic review or proof of complete fact extraction.")
        publish(data)
        return
    validate(data)
    if args.command == "merge":
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        merged = merge_bundle(data, bundle)
        if merged != data:
            # Keep the exact previous database as well as immutable in-database observations.
            if data_path.exists():
                digest = hashlib.sha256(data_path.read_bytes()).hexdigest()[:16]
                atomic_write(LIBRARY / "history" / f"{digest}.json",
                             json.dumps(data, ensure_ascii=True, indent=2) + "\n")
            atomic_write(data_path, json.dumps(merged, ensure_ascii=True, indent=2) + "\n")
        data = merged
    if args.command != "check":
        scan_evidence(data)
        publish(data)
    flagged = sum(len(review_facts(topic)) for topic in data["topics"])
    print(f"{len(data['topics'])} topics; {len(data['sources'])} PDFs; {flagged} differing facts for review.")
    print("Validated" if args.command == "check" else f"Published {LIBRARY / 'index.html'}")


if __name__ == "__main__":
    main()
