"""Build question-only excerpts; use build_report.py to regenerate HTML from their JSON.

Full extraction requires --ocr-directory containing the 2019 page layout JSON
produced locally by ocr_question_pages.ps1 from rendered source pages.
"""

import argparse
import html
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf
from extract_questions import PHASE_ONE_RANGES


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "pyp_analysis"
SUBJECTS = ("Quantitative Aptitude", "Reasoning", "English")
QUESTION = re.compile(r"^[Qq]\s*[.:]?\s*([0-9IlOi]{1,3})(?:\s*[.)]|\s*$)\s*")
DIRECTION = re.compile(r"^[([]?\s*(?:directions?|passage)\b|^I[.)]\s*\d+[.)]", re.I)
RANGE = re.compile(r"(?:[Qq]\s*)?(\d{1,3})\s*[-–—]\s*(?:[Qq]\s*)?(\d{1,3})")


def topic_for(subject, text, shared=False):
    text = text.lower()
    if subject == "Quantitative Aptitude":
        if re.search(r"data sufficien|statements?.*(?:necessary|sufficient)|quantity i|quantity ii", text):
            return "Quantity comparison and data sufficiency", "Quantity comparison / data sufficiency"
        if re.search(r"number series|sequence of numbers|wrong.*series|series.*wrong|missing.*series", text):
            return "Number series", "Missing / wrong / linked number series"
        if re.search(r"quadratic|equations? .*given|[xyz][²^2]", text):
            return "Quadratic equations", "Quadratic equations / equation comparison"
        if re.search(r"\bhcf\b|\blcm\b|divisors|divisible", text):
            return "Number system", "Divisibility / HCF / LCM"
        if re.search(r"all three subjects|both a and b|venn", text):
            return "Arithmetic and standalone quantitative questions", "Sets / Venn diagrams"
        if shared and re.search(r"graph|chart|table|data|number of|ratio of", text):
            kind = "Caselet DI"
            for word, label in (("bar", "Bar-chart DI"), ("pie", "Pie-chart DI"),
                                ("line graph", "Line-chart DI"), ("table", "Tabular DI")):
                if word in text:
                    kind = label
                    break
            if "graph" in text and "table" in text:
                kind = "Mixed chart/table DI"
            return "Data interpretation", kind
        rules = [
            (r"series|wrong number|missing number", "Number series"),
            (r"quadratic|equations? .*given|[xy][²^]", "Quadratic equations"),
            (r"quantity i|quantity ii|statement i|data sufficien", "Quantity comparison / data sufficiency"),
            (r"train|speed|travel|distance|boat|stream", "Time, speed and distance"),
            (r"pipe|cistern|finish.*work|complete.*work|efficien", "Time and work / pipes"),
            (r"profit|loss|discount|marked price|cost price|selling price", "Profit, loss and discount"),
            (r"compound|simple interest|interest|invested.*rate", "Interest"),
            (r"mixture|milk|water|alloy", "Mixtures and alligation"),
            (r"partner|business|investment.*ratio", "Partnership"),
            (r"probability|random|ways|arrange.*letters", "Probability / counting"),
            (r"circle|radius|rectangle|square|volume|area|perimeter", "Mensuration"),
            (r"age|years old", "Ages"),
            (r"average", "Averages"),
            (r"percent|%|income|salary|wage", "Percentages"),
            (r"ratio|proportion", "Ratio and proportion"),
            (r"simplif|approxim", "Simplification / approximation"),
        ]
        for pattern, label in rules:
            if re.search(pattern, text):
                return "Arithmetic and standalone quantitative questions", label
        return "Other quantitative questions", "Source review / mixed quantitative"
    if subject == "Reasoning":
        for pattern, label in [
            (r"data.*sufficient|statement.*sufficient|sufficient.*answer|answered using sentences", "Data sufficiency"),
            (r"input|output|machine|step i", "Input-output"),
            (r"certain code|coded|coding", "Coding-decoding"),
            (r"assumptions?|inferences?|inferred|arguments?|strong reason|course of action|strengthen|weaken", "Critical reasoning"),
            (r"inequal|[<>≥≤]", "Inequalities"),
            (r"statements.*conclusions|syllog|only a few|all .*some|some .*all|no .*some", "Syllogisms"),
        ]:
            if re.search(pattern, text, re.S):
                return "Standalone reasoning", label
        if re.search(r"\bsit(?:ting|s)?\b|seated|seating", text):
            if re.search(r"circular|circle|round table", text):
                label = "Circular seating"
            elif re.search(r"parallel|two rows|both.*rows", text):
                label = "Parallel-row seating"
            elif re.search(r"square|rectangular|rectangle|triangular", text):
                label = "Geometric seating"
            else:
                label = "Linear / variable-person seating"
            return "Seating arrangements", label
        if shared and re.search(r"floor|storey|building|flat", text):
            return "Puzzles", "Floor / flat puzzle"
        if shared and re.search(r"\b(?:months?|dates?|days?|weeks?|schedule|born|birth|years?|ages?)\b", text) and re.search(r"persons?|people|friends?|born|birth|age|parcel|receive", text):
            return "Puzzles", "Scheduling / age / birth-year puzzle"
        if shared and re.search(r"boxes|box |stack", text):
            return "Puzzles", "Box / stacking puzzle"
        if shared and re.search(r"people|persons|different|each|seven|eight|six", text):
            return "Puzzles", "Multi-attribute / distribution puzzle"
        rules = [
            (r"syllog|all .*some|some .*all|no .*some|possibility", "Syllogisms"),
            (r"coded|code|coding", "Coding-decoding"),
            (r"input|output|step i|machine", "Input-output"),
            (r"inequal|[<>≥≤]", "Inequalities"),
            (r"north|south|east|west|direction|distance", "Direction and distance"),
            (r"\b(?:father|mother|brother|sister|daughter|son|wife|husband)\b", "Blood relations"),
            (r"rank|ranking|position|tall|height", "Order and ranking"),
            (r"assumption|inference|argument|conclusion|course of action|strengthen|weaken", "Critical reasoning"),
            (r"series|alphabet|letter|digit|number|word|symbol", "Alphanumeric / word operations"),
            (r"data sufficien|statement i|statement ii", "Data sufficiency"),
        ]
        for pattern, label in rules:
            if re.search(pattern, text):
                return "Standalone reasoning", label
        return "Other reasoning", "Source review / mixed reasoning"
    if shared and re.search(r"cloze|blanks|numbered gaps|words.*omitted|missing words", text, re.S):
        return "Cloze test / fillers", "Cloze test / fillers"
    if shared and re.search(r"(?:read|following|given) (?:the )?(?:following )?passage|comprehension", text):
        return "Reading comprehension", "Passage-based questions"
    if re.search(r"replace.*(?:part|phrase)|part.*replace|no correction|no improvement", text):
        return "Sentence / phrase improvement", "Sentence / phrase improvement"
    if re.search(r"does not logically fit|breaks the coherence|odd sentence", text):
        return "Paragraph coherence / odd sentence", "Paragraph coherence / odd sentence"
    if re.search(r"two columns|combine|connectors", text):
        return "Sentence connectors / column matching", "Sentence connectors / column matching"
    for pattern, label in [
        (r"rearrang|correct order|coherent|sequence|jumbled", "Sentence / paragraph rearrangement"),
        (r"error|incorrect|grammatically|correct sentence", "Grammar / error detection"),
        (r"blank|fill|cloze", "Cloze test / fillers"),
        (r"synonym|antonym|meaning|bold|highlighted|underlined|vocabulary|used in context", "Vocabulary / contextual usage"),
        (r"replace|replacement|improve|phrase", "Sentence / phrase improvement"),
        (r"connect|combine|starter", "Sentence connectors"),
        (r"passage|author|inference", "Reading comprehension"),
    ]:
        if re.search(pattern, text):
            return label, label
    return "Other English questions", "Source review / mixed English"


def read_lines(page, page_number, ocr_directory=None):
    if ocr_directory:
        filename = ocr_directory / f"page-{page_number:03d}.json"
        if not filename.is_file():
            raise FileNotFoundError(f"Required OCR layout not found: {filename}")
        data = json.loads(filename.read_text(encoding="utf-8-sig"))
        sx, sy = page.rect.width / data["width"], page.rect.height / data["height"]
        lines = [{"text": line["text"], "rect": pymupdf.Rect(
            line["x0"] * sx, line["y0"] * sy, line["x1"] * sx, line["y1"] * sy
        )} for line in data["lines"]]
    else:
        lines = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                if text:
                    lines.append({"text": text, "rect": pymupdf.Rect(line["bbox"])})
    return sorted(lines, key=lambda line: (round(line["rect"].y0, 1), line["rect"].x0))


def body_lines(lines, page):
    return [line for line in lines if
            40 < line["rect"].y0 < page.rect.height - 28
            and not re.match(r"^(?:RBI Grade B|EduTap|Quantitative Aptitude$|Reasoning$|English$|"
                             r"English Language$|.*Recollected Questions$)", line["text"], re.I)
            and not (line["text"].isdigit() and line["rect"].y0 < 100)]


def extract_section(document, year, subject, pages, ocr_directory):
    stream, bounds = [], {}
    for number in pages:
        page = document[number - 1]
        lines = body_lines(read_lines(page, number, ocr_directory), page)
        if any(re.match(r"^(?:.*Answer\s*Key|Answers?\s*(?:and\s*)?Explanations?|Solutions?)\s*$", line["text"], re.I)
               for line in lines[:5]):
            raise ValueError(f"Answer section unexpectedly included: {year} p{number}")
        if not lines:
            raise ValueError(f"No recoverable question content: {year} p{number}")
        bottom = page.rect.height - 28
        if not ocr_directory:
            bottom = max(line["rect"].y1 for line in lines) + 9
            for drawing in page.get_drawings():
                rect = drawing["rect"]
                if (rect.y0 > 55 and rect.y1 < page.rect.height - 45
                        and rect.height < page.rect.height * 0.65):
                    bottom = max(bottom, rect.y1 + 5)
        bounds[number] = (min(line["rect"].y0 for line in lines), bottom)
        stream.extend({**line, "page": number} for line in lines)
    events = []
    for index, line in enumerate(stream):
        text = line["text"]
        match = QUESTION.match(text)
        # OCR occasionally drops the Q before a complete question line.
        if not match and year == 2019 and subject == "Reasoning":
            match = re.match(r"^(60)[.)]\s+Statement:", text)
        manual_number = None
        if not match and year == 2019 and line["page"] == 39:
            # Q100's printed label was visually verified; OCR omitted only the label.
            if text.startswith("Which Of the following will be the fourth statement"):
                manual_number = 100
        if match or manual_number is not None:
            number = manual_number if manual_number is not None else int(
                match.group(1).translate(str.maketrans({"I": "1", "l": "1", "i": "1", "O": "0"})))
            events.append({"kind": "question", "number": number, "index": index})
        elif DIRECTION.match(text):
            events.append({"kind": "context", "index": index})
    if not events:
        raise ValueError(f"No question markers found: {year} {subject}")
    if events[0]["index"]:
        events.insert(0, {"kind": "context", "index": 0})
    for event_index, event in enumerate(events):
        if event["kind"] != "context":
            continue
        end = events[event_index + 1]["index"] if event_index + 1 < len(events) else len(stream)
        text = "\n".join(line["text"] for line in stream[event["index"]:end])
        singleton = re.search(r"(?:directions?)\s*\(\s*Q?\s*(\d{1,3})\s*\)", text[:160], re.I)
        if singleton and not RANGE.search(text[:160]) and re.search(r"(?m)^A[.)]\s", text):
            event.update(kind="question", number=int(singleton.group(1)))
    segments = []
    active_context = []
    active_range = None
    for event_index, event in enumerate(events):
        end = events[event_index + 1]["index"] if event_index + 1 < len(events) else len(stream)
        lines = stream[event["index"]:end]
        text = "\n".join(line["text"] for line in lines)
        start = lines[0]
        stop = stream[end] if end < len(stream) else None
        clips = []
        for page_number in pages:
            if page_number < start["page"] or stop and page_number > stop["page"]:
                continue
            top = start["rect"].y0 - 3 if page_number == start["page"] else bounds[page_number][0] - 3
            bottom = stop["rect"].y0 - 3 if stop and page_number == stop["page"] else bounds[page_number][1]
            if bottom - top > 4:
                clips.append((page_number, top, bottom))
            if stop and page_number == stop["page"]:
                break
        segment = {"kind": event["kind"], "text": text, "clips": clips}
        if event["kind"] == "context":
            match = RANGE.search(text[:180])
            if match:
                active_range = (int(match.group(1)), int(match.group(2)))
                active_context = [segment]
            else:
                active_context = [segment]
                active_range = None
        else:
            number = event["number"]
            if subject == "Reasoning" and re.search(
                r"pairs of letters|word.*(?:consonants|vowels|english alphabet)|letters.*word",
                text, re.I | re.S
            ):
                active_context = []
                active_range = None
            if active_range and not active_range[0] <= number <= active_range[1] and not (
                subject == "English" and "passage" in context_text_for(active_context).lower()
                and re.search(r"passage|meaning|synonym|antonym", text, re.I)
            ) and not (
                subject == "Reasoning" and any(
                    re.search(pattern, text, re.I) and re.search(
                        pattern, context_text_for(active_context), re.I
                    ) for pattern in (
                        r"parcel", r"\bsit(?:ting|s)?\b", r"floor", r"boxes?", r"born",
                        r"\bages?\b", r"\blikes?\b", r"\blives?\b", r"collected"
                    )
                )
            ):
                active_context = []
                active_range = None
            context_text = "\n".join(item["text"] for item in active_context)
            chapter, topic = topic_for(subject, context_text + "\n" + text, bool(active_context))
            segment.update(number=number, contexts=list(active_context), chapter=chapter, topic=topic)
            segments.append(segment)
    return segments


def context_text_for(contexts):
    return "\n".join(context["text"] for context in contexts)


def build(ocr_directory):
    OUTPUT.mkdir(exist_ok=True)
    asset_directory = OUTPUT / "phase1_question_assets"
    asset_directory.mkdir(exist_ok=True)
    connection = sqlite3.connect(ROOT / "PYP" / "analysis" / "questions.sqlite")
    connection.row_factory = sqlite3.Row
    indexed = list(connection.execute(
        """SELECT q.*,d.filename FROM questions q JOIN documents d USING(document_id)
           WHERE phase='Phase 1' AND subject IN (?,?,?)
           ORDER BY year,subject,pdf_page_start,CAST(original_question_number AS INTEGER)""",
        SUBJECTS,
    ))
    sections = defaultdict(list)
    for row in indexed:
        sections[(row["filename"], row["year"], row["subject"])].append(row)
    records, audit = [], []
    for (filename, year, subject), rows in sections.items():
        document = pymupdf.open(ROOT / "PYP" / filename)
        if year == 2019:
            lower, upper = {"Reasoning": (5, 24), "Quantitative Aptitude": (26, 34),
                            "English": (36, 45)}[subject]
        else:
            lower = min(row["pdf_page_start"] for row in rows)
            upper = max(row["pdf_page_end"] for row in rows)
            allowed = next((range(lo, hi + 1) for lo, hi, name in
                            PHASE_ONE_RANGES[str(year)] if name == subject))
            while lower > 1:
                previous_text = document[lower - 2].get_text()
                previous_directions = [int(match.group(1)) for match in re.finditer(
                    r"Directions?\s*[:(]*\s*Q?\s*(\d{1,3})", previous_text, re.I)]
                if (not re.search(r"Phase\s*1", previous_text[:250], re.I)
                        or re.search(r"(?m)^\s*Q\s*[.:]?\s*\d", previous_text)
                        or re.search(r"answer\s*key", previous_text[:700], re.I)
                        or any(number not in allowed for number in previous_directions)):
                    break
                lower -= 1
            while upper < len(document):
                next_text = document[upper].get_text()
                if re.search(r"answer\s*key", next_text[:700], re.I):
                    break
                numbers = [int(match.group(1)) for match in
                           re.finditer(r"(?m)^\s*Q\s*[.:]?\s*(\d{1,3})[.)]", next_text)]
                numbers.extend(int(match.group(1)) for match in re.finditer(
                    r"(?im)^\s*Directions?\s*\(\s*Q?\s*(\d{1,3})\s*\)", next_text))
                if not numbers or any(number not in allowed for number in numbers):
                    break
                upper += 1
        segments = extract_section(document, year, subject, list(range(lower, upper + 1)),
                                   ocr_directory if year == 2019 else None)
        cached_contexts = {}
        for ordinal, segment in enumerate(segments, 1):
            prefix = f"{year}-{subject.split()[0].lower()}-{ordinal:03d}"

            def render(clips, name):
                files = []
                for part, (page_number, top, bottom) in enumerate(clips, 1):
                    page = document[page_number - 1]
                    clip = pymupdf.Rect(28, max(0, top), page.rect.width - 28,
                                       min(page.rect.height - 25, bottom))
                    path = asset_directory / f"{name}-{part:02d}.png"
                    page.get_pixmap(matrix=pymupdf.Matrix(1.65, 1.65), clip=clip).save(path)
                    files.append(f"phase1_question_assets/{path.name}")
                return files

            contexts = []
            for context in segment["contexts"]:
                key = tuple(context["clips"])
                if key not in cached_contexts:
                    cached_contexts[key] = render(context["clips"], prefix + "-context")
                contexts.extend(cached_contexts[key])
            records.append({
                "id": prefix, "year": year, "subject": subject,
                "chapter": segment["chapter"], "topic": segment["topic"],
                "original_number": segment["number"], "source": filename,
                "pages": [clip[0] for clip in segment["clips"]],
                "images": render(segment["clips"], prefix), "contexts": contexts,
                "search_text": segment["text"] + "\n" + "\n".join(c["text"] for c in segment["contexts"]),
                "ocr": year == 2019,
            })
        observed = Counter(segment["number"] for segment in segments)
        expected = Counter(int(row["original_question_number"]) for row in rows)
        audit.append({
            "year": year, "subject": subject, "indexed_count": len(rows),
            "extracted_count": len(segments),
            "indexed_markers_not_recovered": list((expected - observed).elements()),
            "additional_markers_recovered": list((observed - expected).elements()),
            "duplicate_numbers": [number for number, count in observed.items() if count > 1],
            "missing_numbers": sorted(set(
                range(1, 61) if year == 2019 and subject == "Reasoning"
                else range(61, 91) if year == 2019 and subject == "Quantitative Aptitude"
                else range(91, 121) if year == 2019
                else next(range(lo, hi + 1) for lo, hi, name in PHASE_ONE_RANGES[str(year)]
                          if name == subject)
            ) - set(observed)),
        })
        document.close()
        print(f"{year} {subject}: {len(segments)} questions; {len(cached_contexts)} shared sets")
    connection.close()
    unrecovered = [row for row in audit if row["indexed_markers_not_recovered"]]
    if unrecovered:
        raise ValueError(f"Previously indexed questions were not recovered: {unrecovered}")
    paths = {path for record in records for path in record["images"] + record["contexts"]}
    if any(not (OUTPUT / path).is_file() for path in paths):
        raise FileNotFoundError("A question or shared-context excerpt is missing.")
    (OUTPUT / "phase1_question_bank.json").write_text(
        json.dumps({"questions": records, "audit": audit}, ensure_ascii=False), encoding="utf-8")
    (OUTPUT / "phase1_question_bank.html").write_text(build_html(records, audit), encoding="utf-8")
    print(f"Wrote {len(records)} question records and question-only excerpts")


def build_html(records, audit):
    data = json.dumps(records, ensure_ascii=False).replace("<", "\\u003c")
    rows = "".join(
        f"<tr><td>{row['year']}</td><td>{html.escape(row['subject'])}</td>"
        f"<td>{row['extracted_count']}</td><td>{html.escape(str(row['missing_numbers']))}</td>"
        f"<td>{html.escape(str(row['duplicate_numbers']))}</td></tr>"
        for row in audit
    )
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Phase I PYQ Question Bank | RBI Grade B</title>
<style>
*{box-sizing:border-box}body{margin:0;font:16px/1.6 "Segoe UI",sans-serif;background:#f2f6f7;color:#183345}
main{max-width:1200px;margin:auto;padding:22px}header{background:#12394b;color:white;padding:25px;border-radius:14px}h1{margin:0;font-size:30px}header a{color:#c9f2eb}a{color:#087568}
.controls{position:sticky;top:0;z-index:2;background:#f2f6f7;display:flex;flex-wrap:wrap;gap:8px;padding:14px 0}
input,select,button{font:inherit;padding:9px;border:1px solid #cddce2;border-radius:7px;background:white;max-width:100%}input{flex:1;min-width:150px}select{min-width:0;width:230px}
.warning{background:#fff2d9;padding:15px;border-radius:9px;font-size:14px;margin:15px 0}.question{background:white;border:1px solid #d9e4e8;border-radius:12px;padding:15px;margin:16px 0}
.question h3{margin:0}.meta{font-size:13px;color:#526b79}.question img{display:block;width:auto;max-width:100%;height:auto;margin:12px auto;background:white}.question pre{white-space:pre-wrap;overflow-wrap:anywhere;font:16px/1.7 "Segoe UI",sans-serif}.excerpt{display:block}
details{padding:10px;background:#f5f9f9;border-radius:8px;margin:12px 0}summary{cursor:pointer;font-weight:650}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;border-bottom:1px solid #d9e4e8;padding:7px}
.pager{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.table-wrap{overflow:auto}button{cursor:pointer}button:disabled{cursor:default;opacity:.5}
@media(max-width:600px){main{padding:10px}header{padding:16px}.controls{position:static}.controls>*{flex:1 1 140px}.question{padding:9px}h1{font-size:24px}}
</style></head><body><main>
<header><h1>Phase I: topic-wise previous-year questions</h1><p>Quantitative Aptitude · Reasoning · English — 2019 and 2021–2026 supplied papers. Questions and options only, without answers or solutions.</p>
<a href="rbi_grade_b_report.html">Back to study report</a></header>
<p>Topic-wise PDFs:
<a href="phase1_english_topicwise.pdf" target="_blank" rel="noopener">English</a> ·
<a href="phase1_quants_topicwise.pdf" target="_blank" rel="noopener">Quantitative Aptitude</a> ·
<a href="phase1_reasoning_topicwise.pdf" target="_blank" rel="noopener">Reasoning</a>
</p>
<div class="warning">Source excerpts preserve the original DI charts, tables, passages and puzzle constraints. Shared instructions open automatically before each question. No missing questions are invented. The 2019 scan uses OCR for navigation, while the displayed questions are original images. Topic tags are navigation aids and may need source review. In 2025 Reasoning, the question under Directions (125) is printed as Q155; both printed Q155 questions are retained separately. The unnumbered question under Directions (170) is included as 170. Options are part of the questions, not answer keys.</div>
<p class="meta">Source limitation: 2021 English Q180 refers to two columns that are not reproduced in the supplied question page; its available instructions and options are retained without inventing the missing sentences.</p>
<details><summary>Coverage and extraction audit</summary><div class="table-wrap"><table><thead><tr><th>Year</th><th>Subject</th><th>Questions extracted</th><th>Missing printed numbers</th><th>Duplicate printed numbers</th></tr></thead><tbody>""" + rows + """</tbody></table></div></details>
<div class="controls"><select id="subject" aria-label="Subject"></select><select id="chapter" aria-label="Chapter"><option value="">All chapters</option></select><select id="topic" aria-label="Topic"><option value="">All topics</option></select><select id="year" aria-label="Year"><option value="">All years</option></select><input id="search" type="search" aria-label="Search question text" placeholder="Search questions or set instructions"><button id="reset">Reset</button></div>
<p id="count" aria-live="polite"></p><div class="pager"><button id="previous">Previous</button><span id="page-number"></span><button id="next">Next</button></div><div id="questions"></div>
<script>
const questions=""" + data + """;
const subjects=["Quantitative Aptitude","Reasoning","English"],$=s=>document.querySelector(s);
let page=0;const pageSize=15;
function option(select,value,label=value){const o=document.createElement("option");o.value=value;o.textContent=label;select.append(o)}
subjects.forEach(s=>option($("#subject"),s));
[...new Set(questions.map(q=>q.year))].sort().forEach(y=>option($("#year"),String(y)));
function choices(){
 const s=$("#subject").value,c=$("#chapter").value;
 $("#chapter").replaceChildren();option($("#chapter"),"","All chapters");
 [...new Set(questions.filter(q=>q.subject===s).map(q=>q.chapter))].sort().forEach(v=>option($("#chapter"),v));
 if([...$("#chapter").options].some(o=>o.value===c))$("#chapter").value=c;
 topics();
}
function topics(){
 const t=$("#topic").value;$("#topic").replaceChildren();option($("#topic"),"","All topics");
 [...new Set(questions.filter(q=>q.subject===$("#subject").value&&(!$("#chapter").value||q.chapter===$("#chapter").value)).map(q=>q.topic))].sort().forEach(v=>option($("#topic"),v));
 if([...$("#topic").options].some(o=>o.value===t))$("#topic").value=t;
}
function render(){
 const query=$("#search").value.toLowerCase().trim(),subject=$("#subject").value;
 const subjectQuestions=questions.filter(q=>q.subject===subject);
 const numbering=new Map(subjectQuestions.map((q,i)=>[q.id,i+1]));
 const filtered=subjectQuestions.filter(q=>(!$("#chapter").value||q.chapter===$("#chapter").value)&&(!$("#topic").value||q.topic===$("#topic").value)&&(!$("#year").value||String(q.year)===$("#year").value)&&(!query||q.search_text.toLowerCase().includes(query)));
 const pages=Math.max(1,Math.ceil(filtered.length/pageSize));page=Math.min(page,pages-1);
 $("#count").textContent=`${filtered.length} matching questions · ${subjectQuestions.length} available in ${subject}`;
 $("#page-number").textContent=`Page ${page+1} of ${pages}`;$("#previous").disabled=page===0;$("#next").disabled=page>=pages-1;
 const container=$("#questions");container.replaceChildren();
 function images(parent,paths){paths.forEach(path=>{const link=document.createElement("a");link.className="excerpt";link.href=path;link.target="_blank";link.rel="noopener";link.title="Open full-size question excerpt";const img=document.createElement("img");img.src=path;img.loading="lazy";img.alt="Original question-only source excerpt; open for full size";link.append(img);parent.append(link)})}
 filtered.slice(page*pageSize,(page+1)*pageSize).forEach(q=>{
  const card=document.createElement("article");card.className="question";card.dataset.questionId=q.id;
  const h=document.createElement("h3");h.textContent=`${numbering.get(q.id)}. ${q.topic}`;card.append(h);
  const m=document.createElement("div");m.className="meta";m.textContent=`${q.year} · Original Q${q.original_number} · ${q.chapter}${q.ocr?" · OCR navigation; verify image":""}`;card.append(m);
  const source=document.createElement("a");source.href="../PYP/"+encodeURIComponent(q.source)+"#page="+q.pages[0];source.target="_blank";source.rel="noopener";source.textContent="Original source page "+q.pages.join(", ");card.append(source);
  if(q.contexts.length){const d=document.createElement("details");d.open=true;const s=document.createElement("summary");s.textContent="Shared set instructions / passage / DI data";d.append(s);images(d,q.contexts);card.append(d)}
  images(card,q.images);
  const textView=document.createElement("details"),textSummary=document.createElement("summary");
  textSummary.textContent=q.ocr?"Readable OCR text — verify against original image":"Readable / copyable text — verify mathematical notation against image";
  const text=document.createElement("pre");text.textContent=q.search_text;textView.append(textSummary,text);card.append(textView);
  container.append(card);
 });
}
$("#subject").addEventListener("change",()=>{page=0;$("#chapter").value="";$("#topic").value="";choices();render()});
$("#chapter").addEventListener("change",()=>{page=0;topics();render()});
["topic","year","search"].forEach(id=>$("#"+id).addEventListener(id==="search"?"input":"change",()=>{page=0;render()}));
$("#previous").addEventListener("click",()=>{page--;render()});$("#next").addEventListener("click",()=>{page++;render()});
$("#reset").addEventListener("click",()=>{$("#chapter").value="";$("#topic").value="";$("#year").value="";$("#search").value="";page=0;choices();render()});
choices();render();
</script></main></body></html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr-directory", type=Path, required=True)
    build(parser.parse_args().ocr_directory)
