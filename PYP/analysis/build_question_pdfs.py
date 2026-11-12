"""Export topic-wise question PDFs with subject-specific study analysis."""

import json
from collections import defaultdict
from pathlib import Path

import pymupdf


OUTPUT = Path(__file__).resolve().parents[2] / "pyp_analysis"
SUBJECT_FILES = {
    "English": "phase1_english_topicwise.pdf",
    "Quantitative Aptitude": "phase1_quants_topicwise.pdf",
    "Reasoning": "phase1_reasoning_topicwise.pdf",
}
WIDTH, HEIGHT = 595, 842
MARGIN, BOTTOM = 42, 798
INK = (0.08, 0.20, 0.27)

STUDY_ANALYSIS = {
    "Quantitative Aptitude": [
        ("The recurring pattern", [
            "DI is central: the reviewed papers contain 19 DI sets across the seven supplied years. "
            "The repeated engine is percentage, ratio, average, difference and missing-value reconstruction. "
            "A different chart does not necessarily mean a different mathematical skill.",
            "Study order: fractions and percentages -> ratio and proportion -> averages and weighted "
            "averages -> successive changes -> linear equations -> profit, discount and revenue. "
            "These skills support both DI and standalone arithmetic.",
        ]),
        ("Exact DI patterns to practise", [
            "Total plus category ratio: split totals into groups, then combine selected categories. "
            "Example: 2026 Q118-122, balls and racquets.",
            "Missing table plus revenue: reconstruct counts using count and selling-price equations. "
            "Example: 2022 Q88-92, blue and red pens.",
            "Pie chart plus supplementary table: convert shares into quantities and connect a second "
            "dataset. Example: 2023 Q96-100, school medals.",
            "Paragraph/caselet to table: translate linked constraints into a numerical grid. "
            "Examples: 2019 Q61-66, colleges; 2025 Q107-110, flats and rent.",
            "Changed quantities: defective or returned items, revised percentages, ratios and revenue. "
            "Examples: 2026 Q113-116 and Q118-122.",
            "Overlapping groups: inclusion-exclusion and Venn diagrams. Example: 2023 Q86-90, sports.",
            "Build a clean base table, but derive only the entries needed. Do not calculate every "
            "missing value simply because it exists.",
        ]),
        ("Standalone arithmetic and short formats", [
            "Next cover standard income-expenditure-savings, profit-loss-discount, SI/CI, "
            "time-work-efficiency, speed-distance, trains, boats, ages, partnership, mixtures and basic "
            "mensuration. Practise converting words into equations before collecting shortcuts.",
            "Then practise quadratic factorisation and root comparison; missing/wrong series using "
            "differences, alternating terms, multiplication with adjustments and squares/cubes; "
            "approximation; data sufficiency and quantity comparison using the same arithmetic.",
            "Do not assume series or algebra will be elementary. The supplied papers include linked "
            "series and multi-equation questions. Approximation is an opportunity, not a guaranteed allocation.",
        ]),
        ("What to deprioritise", [
            "Deprioritise endless exotic series patterns, advanced geometry beyond the supplied level, "
            "long algebraic chains before standard arithmetic, and separate tricks courses for every chart type. "
            "This is prioritisation, not a claim that omitted topics cannot appear.",
        ]),
        ("Time traps and the 60% route", [
            "A small missing-data table may be harder than a large graph. Quantity comparison may "
            "require two full word problems for one mark. A series requiring repeated speculative "
            "rules is not a speed question.",
            "Illustrative route: 10 DI + 6 arithmetic + 4 short-format questions correct = 20 correct. "
            "With four wrong answers, net score is 19/30 under quarter-mark negative marking. "
            "Adapt the route: the supplied 2021 paper has only seven DI questions.",
        ]),
        ("Practice sequence", [
            "First learn the arithmetic engine. Then work through all 19 supplied DI sets, moving "
            "from direct data to missing-data and mixed sets. Repair standalone weaknesses alongside them.",
            "Finally use fresh timed sectionals. Track accuracy and time separately for DI, arithmetic "
            "and short formats. A remembered PYQ answer is not evidence of transfer.",
        ]),
    ],
    "Reasoning": [
        ("The recurring pattern", [
            "Seating, ordering and assignment sets, including ranking, account for roughly 26-31 "
            "questions per supplied paper. Input-output has exactly five questions in each of the "
            "seven papers: 35 questions in total. Frequent does not automatically mean fast.",
            "Critical reasoning also recurs: assumptions, inference, arguments, courses of action "
            "and strengthen/weaken questions deserve regular practice. Standalone-only selection "
            "is unlikely to provide a reliable route to 36/60.",
        ]),
        ("Five puzzle templates and what they are mixed with", [
            "Linear and parallel rows + facing directions, countries, chocolates or distances: "
            "separate position, facing and attributes. Examples: 2021 Q123-127; 2025 Q129-132.",
            "Circular and square seating + ages, relationships, brands or inward/outward facing: "
            "fix a reference position and apply relative left/right consistently. Example: "
            "2021 Q149-153, circular seating with ages.",
            "Floors/flats + employers, fruits or adjacent buildings: draw the grid first; distinguish "
            "above/below from same-floor relations. Example: 2022 Q114-118.",
            "Dates/months/birth years + ages, cities or experience: create chronological slots and "
            "keep arithmetic separate from placement. Example: 2023 Q113-117.",
            "Boxes/designations/distribution + colours, objects, quantities or group-size limits: "
            "use an ordered grid or assignment matrix. Examples: 2023 Q120-124, boxes; "
            "2025 Q141-146, cities and objects.",
            "Learn the ordinary version first, then add one attribute. Do not begin with "
            "uncertain-person-count, multi-attribute puzzles.",
        ]),
        ("Input-output: prepare all seven sets", [
            "Identify what changes at each step, whether words and numbers follow separate rules, "
            "selection order versus numerical transformation, and which positions become fixed.",
            "Validate the candidate rule against another demonstrated step before tracing the new "
            "input. One incorrect rule can affect all five answers.",
        ]),
        ("Build the standalone scoring base", [
            "Study inequalities including coded relationships; syllogisms including reverse selection "
            "of statements; directions using coordinates; letter/digit operations; and data sufficiency.",
            "For critical reasoning, identify claim -> evidence -> missing link. Distinguish "
            "assumption from inference, strength from relevance, and cause from correlation. "
            "Do not answer from personal opinion or outside facts.",
            "In data sufficiency, test whether the requested answer is unique. You need not always "
            "solve the complete arrangement.",
        ]),
        ("What to deprioritise and when to leave", [
            "Deprioritise rare coding systems before recurring formats, exhaustive puzzle variants "
            "and memorised critical-reasoning answers. Do not treat every puzzle as compulsory.",
            "Warning signs: uncertain person count plus several attributes; repeated case creation "
            "without elimination; no stable deductions; continuing only because time has already been spent.",
        ]),
        ("The 60% route and practice sequence", [
            "Illustrative route: 20 correct from selected sets + 4 input-output + 6 direct questions "
            "+ 8 critical-reasoning/data-sufficiency questions = 38 correct. With six wrong, "
            "net score is 36.5/60 under quarter-mark negative marking. These groups must not overlap.",
            "Learn direct basics and the five templates, then add mixed attributes. Complete all "
            "seven input-output sets and select puzzles covering every template. Finish with fresh "
            "timed sectionals that test both set selection and standalone accuracy.",
        ]),
    ],
    "English": [
        ("The recurring pattern", [
            "Prepare four transferable skills rather than memorising dozens of formats: passage "
            "comprehension, sentence grammar, contextual word choice and logical cohesion.",
            "RC, including passage-based vocabulary, accounts for 59 of the 210 supplied questions "
            "(6-15 per paper). Grammar and vocabulary also appear through swaps, fillers, "
            "replacement, matching and usage questions.",
        ]),
        ("Skill 1: passage comprehension", [
            "Practise stated facts, inference, theme, tone, true/false and contextual vocabulary. "
            "Locate textual evidence and distinguish what is stated from what is merely plausible.",
            "Examples: 2024 Q171-178, inference-heavy RC; 2025 Q171-178, theme, tone, imagery "
            "and contextual vocabulary. Read the actual passage even when its topic is familiar.",
        ]),
        ("Skill 2: sentence grammar", [
            "Study subject-verb agreement, tense, pronouns, modifiers, parallelism, articles and "
            "prepositions. Apply each rule to error detection, phrase improvement and correct-sentence "
            "selection rather than learning terminology alone.",
            "Example: 2023 Q182-196, phrase improvement and error detection. For every error, "
            "explain the violated rule and rewrite only the affected part.",
        ]),
        ("Skill 3: contextual word choice", [
            "Practise fillers, cloze, word swaps, usage and idioms. Check meaning, grammatical role "
            "and collocation together. A dictionary synonym may not fit the sentence.",
            "Examples: 2019 Q104-109 and 2025 Q179-184, contextual cloze/replacement. "
            "Keep short vocabulary notes: word/phrase -> meaning here -> common usage -> your confusion.",
        ]),
        ("Skill 4: logical cohesion", [
            "Practise sentence and paragraph order, column matching, connectors and odd sentences. "
            "Use pronoun references, mandatory pairs, contrast, cause-effect and chronology.",
            "Examples: 2024 Q179-181, Q189-190 and Q198-200. Look for an elimination-enabling "
            "pair before reconstructing every possible sequence.",
        ]),
        ("What to deprioritise", [
            "Deprioritise huge isolated synonym lists, rare idioms without context, grammar terminology "
            "you cannot apply, and editorial reading without retrieval or question practice. "
            "Reading should feed comprehension practice and a small error-based vocabulary list.",
        ]),
        ("Time traps and the 60% route", [
            "Avoid outside knowledge in RC, dictionary-only word matching and missing NOT/EXCEPT/"
            "incorrect. Do not spend two minutes debating one ambiguous word.",
            "For ambiguity, reread the deciding evidence once, then answer or leave. In ordering "
            "questions, use mandatory pairs to eliminate options when possible.",
            "Illustrative route: 6 RC + 7 grammar/context + 7 cohesion/vocabulary correct = "
            "20 correct. Count each question once. With four wrong, net score is 19/30 under "
            "quarter-mark negative marking. Adapt to the paper's actual format mix.",
        ]),
        ("Practice sequence", [
            "Practise RC evidence and contextual grammar daily. Complete all supplied RC passages, "
            "then use remaining questions to repair specific weaknesses across the four skills.",
            "Test transfer using fresh timed sectionals. Review both wrong answers and answers "
            "that were correct only by guessing.",
        ]),
    ],
}


def add_study_analysis(subject, path):
    """Prepend guidance without reflowing or renumbering existing question pages."""
    guide = Book(subject)
    guide.new_page()
    guide.bookmarks.append([1, "Study analysis and 60% strategy", 1])
    guide.text(f"{subject}: study analysis", 21, True)
    guide.text("Patterns, priorities, practice and time-trap control", 12, True)
    guide.text(
        "Based on the seven supplied memory-based papers: 2019 and 2021-2026. "
        "These are historical patterns, not a prediction or a guarantee of 60%. "
        "Automatic topic labels are navigation aids; this analysis uses actual question/set "
        "instructions. Difficulty and personal speed must be tested in mocks.", 10
    )
    guide.text(
        "Examples below use the original year and question number, not the running Question "
        "number in this booklet. The question section remains question-only: no answers or solutions.",
        10
    )
    for heading, paragraphs in STUDY_ANALYSIS[subject]:
        if guide.y + 90 > BOTTOM:
            guide.new_page()
        guide.bookmarks.append([2, heading, len(guide.document)])
        guide.text(heading, 13, True)
        for paragraph in paragraphs:
            guide.text(paragraph, 10)
    guide.text("Scoring and mock-calibrated skip rules", 13, True)
    guide.text(
        "With one-mark questions and a quarter-mark penalty: net = correct - 0.25 x wrong. "
        "The 60% targets are 18/30 for Quant/English and 36/60 for Reasoning. "
        "Confirm marking and sectional timings in the applicable official notification. "
        "Attempting 60% of questions is not scoring 60%.", 10
    )
    guide.text(
        "Initial thresholds to calibrate, not rigid laws: park a standalone if no credible method "
        "emerges in 20-30 seconds; park a series if standard checks show no rule in about "
        "30-40 seconds. For a DI/puzzle set, review progress after 60-90 seconds. Leave if there "
        "is no useful table, placement or deduction. Continue a productive set while it yields "
        "answers; review the time investment around 4-6 minutes.", 10
    )
    guide.text(
        "Choose by likely correct marks per minute, not the topic name or apparent length. "
        "Record: pattern | correct/wrong | time | mistake | earlier skip signal. "
        "Exceed the target in at least three consecutive fresh timed sectionals before trusting "
        "the strategy. This is a readiness checkpoint, not a guarantee.", 10
    )
    guide.text(
        "Pagination: analysis pages use A-prefix numbers. The original question pages retain "
        "their printed numbers and layout. Shared-data references refer to those printed "
        "question-section numbers, not the PDF viewer's physical page count. Use bookmarks to jump.",
        10
    )
    prefix_count = len(guide.document)
    for index, page in enumerate(guide.document):
        page.add_redact_annot(pymupdf.Rect(WIDTH - 90, HEIGHT - 34, WIDTH, HEIGHT))
        page.apply_redactions()
        page.insert_text((WIDTH - 85, HEIGHT - 20), f"A{index + 1}", fontsize=9, color=INK)
    with pymupdf.open(path) as original:
        original_count = len(original)
        original_text = [page.get_text() for page in original]
        toc = original.get_toc()
        metadata = original.metadata
        guide.document.insert_pdf(original)
    guide.document.set_toc(guide.bookmarks + [
        [1, "Topic-wise question bank (original printed pages)", prefix_count + 1]
    ] + [[level + 1, title, page + prefix_count] for level, title, page in toc])
    metadata["subject"] = "Subject study analysis and question-only practice"
    guide.document.set_metadata(metadata)
    try:
        with pymupdf.open(stream=guide.document.tobytes(deflate=True, garbage=4),
                          filetype="pdf") as verified:
            if len(verified) != prefix_count + original_count:
                raise ValueError(f"{path}: page count changed unexpectedly")
            for index, text in enumerate(original_text):
                if verified[index + prefix_count].get_text() != text:
                    raise ValueError(f"{path}: question page {index + 1} changed")
            verified.save(path, deflate=True, garbage=4)
    finally:
        guide.document.close()
    return prefix_count

def compact_bands(pixmap):
    """Remove only near-white horizontal bands; retain all darker image rows."""
    gray = pymupdf.Pixmap(pymupdf.csGRAY, pixmap)
    samples = gray.samples
    occupied = [min(samples[y * gray.stride:y * gray.stride + gray.width]) < 245
                for y in range(gray.height)]
    rows = [y for y, present in enumerate(occupied) if present]
    if not rows:
        return [(0, gray.height)]
    start, end = max(0, rows[0] - 5), min(gray.height, rows[-1] + 6)
    bands, beginning = [], start
    previous = rows[0]
    for row in rows[1:]:
        if row - previous > 48:
            bands.append((beginning, previous + 6))
            beginning = row - 5
        previous = row
    bands.append((beginning, end))
    for y in rows:
        if not any(top <= y < bottom for top, bottom in bands):
            raise ValueError("Whitespace compaction would remove a content row")
    return bands


class Book:
    def __init__(self, subject, phase="Phase I"):
        self.document = pymupdf.open()
        self.subject = subject
        self.phase = phase
        self.page = None
        self.y = MARGIN
        self.bookmarks = []
        self.question_ids = []
        self.image_count = 0
        self.removed_image_rows = 0
        self.excerpt_sources = {}

    def new_page(self):
        self.page = self.document.new_page(width=WIDTH, height=HEIGHT)
        self.page.insert_text((MARGIN, 22), f"RBI Grade B | {self.phase} | {self.subject}",
                              fontsize=9, color=INK)
        self.page.insert_text((WIDTH - 85, HEIGHT - 20),
                              str(len(self.document)), fontsize=9, color=INK)
        self.y = MARGIN

    def text(self, value, size=11, bold=False):
        font = "hebo" if bold else "helv"
        lines = []
        for paragraph in value.splitlines():
            line = ""
            for word in paragraph.split():
                candidate = f"{line} {word}".strip()
                if line and pymupdf.get_text_length(candidate, fontname=font, fontsize=size) > WIDTH - 2 * MARGIN:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        needed = len(lines) * (size + 3) + 3
        if self.page is None or self.y + needed > BOTTOM:
            self.new_page()
        for line in lines:
            self.page.insert_text((MARGIN, self.y + size), line,
                                  fontname=font, fontsize=size, color=INK)
            self.y += size + 3
        self.y += 3

    def image(self, relative_path):
        path = OUTPUT / relative_path
        if not path.is_file():
            raise FileNotFoundError(path)
        if relative_path not in self.excerpt_sources:
            pixmap = pymupdf.Pixmap(str(path))
            bands = compact_bands(pixmap)
            source = pymupdf.open()
            source_page = source.new_page(width=pixmap.width, height=pixmap.height)
            source_page.insert_image(source_page.rect, filename=str(path))
            self.excerpt_sources[relative_path] = (source, bands)
            self.removed_image_rows += pixmap.height - sum(bottom - top for top, bottom in bands)
        source, bands = self.excerpt_sources[relative_path]
        available_width = WIDTH - 2 * MARGIN
        scale = available_width / source[0].rect.width
        for top, bottom in bands:
            while top < bottom:
                if self.page is None or BOTTOM - self.y < 45:
                    self.new_page()
                remaining = (BOTTOM - self.y) / scale
                stop = min(bottom, top + remaining)
                if stop < bottom:
                    # Split only at a whitespace row, never through text or a chart.
                    pixmap = pymupdf.Pixmap(str(path))
                    gray = pymupdf.Pixmap(pymupdf.csGRAY, pixmap)
                    samples = gray.samples
                    candidates = [
                        row for row in range(int(top + 30 / scale), int(stop))
                        if min(samples[row * gray.stride:row * gray.stride + gray.width]) >= 245
                    ]
                    if candidates:
                        stop = candidates[-1]
                    else:
                        self.new_page()
                        stop = min(bottom, top + (BOTTOM - self.y) / scale)
                        if stop < bottom:
                            raise ValueError(f"Unbroken source content exceeds a print page: {path}")
                height = (stop - top) * scale
                self.page.show_pdf_page(
                    pymupdf.Rect(MARGIN, self.y, WIDTH - MARGIN, self.y + height),
                    source, 0, clip=pymupdf.Rect(0, top, source[0].rect.width, stop),
                )
                self.y += height
                top = stop
            self.y += 3
        self.y += 3
        self.image_count += 1

    def export(self, questions, path):
        self.new_page()
        self.text(f"{self.subject}: topic-wise previous-year questions", 22, True)
        self.text(f"{len(questions)} numbered questions | 2019 and 2021-2026", 13)
        self.text("Questions and options only. No answer keys or solutions.", 12, True)
        self.text(
            "Grouped by chapter and topic, then source year and question order. "
            "Use the PDF bookmarks to jump to a topic. Shared instructions, reading passages, "
            "DI charts and tables appear before their questions. Later questions from the "
            "same set reference the shared-data PDF page. Excess near-white horizontal "
            "bands are trimmed without reducing the original excerpt text scale."
        )
        self.text(
            "The displayed excerpts are from the original supplied memory-based PDFs. "
            "Topic labels are navigation aids, not official syllabus classifications. "
            "Source wording and numbering anomalies are preserved; no questions or missing "
            "data have been invented."
        )
        if self.subject == "English":
            self.text(
                "Source limitation: 2021 Q180 refers to sentence columns absent from its "
                "supplied page. Available instructions and options are included."
            )
        if self.subject == "Reasoning":
            self.text(
                "Source numbering: the 2025 question under Directions (125) is printed Q155. "
                "Both printed Q155 questions are retained. The unnumbered question under "
                "Directions (170) is listed as 170."
            )
        groups = defaultdict(list)
        for question in questions:
            groups[(question["chapter"], question["topic"])].append(question)
        self.text("Topic index", 15, True)
        for (chapter, topic), members in sorted(groups.items()):
            self.text(f"{chapter} / {topic}: {len(members)} questions", 10)
        number, previous_chapter = 0, None
        shared_pages = {}
        for (chapter, topic), members in sorted(groups.items()):
            if self.y + 130 > BOTTOM:
                self.new_page()
            else:
                self.y += 12
            if chapter != previous_chapter:
                self.bookmarks.append([1, chapter, len(self.document)])
                previous_chapter = chapter
            self.bookmarks.append([2, topic, len(self.document)])
            self.text(chapter, 13, True)
            self.text(topic, 17, True)
            for question in sorted(members, key=lambda q: (q["year"], q["id"])):
                number += 1
                # Reserve space for the question label and its source metadata.
                if self.y + 65 > BOTTOM:
                    self.new_page()
                self.text(f"Question {number} | {question['year']} | Original Q{question['original_number']}",
                          11, True)
                self.text(
                    f"Source: {question['source']} | original PDF page(s): "
                    + ", ".join(str(page) for page in question["pages"]), 9
                )
                key = (chapter, topic, tuple(question["contexts"]))
                if question["contexts"]:
                    if key not in shared_pages:
                        if self.y + 50 > BOTTOM:
                            self.new_page()
                        shared_pages[key] = len(self.document)
                        self.text("Shared instructions / passage / DI data", 10, True)
                        for image in question["contexts"]:
                            self.image(image)
                    else:
                        self.text(f"Shared instructions / data: see this PDF page "
                                  f"{shared_pages[key]}.", 10, True)
                for image in question["images"]:
                    self.image(image)
                self.question_ids.append(question["id"])
        self.document.set_toc(self.bookmarks)
        self.document.set_metadata({
            "title": f"RBI Grade B Phase I - {self.subject} - Topic-wise PYQs",
            "subject": "Question-only practice; supplied 2019 and 2021-2026 papers",
            "creator": "Local question bank export",
        })
        self.document.save(path, deflate=True, garbage=4)
        self.document.close()
        for source, _ in self.excerpt_sources.values():
            source.close()
        with pymupdf.open(path) as saved:
            labels = sum(page.get_text().count("Question ") for page in saved)
            if labels != len(questions):
                raise ValueError(f"{path}: {labels} question labels; expected {len(questions)}")
            if not saved.get_toc():
                raise ValueError(f"{path}: topic bookmarks missing")
            result = {"filename": path.name, "questions": len(questions),
                      "pages": len(saved), "topics": len(groups),
                      "image_placements": self.image_count,
                      "whitespace_rows_removed": self.removed_image_rows}
        if len(set(self.question_ids)) != len(questions):
            raise ValueError(f"{path}: duplicated or missing question IDs")
        expected_images = sum(len(q["images"]) for q in questions)
        expected_images += sum(len(key[2]) for key in {
            (q["chapter"], q["topic"], tuple(q["contexts"])) for q in questions
        })
        if self.image_count != expected_images:
            raise ValueError(f"{path}: an original question or shared-data excerpt is missing")
        return result


def main():
    bank = json.loads((OUTPUT / "phase1_question_bank.json").read_text(encoding="utf-8"))
    results = []
    for subject, filename in SUBJECT_FILES.items():
        questions = [q for q in bank["questions"] if q["subject"] == subject]
        expected = 420 if subject == "Reasoning" else 210
        if len(questions) != expected:
            raise ValueError(f"{subject}: expected {expected} questions, found {len(questions)}")
        result = Book(subject).export(questions, OUTPUT / filename)
        analysis_pages = add_study_analysis(subject, OUTPUT / filename)
        result["pages"] += analysis_pages
        results.append(result)
        print(f"{filename}: {result['questions']} questions, {result['pages']} pages, "
              f"{result['topics']} topics")
    if sum(result["questions"] for result in results) != len(bank["questions"]):
        raise ValueError("Not every question was exported")


if __name__ == "__main__":
    main()
