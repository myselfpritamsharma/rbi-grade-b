import csv
import hashlib
import json
import re
import sqlite3
import tempfile
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DATABASE = OUT / "questions.sqlite"
SYLLABUS_NAME = "Latest-RBI-Grade-B-Syllabus-2025-Official-PDF.pdf"
QUESTION_START = re.compile(
    r"(?m)^[ \t]*Q[ \t]*[.:]?[ \t]*(\d{1,3})[ \t]*[.)](?=[ \t]|$)"
)
PHASE_ONE_RANGES = {
    "2021": [(1, 80, "General Awareness"), (81, 110, "Quantitative Aptitude"),
             (111, 170, "Reasoning"), (171, 200, "English")],
    "2022": [(1, 80, "General Awareness"), (81, 110, "Quantitative Aptitude"),
             (111, 170, "Reasoning"), (171, 200, "English")],
    "2023": [(1, 80, "General Awareness"), (81, 110, "Quantitative Aptitude"),
             (111, 170, "Reasoning"), (171, 200, "English")],
    "2024": [(1, 80, "General Awareness"), (81, 110, "Quantitative Aptitude"),
             (111, 170, "Reasoning"), (171, 200, "English")],
    "2025": [(1, 80, "General Awareness"), (81, 110, "Quantitative Aptitude"),
             (111, 170, "Reasoning"), (171, 200, "English")],
    "2026": [(1, 80, "General Awareness"), (81, 110, "English"),
             (111, 140, "Quantitative Aptitude"), (141, 200, "Reasoning")],
}
SECTION_NAMES = {
    "general awareness": ("General Awareness", "GA"),
    "quantitative aptitude": ("Quantitative Aptitude", "QA"),
    "reasoning": ("Reasoning", "RA"),
    "reasoning ability": ("Reasoning", "RA"),
    "english language": ("English", "EN"),
    "english": ("English", "EN"),
    "economic and social issues": ("Economic and Social Issues", "ESI"),
    "descriptive english": ("Descriptive English", "DE"),
    "finance and management": ("Finance and Management", "FM"),
    "finance": ("Finance and Management", "FM"),
    "management": ("Finance and Management", "FM"),
    "essay writing": ("Descriptive English", "DE"),
    "precis writing": ("Descriptive English", "DE"),
    "reading comprehension": ("Descriptive English", "DE"),
}
IGNORED_HEADINGS = {
    "objective", "descriptive", "essay writing", "precis writing",
    "reading comprehension", "question", "answer",
}


def clean_lines(text):
    cleaned = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.isdigit():
            continue
        if line.casefold().startswith("rbi grade b "):
            continue
        if line.casefold() in {key for key in SECTION_NAMES} | IGNORED_HEADINGS:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def read_page_heading(lines):
    for line in lines[:8]:
        key = re.sub(r"\s+", " ", line).strip().casefold()
        if key in SECTION_NAMES:
            return SECTION_NAMES[key]
    return None


def assigned_phase_one_subject(year, number, current):
    for lower, upper, subject in PHASE_ONE_RANGES.get(year, []):
        if lower <= number <= upper:
            return subject, "question-number range"
    return current, "section heading"


def question_rows_for_pdf(pdf_path):
    year = re.match(r"(20\d{2})", pdf_path.name).group(1)
    document_id = f"DOC-{year}"
    pdf = pymupdf.open(pdf_path)
    phase = None
    phase_subject = {}
    phase_subsection = {}
    last_phase_two_number = {}
    phase_two_descriptive_mode = set()
    page_rows = []
    question_rows = []

    for page_number, page in enumerate(pdf, start=1):
        raw_text = page.get_text("text")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        heading = " ".join(lines[:8])
        phase_match = re.search(r"\bPhase\s*[-:]?\s*(1|2)\b", heading, re.I)
        if phase_match:
            phase = f"Phase {phase_match.group(1)}"

        if re.search(r"answer\s+key", heading, re.I):
            continue
        if re.search(r"table of contents|^preface\b|^disclaimer\b|what next|about us",
                     heading, re.I):
            continue
        if not phase:
            continue

        heading_subject = read_page_heading(lines[2:])
        if heading_subject:
            subject_name, subject_code = heading_subject
            if subject_name not in {"Descriptive English"}:
                phase_subject[phase] = (subject_name, subject_code)
            elif phase == "Phase 2":
                phase_subject[phase] = (subject_name, subject_code)
        if phase == "Phase 2":
            normalized_lines = {re.sub(r"\s+", " ", line).strip().casefold()
                                for line in lines[2:8]}
            if "objective" in normalized_lines:
                phase_subsection[phase] = "Objective"
                if phase_subject.get(phase, ("", ""))[0] == "Descriptive English":
                    phase_subject[phase] = ("Economic and Social Issues", "ESI")
            elif "descriptive" in normalized_lines:
                phase_subsection[phase] = "Descriptive"

        section_info = phase_subject.get(phase)
        if section_info is None:
            section_info = ("Unclassified", "UN")

        body = clean_lines(raw_text)
        page_rows.append({
            "document_id": document_id,
            "pdf_page": page_number,
            "phase": phase,
            "section": section_info[0],
            "page_text": body,
        })

        body_matches = list(QUESTION_START.finditer(body))
        for index, match in enumerate(body_matches):
            end = body_matches[index + 1].start() if index + 1 < len(body_matches) else len(body)
            number = int(match.group(1))
            question_text = body[match.start():end].strip()
            if phase == "Phase 1":
                subject, classification_basis = assigned_phase_one_subject(
                    year, number, section_info[0]
                )
                subject_code = next(
                    (code for name, code in SECTION_NAMES.values() if name == subject),
                    "UN",
                )
            else:
                subject, subject_code = section_info
                classification_basis = "section heading"
            if phase == "Phase 2":
                reset_key = (subject, section_info[1])
                previous_number = last_phase_two_number.get(reset_key, 0)
                if previous_number >= 28 and number <= 6:
                    phase_two_descriptive_mode.add(reset_key)
                if phase_subsection.get(phase) == "Descriptive":
                    phase_two_descriptive_mode.add(reset_key)
                descriptive = (
                    subject == "Descriptive English"
                    or reset_key in phase_two_descriptive_mode
                )
                section = "Descriptive" if descriptive else "Objective"
                last_phase_two_number[reset_key] = number
            else:
                section = "Objective"
            if phase == "Phase 1" and subject == "English":
                section = "Objective"
            page_prefix = (
                clean_lines(body[:match.start()])
                if index == 0 and not QUESTION_START.search(body[:match.start()])
                else ""
            )
            has_encoding_uncertainty = "\ufffd" in question_text
            question_rows.append({
                "document_id": document_id,
                "year": int(year),
                "phase": phase,
                "subject": subject,
                "section": section,
                "original_question_number": str(number),
                "pdf_page_start": page_number,
                "pdf_page_end": page_number,
                "question_text": question_text,
                "shared_context": page_prefix,
                "classification_basis": classification_basis,
                "subject_code": subject_code,
                "manual_review_required": int(
                    subject == "Unclassified" or has_encoding_uncertainty
                ),
                "extraction_confidence": 0.75 if has_encoding_uncertainty else 0.98,
                "classification_confidence": (
                    0.96 if classification_basis == "section heading" else 0.82
                ),
            })

    pdf.close()
    return question_rows, page_rows


def question_rows_for_2019(pdf_path):
    ocr_directory = Path(tempfile.gettempdir()) / "RBI-GrB-2019-OCR" / "text"
    page_sections = [
        (5, 24, "Phase 1", "Reasoning", "RA"),
        (26, 34, "Phase 1", "Quantitative Aptitude", "QA"),
        (36, 45, "Phase 1", "English", "EN"),
        (47, 66, "Phase 1", "General Awareness", "GA"),
        (68, 70, "Phase 2", "Descriptive English", "DE"),
        (71, 93, "Phase 2", "Economic and Social Issues", "ESI"),
    ]
    pdf = pymupdf.open(pdf_path)
    question_rows = []
    page_rows = []
    for page_number, page in enumerate(pdf, start=1):
        source_text = page.get_text("text")
        is_ocr = len(source_text.strip()) <= 40
        if is_ocr:
            ocr_file = ocr_directory / f"page-{page_number:03d}.txt"
            if not ocr_file.exists():
                continue
            source_text = ocr_file.read_text(encoding="utf-8-sig")
        section_info = next(
            (row for row in page_sections if row[0] <= page_number <= row[1]),
            None,
        )
        if not section_info:
            continue
        _, _, phase, subject, subject_code = section_info
        body = clean_lines(source_text)
        matches = list(QUESTION_START.finditer(body))
        page_rows.append({
            "document_id": "DOC-2019",
            "pdf_page": page_number,
            "phase": phase,
            "section": subject,
            "page_text": body,
            "ocr_required": int(is_ocr),
        })
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            question_text = body[match.start():end].strip()
            number = int(match.group(1))
            descriptive = subject == "Descriptive English" or (
                phase == "Phase 2"
                and not re.search(r"(?m)^\s*(?:A[.)]|A\s*[.)])", question_text)
            )
            labels = topic_tags(phase, subject, question_text)
            question_rows.append({
                "document_id": "DOC-2019",
                "year": 2019,
                "phase": phase,
                "subject": subject,
                "section": "Descriptive" if descriptive else "Objective",
                "original_question_number": str(number),
                "pdf_page_start": page_number,
                "pdf_page_end": page_number,
                "question_summary": "; ".join(labels),
                "topic_labels": labels,
                "classification_basis": "2019 contents-page PDF page range",
                "subject_code": subject_code,
                "manual_review_required": 1 if is_ocr else 0,
                "extraction_confidence": 0.60 if is_ocr else 0.95,
                "classification_confidence": 0.88,
                "ocr_uncertainty": "OCR; verify source page" if is_ocr else None,
            })
    pdf.close()
    return question_rows, page_rows


def add_syllabus_record(connection):
    syllabus_path = ROOT / SYLLABUS_NAME
    digest = hashlib.sha256(syllabus_path.read_bytes()).hexdigest()
    pdf = pymupdf.open(syllabus_path)
    page_texts = [page.get_text("text").strip() for page in pdf]
    full_text = "\n\n".join(page_texts).strip()
    connection.execute(
        """INSERT OR REPLACE INTO documents
           (document_id,filename,year,phase_coverage,sections,page_count,document_type,
            text_layer,ocr_requirement,answer_key_status,shift_status,sha256,
            inventory_status,notes)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("DOC-SYLLABUS-2025", SYLLABUS_NAME, 2025,         "Official syllabus excerpt",
        "Phase II ESI, English writing skills and General Finance and Management",
         len(pdf), "Official RBI Grade B syllabus/notification excerpt",
         f"Searchable text on {sum(len(text) > 40 for text in page_texts)}/{len(pdf)} pages",
         "No general OCR indicated", "Not applicable", "Not applicable", digest,
         "Official syllabus supplied by user; established as classification baseline",
         "This file contains Phase II syllabus pages only; Phase I syllabus is not present. "
         "Use as the 2025 Phase II taxonomy baseline, not as a retroactive syllabus."),
    )
    for page_number, text in enumerate(page_texts, start=1):
        connection.execute(
            """INSERT OR REPLACE INTO page_audit
               (document_id,pdf_page,extracted_character_count,ocr_required,
                review_status,notes) VALUES(?,?,?,?,?,?)""",
            ("DOC-SYLLABUS-2025", page_number, len(text), int(len(text) <= 40),
             "syllabus_text_extracted", "Official 2025 syllabus page"),
        )
    pdf.close()
    return len(page_texts), full_text


def seed_syllabus_taxonomy(connection):
    taxonomy_rows = [
        ("2025-P2-ESI-001", "Phase 2", "ESI", "Growth and Development",
         "Measurement; poverty alleviation; employment generation; sustainable development; environmental issues"),
        ("2025-P2-ESI-002", "Phase 2", "ESI", "Indian Economy",
         "Economic history; industrial and labour policy; monetary and fiscal policy since 1991; Economic Survey and Union Budget; money and financial markets; banks and RBI in development; public finance; political economy; industrial developments; agriculture; services"),
        ("2025-P2-ESI-003", "Phase 2", "ESI", "Globalization",
         "Opening of the Indian economy; balance of payments; export-import policy; international economic institutions; IMF; World Bank; WTO; regional economic cooperation; international economic issues"),
        ("2025-P2-ESI-004", "Phase 2", "ESI", "Social Structure in India",
         "Multiculturalism; demographic trends; urbanisation and migration; gender issues; social justice"),
        ("2025-P2-FM-001", "Phase 2", "Finance", "Financial System",
         "Financial institutions; RBI; Indian banking system; SIDBI; EXIM Bank; NABARD; NHB; NaBFID; global financial-system developments; information technology in banking and finance; non-banking system; digital payments"),
        ("2025-P2-FM-002", "Phase 2", "Finance", "Financial Markets",
         "Primary and secondary markets; forex; money; bond and equity markets; functions; instruments; recent developments"),
        ("2025-P2-FM-003", "Phase 2", "Finance", "Financial Risk Management", "General topics"),
        ("2025-P2-FM-004", "Phase 2", "Finance", "Basics of Derivatives", "General topics"),
        ("2025-P2-FM-005", "Phase 2", "Finance", "Global Financial Markets and International Banking",
         "Broad trends and latest developments"),
        ("2025-P2-FM-006", "Phase 2", "Finance", "Financial Inclusion", "General topics"),
        ("2025-P2-FM-007", "Phase 2", "Finance", "Alternate Sources of Finance",
         "Private and social cost-benefit; public-private partnership"),
        ("2025-P2-FM-008", "Phase 2", "Finance", "Corporate Governance in Banking", "General topics"),
        ("2025-P2-FM-009", "Phase 2", "Finance", "Union Budget", "Concepts; approach; broad trends"),
        ("2025-P2-FM-010", "Phase 2", "Finance", "Accounting and Financial Statements",
         "Balance sheet; profit and loss; cash flow; ratio analysis"),
        ("2025-P2-FM-011", "Phase 2", "Finance", "Inflation",
         "Definition; trends; estimates; consequences; remedies; WPI; CPI; balance between inflation and growth through monetary and fiscal policies"),
        ("2025-P2-MGMT-001", "Phase 2", "Management",
         "Fundamentals of Management and Organizational Behaviour",
         "Management introduction and thought; management functions and roles; nudge theory; organizational behaviour; personality; reinforcement; perception; motivation; leadership; emotional intelligence; interpersonal relationships; conflict; organizational change and development"),
        ("2025-P2-MGMT-002", "Phase 2", "Management",
         "Ethics at the Workplace and Corporate Governance",
         "Ethical theories; business ethics; ethical principles; organization structure; board of directors; ethics programmes; codes of ethics and conduct; corporate governance factors and mechanisms"),
        ("2025-P2-MGMT-003", "Phase 2", "Management", "Communication",
         "Communication process and channels; oral and written; verbal and non-verbal; upward, downward and lateral; barriers; information technology"),
        ("2025-P2-ENG-001", "Phase 2", "English Writing Skills",
         "English writing skills", "Expression and understanding of the topic"),
    ]
    for taxonomy_id, phase, subject, topic, detail in taxonomy_rows:
        connection.execute(
            """INSERT OR IGNORE INTO taxonomy
               (taxonomy_id,version,phase,subject,topic,subtopic,official_heading,notes)
               VALUES(?,?,?,?,?,?,?,?)""",
            (taxonomy_id, "2025-official", phase, subject, topic, detail,
             topic, "Mapped from the user-supplied official 2025 RBI syllabus excerpt."),
        )
    with (OUT / "topic_taxonomy_2025.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["taxonomy_id", "phase", "subject", "topic",
                         "official_scope_excerpt", "source_document"])
        for taxonomy_id, phase, subject, topic, detail in taxonomy_rows:
            writer.writerow([taxonomy_id, phase, subject, topic, detail, SYLLABUS_NAME])


def topic_tags(phase, subject, text):
    text = text.casefold()
    rules = {
        "General Awareness": [
            ("RBI and monetary system", r"\brbi\b|monetary policy|repo rate|ombudsman|reserve bank|marginal standing facility"),
            ("Banking and financial system", r"\bbank|nbfc|payment bank|sebi|insurance|pension|upi|fintech|financial"),
            ("Government schemes and policies", r"\bscheme\b|yojana|mission|union budget|government|ministry|policy|launched"),
            ("Reports, indices and surveys", r"\breport\b|index|survey|ranked|ranking|annual report|according to"),
            ("Indian economy and public finance", r"\bgdp\b|inflation|fiscal|tax|employment|national income|economy|trade"),
            ("Environment and sustainable development", r"\bclimate\b|environment|sustainable development|\bsd[g]?s?\b|biodiversity"),
            ("International affairs and institutions", r"\bimf\b|world bank|\bwto\b|united nations|international|country|countries|agreement|summit"),
            ("Science and technology", r"\bscience\b|technology|digital|artificial intelligence|\bai\b|space|satellite"),
            ("Sports, culture and general knowledge", r"\bsport|tournament|award|author|book|festival|heritage|national park|city|state"),
        ],
        "Quantitative Aptitude": [
            ("Data interpretation", r"table|chart|graph|caselet|data interpretation"),
            ("Arithmetic", r"percent|ratio|average|profit|loss|interest|work|distance|mixture|partnership"),
            ("Number systems and sequences", r"series|sequence|remainder|divisib|number"),
            ("Algebra and equations", r"equation|variable|polynomial|quadratic|algebra"),
            ("Probability and counting", r"probability|permutation|combination"),
            ("Geometry and mensuration", r"area|volume|radius|triangle|circle|cylinder|geometry"),
        ],
        "Reasoning": [
            ("Puzzles and seating arrangements", r"seating|floor|row|circle|arrangement|schedule|persons"),
            ("Syllogisms and deductions", r"syllogism|conclusion|statement"),
            ("Coding and input-output", r"coded|coding|decode|input.output"),
            ("Data sufficiency", r"data sufficien|statement i|statement ii"),
            ("Logical and critical reasoning", r"assumption|inference|argument|course of action|reasoning"),
        ],
        "English": [
            ("Reading comprehension", r"passage|according to the passage|author"),
            ("Vocabulary and usage", r"synonym|antonym|meaning|word"),
            ("Grammar and sentence correction", r"grammar|error|sentence|correction"),
            ("Cloze and fillers", r"blank|fill in|filler|cloze"),
            ("Sentence arrangement", r"rearrange|para jumble|sequence the sentences"),
        ],
        "Economic and Social Issues": [
            ("Growth and Development", r"growth|national income|per capita|poverty|employment|development"),
            ("Sustainable Development and Environment", r"sustainable|environment|climate|emission"),
            ("Indian Economy", r"indian economy|economic survey|union budget|monetary|fiscal|agriculture|industry|services|public finance"),
            ("Globalization and International Economic Issues", r"global|trade|balance of payments|export|import|wto|imf|world bank"),
            ("Social Structure in India", r"demograph|urban|migration|gender|social justice|multicultural"),
        ],
        "Finance and Management": [
            ("Financial System and Banking", r"bank|rbi|financial institution|nbfc|digital payment|financial inclusion"),
            ("Financial Markets and Instruments", r"market|forex|bond|equity|derivative|securities"),
            ("Risk, Accounting and Financial Analysis", r"risk|account|balance sheet|cash flow|ratio|capital adequacy"),
            ("Inflation, Budget and Public Finance", r"inflation|wpi|cpi|union budget|fiscal"),
            ("Management and Organizational Behaviour", r"management|organization|organizational|motivation|personality|perception|reinforcement|leadership"),
            ("Ethics and Corporate Governance", r"ethic|governance|board of director|compliance"),
            ("Communication and Interpersonal Relations", r"communication|conflict|interpersonal|transactional analysis|johari"),
        ],
        "Descriptive English": [
            ("Essay writing", r"\bessay\b"),
            ("Precis writing", r"pr[eé]cis"),
            ("Reading comprehension", r"comprehension|read the passage"),
        ],
    }
    matches = [
        label for label, pattern in rules.get(subject, [])
        if re.search(pattern, text, re.I)
    ]
    return matches or [f"{subject}: other/uncategorized"]


def flag_duplicate_question_markers(question_rows):
    marker_counts = {}
    for row in question_rows:
        key = (
            row["phase"], row["subject"], row["section"],
            row["original_question_number"],
        )
        marker_counts[key] = marker_counts.get(key, 0) + 1
    for row in question_rows:
        key = (
            row["phase"], row["subject"], row["section"],
            row["original_question_number"],
        )
        if marker_counts[key] > 1:
            row["manual_review_required"] = 1
            row["classification_confidence"] = min(
                row["classification_confidence"], 0.60
            )
            row["source_anomaly_note"] = (
                "Duplicate question marker in supplied compilation; "
                "printed number preserved for review."
            )


def setup_database(connection):
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(questions)")
    }
    for name in ("question_text", "shared_context", "classification_basis"):
        if name not in columns:
            connection.execute(f"ALTER TABLE questions ADD COLUMN {name} TEXT")
    connection.execute("DROP TABLE IF EXISTS paper_pages")
    connection.commit()


def write_gap_report(connection):
    rows = []
    for year, ranges in PHASE_ONE_RANGES.items():
        for lower, upper, subject in ranges:
            marker_counts = connection.execute(
                    """SELECT original_question_number,COUNT(*) FROM questions
                       WHERE year=? AND phase='Phase 1' AND subject=?
                       GROUP BY original_question_number""",
                    (int(year), subject),
                ).fetchall()
            observed = {int(row[0]) for row in marker_counts}
            duplicates = sorted(
                int(row[0]) for row in marker_counts if row[1] > 1
            )
            missing = sorted(set(range(lower, upper + 1)) - observed)
            status = (
                "Question-number gaps and duplicate markers in supplied compilation"
                if missing and duplicates else
                "Question-number gaps in supplied compilation" if missing else
                "Duplicate question markers in supplied compilation" if duplicates else
                "Question markers complete for expected range"
            )
            rows.append({
                "year": year,
                "phase": "Phase 1",
                "subject": subject,
                "section": "Objective",
                "expected_count": upper - lower + 1,
                "observed_count": len(observed),
                "missing_question_numbers": ";".join(map(str, missing)),
                "duplicate_question_numbers": ";".join(map(str, duplicates)),
                "status": status,
            })
    for year in range(2021, 2026):
        for subject, section, expected in (
            ("Descriptive English", "Descriptive", 3),
            ("Economic and Social Issues", "Objective", 30),
            ("Economic and Social Issues", "Descriptive", 6),
            ("Finance and Management", "Objective", 30),
            ("Finance and Management", "Descriptive", 6),
        ):
            marker_counts = connection.execute(
                    """SELECT original_question_number,COUNT(*) FROM questions
                       WHERE year=? AND phase='Phase 2' AND subject=? AND section=?
                       GROUP BY original_question_number""",
                    (year, subject, section),
                ).fetchall()
            observed = {int(row[0]) for row in marker_counts}
            duplicates = sorted(
                int(row[0]) for row in marker_counts if row[1] > 1
            )
            missing = sorted(set(range(1, expected + 1)) - observed)
            status = (
                "Question-number gaps and duplicate markers in supplied compilation"
                if missing and duplicates else
                "Question-number gaps in supplied compilation" if missing else
                "Duplicate question markers in supplied compilation" if duplicates else
                "Question markers complete for expected range"
            )
            rows.append({
                "year": str(year),
                "phase": "Phase 2",
                "subject": subject,
                "section": section,
                "expected_count": expected,
                "observed_count": len(observed),
                "missing_question_numbers": ";".join(map(str, missing)),
                "duplicate_question_numbers": ";".join(map(str, duplicates)),
                "status": status,
            })
    observed_2019 = connection.execute(
        "SELECT COUNT(*) FROM questions WHERE year=2019"
    ).fetchone()[0]
    rows.extend([
        {"year": "2019", "phase": "Phase 1 and Phase 2", "subject": "All listed sections",
         "section": "", "expected_count": "", "observed_count": observed_2019,
         "missing_question_numbers": "",
         "duplicate_question_numbers": "",
         "status": "OCR extraction recorded; no expected question counts inferred"},
        {"year": "2019", "phase": "Phase 2", "subject": "Descriptive English",
         "section": "Descriptive", "expected_count": "", "observed_count": 0,
         "missing_question_numbers": "",
         "duplicate_question_numbers": "",
         "status": "Section appears in contents; OCR found passage pages but no numbered prompts"},
        {"year": "2020", "phase": "Phase 1 and Phase 2", "subject": "",
         "section": "", "expected_count": "", "observed_count": 0,
         "missing_question_numbers": "", "duplicate_question_numbers": "",
         "status": "No 2020 paper supplied"},
        {"year": "2026", "phase": "Phase 2", "subject": "",
         "section": "", "expected_count": "", "observed_count": 0,
         "missing_question_numbers": "", "duplicate_question_numbers": "",
         "status": "No Phase 2 paper supplied"},
    ])
    with (OUT / "extraction_gaps.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def write_frequency_reports(connection):
    with (OUT / "year_subject_frequency.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["year", "phase", "subject", "section", "question_count"])
        writer.writerows(connection.execute(
            """SELECT year,phase,subject,section,COUNT(*)
               FROM questions GROUP BY year,phase,subject,section
               ORDER BY year,phase,subject,section"""
        ))
    topic_rows = connection.execute(
        """SELECT q.year,q.phase,q.subject,t.topic,COUNT(DISTINCT q.question_id)
           FROM questions q
           JOIN question_taxonomy qt ON qt.question_id=q.question_id
           JOIN taxonomy t ON t.taxonomy_id=qt.taxonomy_id
           WHERE qt.tag_role='primary'
           GROUP BY q.year,q.phase,q.subject,t.topic
           ORDER BY q.year,q.phase,q.subject,COUNT(DISTINCT q.question_id) DESC,t.topic"""
    ).fetchall()
    denominators = {
        (year, phase, subject): count
        for year, phase, subject, count in connection.execute(
            """SELECT year,phase,subject,COUNT(*) FROM questions
               GROUP BY year,phase,subject"""
        )
    }
    with (OUT / "frequency_by_theme.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["year", "phase", "subject", "primary_theme",
                         "question_count", "subject_question_count", "share_percent"])
        for year, phase, subject, topic, count in topic_rows:
            denominator = denominators[(year, phase, subject)]
            writer.writerow([
                year, phase, subject, topic, count, denominator,
                round(count * 100 / denominator, 1),
            ])


def write_progress_log(connection):
    question_count = connection.execute(
        "SELECT COUNT(*) FROM questions"
    ).fetchone()[0]
    question_papers = connection.execute(
        "SELECT COUNT(*) FROM documents WHERE document_id LIKE 'DOC-20%'"
    ).fetchone()[0]
    page_count = connection.execute(
        "SELECT SUM(page_count) FROM documents WHERE document_id LIKE 'DOC-20%'"
    ).fetchone()[0]
    ocr_records = connection.execute(
        "SELECT COUNT(*) FROM questions WHERE year=2019 AND manual_review_required=1"
    ).fetchone()[0]
    rows = [
        {
            "stage": "A - Document audit",
            "status": "Complete for supplied files and contents coverage",
            "evidence": "8 question-paper cycles/files plus supplementary guide and official 2025 syllabus excerpt inventoried; page counts, duplicates, section coverage, and text/OCR status recorded.",
            "pending": "Official year-by-year pattern cross-check; 2025 syllabus excerpt does not contain Phase I syllabus.",
        },
        {
            "stage": "B - Question extraction",
            "status": "Question-marker indexing completed; manual review remains",
            "evidence": f"{question_count} labeled question records indexed from 7 supplied paper PDFs ({page_count} pages); 2019 OCR performed on 82 pages with {ocr_records} low-confidence records flagged.",
            "pending": "Review OCR-derived records, source numbering gaps, and page-boundary passages; do not infer absent questions.",
        },
        {
            "stage": "C - Database consolidation",
            "status": "Complete for extracted records",
            "evidence": "SQLite question IDs, phase/subject/section, theme tags, PDF page citations, syllabus taxonomy and per-page question references consolidated; no answer keys or verbatim question text copied.",
            "pending": "Manually validate topic assignments and descriptive-question boundaries.",
        },
        {
            "stage": "D - Analysis",
            "status": "Preliminary theme frequencies generated",
            "evidence": "Year/subject counts and keyword-derived primary-theme frequencies exported with per-subject denominators.",
            "pending": "Manual subject/topic review, historical trend interpretation, repetition clusters, difficulty, source mapping, and structural comparison.",
        },
        {
            "stage": "E - Synthesis",
            "status": "Pending",
            "evidence": "Inventory, question index, topic taxonomy, gap log, and preliminary frequency tables available.",
            "pending": "Research report, charts/dashboard, and preparation roadmap.",
        },
        {
            "stage": "F - Quality assurance",
            "status": "Database integrity checks passed; source QA in progress",
            "evidence": "SQLite integrity and foreign-key checks pass; missing question-number runs are explicit; no answer-key content is included.",
            "pending": "Visually verify OCR and all flagged/ambiguous source pages before reporting final findings.",
        },
    ]
    with (OUT / "project_progress.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys=ON")
    setup_database(connection)
    connection.execute(
        "UPDATE taxonomy SET topic=REPLACE(topic,' — other/uncategorized',': other/uncategorized')"
    )
    syllabus_pages, syllabus_text = add_syllabus_record(connection)
    seed_syllabus_taxonomy(connection)
    with (OUT / "document_inventory.csv").open(
        newline="", encoding="utf-8-sig"
    ) as file:
        inventory = list(csv.DictReader(file))
    for row in inventory:
        if row["document_id"] == "DOC-2019":
            row["text_layer"] = "Text layer partial; Windows OCR applied to 82 low-text pages"
            row["ocr_requirement"] = "OCR applied; low-confidence OCR question records flagged for review"
            row["inventory_status"] = "Contents ranges mapped; OCR question indexing completed; manual review pending"
            row["notes"] = (
                "Memory-based compilation. Contents list no Phase 2 Finance and Management. "
                "OCR question counts are observed markers, not inferred paper totals."
            )
        elif row["document_id"] == "DOC-SYLLABUS-2025":
            row["phase_coverage"] = "Official Phase II syllabus excerpt"
            row["sections"] = (
                "Phase II ESI, English writing skills, General Finance and Management"
            )
            row["inventory_status"] = (
                "Official syllabus supplied by user; used as Phase II classification baseline"
            )
            row["notes"] = (
                "Phase I syllabus is not present in the supplied excerpt. "
                "Do not apply this syllabus retroactively."
            )
    if not any(row["document_id"] == "DOC-SYLLABUS-2025" for row in inventory):
        syllabus_path = ROOT / SYLLABUS_NAME
        syllabus_pdf = pymupdf.open(syllabus_path)
        inventory.append({
            "document_id": "DOC-SYLLABUS-2025",
            "filename": SYLLABUS_NAME,
            "year": "2025",
            "phase_coverage": "Official syllabus",
            "sections": "Phase II ESI, English writing skills, General Finance and Management",
            "pages": str(len(syllabus_pdf)),
            "document_type": "Official RBI syllabus/notification excerpt",
            "text_layer": f"Searchable text on {syllabus_pages}/{len(syllabus_pdf)} pages",
            "ocr_requirement": "No general OCR indicated",
            "answer_key": "Not applicable",
            "shift": "Not applicable",
            "sha256": hashlib.sha256(syllabus_path.read_bytes()).hexdigest(),
            "inventory_status": "Official syllabus supplied by user; established as classification baseline",
            "notes": "Phase II syllabus only; use as 2025 taxonomy baseline, not retroactively.",
        })
        syllabus_pdf.close()
        with (OUT / "document_inventory.csv").open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=inventory[0].keys())
            writer.writeheader()
            writer.writerows(inventory)
    else:
        with (OUT / "document_inventory.csv").open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=inventory[0].keys())
            writer.writeheader()
            writer.writerows(inventory)

    for pdf_path in sorted(ROOT.glob("20*.pdf")):
        if pdf_path.name.startswith("2019"):
            extracted, page_rows = question_rows_for_2019(pdf_path)
        elif pdf_path.name.startswith("2020"):
            continue
        else:
            extracted, page_rows = question_rows_for_pdf(pdf_path)
        if not extracted:
            continue
        flag_duplicate_question_markers(extracted)
        document_id = extracted[0]["document_id"]
        connection.execute("DELETE FROM cluster_members WHERE question_id LIKE ?",
                           (f"{pdf_path.stem[:4]}-%",))
        connection.execute(
            """DELETE FROM question_taxonomy WHERE question_id IN
               (SELECT question_id FROM questions WHERE document_id=?)""",
            (document_id,),
        )
        connection.execute("DELETE FROM questions WHERE document_id=?", (document_id,))
        page_to_question_ids = {}
        counts = {}
        for row in extracted:
            key = (row["phase"], row["subject"], row["section"],
                   row["original_question_number"])
            counts[key] = counts.get(key, 0) + 1
            suffix = f"-R{counts[key]:02d}" if counts[key] > 1 else ""
            question_id = (
                f'{row["year"]}-P{row["phase"][-1]}-{row["subject_code"]}-'
                f'{row["section"][:3].upper()}-Q{int(row["original_question_number"]):03d}{suffix}'
            )
            row["question_id"] = question_id
            labels = row.get("topic_labels") or topic_tags(
                row["phase"], row["subject"], row.get("question_text", "")
            )
            row["question_summary"] = row.get("question_summary") or "; ".join(labels)
            if row.get("source_anomaly_note"):
                row["question_summary"] += f'; {row["source_anomaly_note"]}'
            for label in labels:
                taxonomy_id = re.sub(
                    r"[^A-Z0-9]+", "-",
                    f'{row["phase"][:1]}-{row["subject_code"]}-{label}'.upper()
                ).strip("-")
                version = "2025-official" if row["phase"] == "Phase 2" else "question-theme-v1"
                notes = (
                    "Mapped to the user-supplied official 2025 Phase II syllabus."
                    if row["phase"] == "Phase 2"
                    else "Question-theme tag; Phase I syllabus was not supplied."
                )
                connection.execute(
                    """INSERT OR IGNORE INTO taxonomy
                       (taxonomy_id,version,phase,subject,topic,official_heading,notes)
                       VALUES(?,?,?,?,?,?,?)""",
                    (taxonomy_id, version, row["phase"], row["subject"], label,
                     label, notes),
                )
            page_to_question_ids.setdefault(row["pdf_page_start"], []).append(question_id)
            connection.execute(
                """INSERT INTO questions
                   (question_id,document_id,year,phase,subject,section,
                    original_question_number,pdf_page_start,pdf_page_end,
                    question_summary,answer_key_status,answer_verification_status,
                    question_format,extraction_confidence,classification_confidence,
                    manual_review_required,question_text,shared_context,classification_basis,
                    ocr_uncertainty)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (question_id, row["document_id"], row["year"], row["phase"],
                 row["subject"], row["section"], row["original_question_number"],
                 row["pdf_page_start"], row["pdf_page_end"], row["question_summary"], None, None,
                 "Descriptive" if row["section"] == "Descriptive" else "Objective",
                 row["extraction_confidence"], row["classification_confidence"],
                 row["manual_review_required"], None, None,
                 row["classification_basis"], row.get("ocr_uncertainty")),
            )
            for label in labels:
                taxonomy_id = re.sub(
                    r"[^A-Z0-9]+", "-",
                    f'{row["phase"][:1]}-{row["subject_code"]}-{label}'.upper()
                ).strip("-")
                connection.execute(
                    """INSERT OR IGNORE INTO question_taxonomy
                       (question_id,taxonomy_id,tag_role,confidence)
                       VALUES(?,?,?,?)""",
                    (question_id, taxonomy_id,
                     "primary" if label == labels[0] else "secondary", 0.65),
                )
        for row in page_rows:
            question_ids = ";".join(page_to_question_ids.get(row["pdf_page"], []))
            extracted_char_count = len(row["page_text"])
            connection.execute(
                """INSERT OR REPLACE INTO page_audit
                   (document_id,pdf_page,extracted_character_count,ocr_required,
                    question_ids,review_status,notes)
                   VALUES(?,?,?,?,?,?,?)""",
                (document_id, row["pdf_page"], extracted_char_count,
                 row.get("ocr_required", 0),
                 question_ids, "question_markers_extracted",
                 f'{row["phase"]}; {row["section"]}; question wording retained in source PDF'),
            )
        connection.commit()
        subject_counts = {}
        for row in extracted:
            key = f'{row["phase"]} / {row["subject"]}'
            subject_counts[key] = subject_counts.get(key, 0) + 1
        print(json.dumps({
            "file": pdf_path.name,
            "question_records": len(extracted),
            "question_pages": len(page_rows),
            "by_phase_subject": subject_counts,
        }, ensure_ascii=False))

    write_gap_report(connection)
    write_frequency_reports(connection)
    write_progress_log(connection)
    with (OUT / "master_questions.csv").open("w", newline="", encoding="utf-8-sig") as file:
        fields = [
            "question_id", "year", "phase", "subject", "section",
            "original_question_number", "pdf_page_start", "pdf_page_end",
            "question_summary", "classification_basis",
            "extraction_confidence", "classification_confidence",
            "manual_review_required",
        ]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in connection.execute(
            """SELECT question_id,year,phase,subject,section,
                      original_question_number,pdf_page_start,pdf_page_end,
                      question_summary,classification_basis,
                      extraction_confidence,classification_confidence,
                      manual_review_required
               FROM questions ORDER BY year,phase,pdf_page_start,question_id"""
        ):
            writer.writerow(dict(zip(fields, row)))

    database_checks = {
        "integrity": connection.execute("PRAGMA integrity_check").fetchone()[0],
        "document_count": connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
        "question_count": connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0],
        "question_page_count": connection.execute(
            "SELECT COUNT(*) FROM page_audit WHERE review_status='question_markers_extracted'"
        ).fetchone()[0],
        "foreign_key_violations": connection.execute("PRAGMA foreign_key_check").fetchall(),
        "syllabus_pages": syllabus_pages,
        "syllabus_text_chars": len(syllabus_text),
        "questions_by_year_phase_subject": connection.execute(
            """SELECT year,phase,subject,COUNT(*) FROM questions
               GROUP BY year,phase,subject ORDER BY year,phase,subject"""
        ).fetchall(),
    }
    (OUT / "extraction_validation.json").write_text(
        json.dumps(database_checks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(database_checks, ensure_ascii=False))
    connection.close()


if __name__ == "__main__":
    main()
