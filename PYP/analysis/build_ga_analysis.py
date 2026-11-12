"""Build a question-pattern study guide, not a current-affairs answer key.

The manually reviewed primary labels below cover all 80 GA prompts in each
supplied paper. Rebuild with the locally installed Python and PyMuPDF.
"""

import csv
from collections import Counter

import pymupdf

from build_question_pdfs import Book, OUTPUT
from build_phase2_analysis import VISUAL_RECALL


FAMILIES = {
    "B": "RBI, banking, payments, markets and financial products",
    "P": "Public schemes, social programmes and development policy",
    "E": "Economy, fiscal/tax, trade flows, reports and social/economic data",
    "I": "International bodies, groupings, diplomacy and agreements",
    "T": "Science, technology, infrastructure and defence",
    "N": "Environment, energy, physical geography and conservation",
    "A": "Other current/static: people, sport, awards, days, books, polity and culture",
}

# One primary bucket per prompt, in original question order, ten per string.
# Classification follows the fact tested, not every institution named in a stem.
# Domain-specific reports remain in their domain (e.g. FSR in B, forests in N).
REVIEWED = {
    2019: (
        "BATITNBBAA", "TAANNTABAA", "BNBITEAAAT", "ATBNIBIATI",
        "AANAIANBAB", "IBEATIAAEI", "TBAIBPEBNA", "AABIIIBBNA",
    ),
    2021: (
        "EEPTTAPBBN", "ENAAABBBBP", "NTPPAABAAB", "PTTBBABBPE",
        "TBNBPTBNTT", "BBAABAIABB", "APABBNPAEN", "APIEIEAIBP",
    ),
    2022: (
        "PBAPBAITBB", "BPAEEEPBAA", "ENNABBBIBB", "AAABIPEAPA",
        "PNTAABNAEE", "ETPPBANBBB", "IPEAIIEPBP", "BBBBABBETN",
    ),
    2023: (
        "IIBAEANEBE", "BNIIEBEBIB", "ABAABEEEEA", "BBNBBBATAE",
        "ENBPEPIPEP", "PEEAPBETBB", "EEPBPBTBEB", "BBBITEEANP",
    ),
    2024: (
        "ABBIBABABP", "IEBBABBBEB", "BABABEBBBE", "TINBEEBBNE",
        "PANBABAEEB", "PBEBBITANE", "PEABBABBBB", "BEPBPBIBPB",
    ),
    2025: (
        "ATAAAATTAA", "AIBEPPABBA", "BBTTANTAAT", "TBEABANBPE",
        "EBBBIBPBEE", "BBBBAEEEEE", "BBIBNBBBNA", "TNTABNTTBB",
    ),
    2026: (
        "TIIAAAAAIA", "IPBTBTBAAP", "AATNATTBBA", "ATNBBIBEAT",
        "BANEPEEAAN", "BBANABPANA", "BNEINBEABN", "ATBBABEEBN",
    ),
}

SECTIONS = [
    ("RBI and finance: learn the rule, scope and exception", [
        ("What to study first",
         "RBI functions and departments; MPC and monetary tools; bank types; NBFC/HFC basics; "
         "SEBI, IRDAI, PFRDA, NABARD, SIDBI and EXIM roles; deposits and insurance; NPAs; "
         "money-market instruments; government securities; payment-system ownership and features."),
        ("Pattern 1 - limits, thresholds, eligibility and exceptions",
         "Learn value + covered entity + transaction/use case + effective date + exception. "
         "Examples: RTGS minimum (2021 Q19; 2026 Q29), UCB exposure (2023 Q25), "
         "SFB-to-universal-bank criteria (2024 Q44), payment-aggregator net worth (2025 Q46). "
         "Do not memorise a naked number without its scope."),
        ("Pattern 2 - institution, mandate and product distinctions",
         "Practise regulator versus operator, institution versus function, account versus payment "
         "instrument, and bank category versus licence. Examples: financial-organisation role "
         "matching (2026 Q15); payment-system operator (2023 Q36); BSBDA features (2025 Q67)."),
        ("Pattern 3 - index/report dimensions and policy framework",
         "Learn what the indicator measures, dimensions, weights if prominent, latest dated "
         "headline, and interpretation. RBI Digital Payments Index: 2021 Q27 and 2024 Q3. "
         "FI-Index: 2024 Q21 and 2025 Q43. Framework pillars: 2025 Q42 and 2026 Q17."),
        ("Pattern 4 - financial concepts in statements",
         "Learn why bond prices and yields move inversely, call/notice/term-money distinctions, "
         "deposit insurance, SGB features and forex-reserve components. Examples: 2022 Q59, "
         "2023 Q32/Q34, 2024 Q46 and 2026 Q52. Concepts make statement elimination possible."),
        ("How to study and keep notes short",
         "Use one static banking source, one monthly compilation and selected RBI releases. "
         "Make a comparison table, not a circular transcription: item | old rule | new rule | "
         "scope | effective date | source. Mark proposed, issued and effective separately."),
        ("What not to study deeply",
         "Do not read every circular, learn advanced derivatives/accounting mathematics for GA, "
         "or memorise every bank's product catalogue. Keep major launches and institutional "
         "changes in a short current-affairs list; do not let them replace conceptual foundations."),
        ("Phase II connection",
         "Payments, inclusion, regulation, consumer protection, inflation and banking stability "
         "feed Finance. Add one mechanism and one policy implication to selected GA facts."),
    ]),
    ("Schemes: study the beneficiary and delivery design", [
        ("The recurring test is not just the scheme name",
         "Prompts ask objective, ministry, beneficiary, exclusion, benefit, funding, component, "
         "target, duration, extension, convergence or the incorrect statement. Reading a launch "
         "headline is insufficient; reading the entire guideline is usually unnecessary."),
        ("Theme 1 - agriculture, rural livelihoods and energy",
         "Prioritise farmer income, irrigation/solar pumps, crop and allied-sector support, "
         "SHGs, rural roads and credit. Examples: PM-KISAN exclusions (2021 Q23); "
         "PM-KUSUM features (2021 Q20; 2023 Q80); SHG-linked scheme (2021 Q45); "
         "horticulture assistance (2023 Q50); rural-road objective (2026 Q45)."),
        ("Theme 2 - credit, livelihoods and enterprise",
         "Prioritise MSME credit/guarantees, street vendors, Mudra, entrepreneurship, inclusion "
         "and skilling. Examples: ECLGS extension/envelope (2022 Q1); PM SVANidhi statements "
         "(2022 Q41); Mudra revised eligibility/limit (2024 Q51); skill-scheme identification "
         "(2025 Q47). Distinguish loan, subsidy, insurance and guarantee."),
        ("Theme 3 - health, education, women and social protection",
         "Prioritise scholarships, nutrition, health coverage, pensions, housing and gender-linked "
         "programmes. Examples: scholarship allocation (2021 Q24), KGBV coverage (2021 Q80), "
         "PMAY-U support (2024 Q10/Q41), BBBP statements (2024 Q79), joint health initiative "
         "(2025 Q39)."),
        ("Theme 4 - infrastructure, industry and trade policy",
         "Cover major housing/water/logistics, PLI, public-asset monetisation and export-support "
         "programmes. Examples: NMP/NIP sector composition (2022 Q49/Q50), RoDTEP replacement "
         "(2021 Q62), foreign-trade-policy pillars (2023 Q8). Some of these are counted under "
         "economy/infrastructure in the primary audit; the conceptual overlap is intentional."),
        ("One compact scheme card",
         "Name | ministry | objective | beneficiary/exclusion | benefit/delivery | funding/type | "
         "target/duration | latest change/date. Use a short field only when applicable. Add one "
         "confusable neighbour and test yourself with two true statements and one altered statement."),
        ("Where to study",
         "Start with one exam-focused monthly source. Verify important changes through PIB, "
         "the implementing ministry, official guidelines and Budget documents. MyScheme is a "
         "discovery aid; scheme guidelines resolve eligibility and benefit details."),
        ("What not to study deeply",
         "Do not memorise every district, administrative form or minor state scheme. Do not copy "
         "all historical extensions. Keep the current version and only the old/new contrast needed "
         "to understand the change. Important national/state developments still need breadth."),
        ("Phase II connection",
         "Group by the problem solved: jobs, poverty, inclusion, health, education, agriculture, "
         "gender or urbanisation. Add delivery mechanism, one outcome and one implementation "
         "constraint for ESI; keep that separate from the factual GA card."),
    ]),
    ("Reports and data: issuer, measure, edition and finding", [
        ("What the papers actually ask",
         "Report issuer; indicator definition/dimensions; India rank or score; top country/state; "
         "largest component; change over time; forecast vintage; and interpretation. "
         "Learn report families, not a spreadsheet of unrelated numbers."),
        ("Observed: RBI report family",
         "Annual Report: government-security holdings and macro/household data (2023 Q11/Q15/Q66). "
         "Financial Stability Report: asset quality and capital (2023 Q16; 2024 Q65). "
         "Report on Currency and Finance: digital-payment implications (2024 Q18). "
         "FI-Index/Digital Payments Index: dimensions and drivers (2024 Q3/Q21; 2025 Q43)."),
        ("Observed: domestic social and economic indicators",
         "Economic Survey (2024 Q49; 2025 Q57); NFHS (2022 Q21); ASUSE (2024 Q36); "
         "SDG India Index (2024 Q35); Social Progress Index (2023 Q57); "
         "State Food Safety Index (2023 Q29); NIRF (2023 Q41); "
         "agriculture ministry annual report (2025 Q50)."),
        ("Observed: international reports and indices",
         "WIPO Global Innovation Index (2021 Q1; 2025 Q58); WEF Global Gender Gap (2023 Q5); "
         "UNDP Human Development Report (2025 Q60); Global Peace Index (2024 Q26); "
         "Environmental Performance Index (2024 Q30); IEA India Energy Outlook (2021 Q2); "
         "FAO State of the World's Forests (2022 Q22/Q80)."),
        ("Observed: less obvious report questions",
         "World Bank Migration and Development Brief (2024 Q72); Atlas-method GNI denomination "
         "(2026 Q47); QS rankings (2025 Q56); IMD competitiveness (2025 Q59); "
         "World Press Freedom Index (2026 Q63). These demonstrate breadth, not a demand to "
         "memorise all reports or all ranks."),
        ("Preparation additions - useful, not all claimed as GA repeats",
         "Read Budget at a Glance and key Budget announcements, relevant Economic Survey "
         "summaries, RBI Monetary Policy Report and Report on Trend and Progress of Banking, "
         "MoSPI GDP/CPI/IIP/PLFS releases, IMF WEO and World Bank Global Findex selectively. "
         "These strengthen GA foundations and Phase II overlap."),
        ("The six-field report note",
         "Title/issuer | edition/release date | what measured | India headline | leading comparator "
         "or largest component | one implication. For numeric data add reference period and unit. "
         "Distinguish rank from score, estimate from forecast, and release year from data year."),
        ("What to skip",
         "Skip whole-country rank tables, technical appendices, every monthly fluctuation and "
         "unchanged minor indicators. Do not memorise historical PYQ values as 2027 facts. "
         "A rank or limit remains tied to its source edition until deliberately updated."),
    ]),
    ("Breadth and mixed questions: a controlled second layer", [
        ("Why core-only preparation is risky",
         "The supplied papers vary sharply. The 2019 and 2026 compilations include substantial "
         "general/static material, while 2024 is particularly finance-heavy. Do not use the "
         "latest paper as a complete blueprint, and do not assume one narrow basket yields 48 marks."),
        ("International institutions and agreements",
         "Learn mandate, members/non-members, headquarters when prominent, host/chair, country "
         "and verified agreement status. Examples: BIMSTEC/ASEAN overlap (2023 Q19); EFTA "
         "members (2025 Q12); OPEC membership (2026 Q2). Keep agreement signed/ratified/"
         "effective distinct; use one small grouping-comparison sheet."),
        ("Environment, energy and geography",
         "Study current-linked national parks/wetlands, biodiversity, major rivers/dams, climate "
         "concepts, energy transition and resource geography. Examples: Ramsar location "
         "(2021 Q66), El Nino mechanism (2023 Q42), lithium-triangle geography (2024 Q59), "
         "dam-river matching (2026 Q54). Avoid encyclopaedic lists of every protected area."),
        ("Technology, infrastructure and defence",
         "Learn agency, purpose, location/partner, headline capability and status. Examples: "
         "railway safety system (2022 Q52), Aditya-L1 milestone (2024 Q31), digital-address "
         "format (2026 Q27), naval exercises (2019 Q125/Q181; 2025 Q2). Skip technical "
         "engineering detail unless the question level demands it."),
        ("Other current affairs and selected static GK",
         "Keep short lists for major awards, books/authors, sports winner/venue, appointments, "
         "days/themes and news-linked polity/history/culture. Examples: sports hosts "
         "(2021 Q58; 2025 Q20; 2026 Q19), book author (2019 Q161; 2025 Q11; 2026 Q30), "
         "anti-defection schedule (2024 Q15). Do not abandon this layer, but cap the time spent."),
        ("How mixed nodes connect - example chains",
         "Digital payments -> operator/features (GA) -> inclusion/costs/consumer protection "
         "(Finance/ESI). Solar-pump scheme -> beneficiary/subsidy (GA) -> farm costs, water "
         "use and energy transition (ESI). Remittances -> report/transaction cost (GA) -> "
         "external sector and development (ESI/Finance). Housing -> eligibility/finance (GA) "
         "-> urbanisation and implementation (ESI)."),
        ("Stop the rabbit hole",
         "For one news event learn the tested fact plus two or three directly connected facts. "
         "Do not expand an exercise into an entire military inventory, or a wetland into a "
         "complete atlas. One source, one compact note, repeated retrieval."),
    ]),
    ("A practical 60% strategy: retrieval, selection and updates", [
        ("Scoring, not just attempts",
         "Assuming 80 one-mark questions with a quarter-mark penalty, target net 48/80. "
         "50 correct and 8 wrong gives 48; 52 correct and 8 wrong gives 50. "
         "At about 85% accuracy, approximately 60 attempts are needed for 48 net. "
         "At 80%, approximately 64 are needed. Confirm official marking and timings for your cycle."),
        ("Where the marks must come from",
         "There is no defensible fixed allocation such as 20 banking + 15 schemes + 13 reports "
         "that guarantees 48. The audit's banking+schemes+economy basket is not even 48 prompts "
         "in several supplied years. Build the core deeply, then earn additional marks through "
         "controlled breadth. Aim above the target in practice."),
        ("A manageable daily block - suggested, not a proven optimum",
         "For a 90-minute GA block: 30 minutes one monthly/current-affairs source, 20 minutes "
         "static banking/economy foundations, 20 minutes closed-book recall or fresh MCQs, "
         "and 20 minutes correcting errors and reviewing old cards. Adjust from your measured "
         "weaknesses; do not add several duplicate compilations."),
        ("If only eight weeks remain",
         "Weeks 1-2: diagnose with fresh GA sections; build banking/payment/inclusion foundations "
         "while maintaining current affairs. Weeks 3-4: scheme themes, Budget/Survey and report "
         "cards. Weeks 5-6: repair international/environment/science/general breadth using "
         "missed-question families. Weeks 7-8: cumulative revision and fresh timed sections; "
         "reduce new-source intake."),
        ("Current-affairs window - a planning choice, not a PYQ finding",
         "Start with roughly the most recent six months, plus the latest relevant annual reports, "
         "Budget/Survey and older major continuing policies. Give recent developments more review "
         "time, but keep static foundations. These files alone do not establish an exact optimal "
         "month window; widen it only when mock misses and major-event relevance justify it."),
        ("Reverse learning from mocks",
         "For each miss label: never studied, forgotten, confused pair, stale value, careless "
         "NOT/EXCEPT, or unjustified guess. Repair the whole fact template, not just that answer. "
         "For a UPI-limit miss, compare use cases and effective dates. For an index miss, "
         "repair issuer, measure, edition and headline. Retest with unseen variants."),
        ("Short notes and revision",
         "Use one-line factual cards, comparison tables and the scheme/report templates. "
         "Keep GA facts separate from a short Phase II box: mechanism + dated evidence + "
         "implication/limitation. Suggested retrieval intervals: next day, one week, two weeks "
         "and one month. Mark superseded facts rather than retaining competing 'latest' values."),
        ("Exam time traps and readiness",
         "First pass: answer secure recall promptly. Park facts with no recognition after about "
         "10-15 seconds; longer thought rarely manufactures recall. Give statement/matching "
         "questions extra time only when elimination is concrete. Avoid stale-value confidence, "
         "similar acronyms and personal-opinion guesses. Calibrate all timings in mocks. "
         "Exceed 48 net in at least three fresh timed sections before trusting the approach; "
         "that is a checkpoint, not a guarantee."),
    ]),
]


VISUAL_GA = [
    ("Use small news-to-static maps",
     "Centre: a new payment-system development.\n"
     "Branches: What changed? Who issued/operates it? Who is covered? "
     "Limit/condition/effective date? Related static concept?\n"
     "Stop unless another connection is directly useful. Do not expand one announcement "
     "into the entire financial system. Discrete facts usually belong in tables, not huge maps."),
    ("Scheme table",
     "Columns: Scheme | Ministry | Beneficiary/exclusion | Benefit | Delivery/funding | "
     "Latest change. Cover a column and retrieve it. Then test a borderline beneficiary "
     "case: eligible or ineligible, and why? Objectives alone do not establish eligibility."),
    ("Report table",
     "Columns: Report | Publisher | Edition/data period | What measured | India headline | "
     "Important comparison. Keep release year distinct from reference year and rank "
     "distinct from score. Every changing figure needs a date or edition."),
    ("Regulatory-change table",
     "Columns: Item | Old rule | New rule | Covered entity/use case | Effective date. "
     "Do not learn an amount without scope. Distinguish announced/proposed, issued "
     "and effective status before memorising the change."),
    ("Turn rows into retrieval questions",
     "Who is excluded? Which institution publishes this? What does the indicator measure? "
     "Does the limit apply to this transaction category? When did the rule become effective? "
     "Reverse questions too: identify the scheme from its beneficiary and benefit."),
    ("Cards versus cases",
     "Use one-fact cards for issuer, date or acronym. Use comparison tables for confusable "
     "institutions and products. Use eligible/ineligible mini-cases for complicated rules. "
     "Reading a table repeatedly is not the same as recalling its hidden columns."),
]


def reviewed_rows():
    rows = []
    for year, blocks in REVIEWED.items():
        if len(blocks) != 8 or any(len(block) != 10 for block in blocks):
            raise ValueError(f"{year}: expected eight blocks of ten reviewed prompts")
        for offset, family in enumerate("".join(blocks)):
            if family not in FAMILIES:
                raise ValueError(f"{year}: unknown family {family}")
            number = offset + (121 if year == 2019 else 1)
            rows.append({
                "year": year,
                "original_question_number": number,
                "primary_family": family,
                "family_description": FAMILIES[family],
                "source": f"{year} (Phase 1{'-2' if year != 2026 else ''}).pdf",
            })
    if len(rows) != 560:
        raise ValueError("Expected 560 manually reviewed GA prompts")
    return rows


def build():
    rows = reviewed_rows()
    audit = OUTPUT / "phase1_general_awareness_pattern_audit.csv"
    with audit.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    book = Book("General Awareness")
    book.new_page()
    book.bookmarks.append([1, "Evidence, frequency and limits", 1])
    book.text("General Awareness: study analysis", 21, True)
    book.text("Exact fact patterns, priorities and a 60% preparation strategy", 12, True)
    book.text(
        "Evidence: 560 GA prompts, 80 each from the supplied 2019 and 2021-2026 "
        "memory-based compilations. The 2019 section was reviewed using local OCR. "
        "No 2020 paper was supplied. Examples use original question numbers "
        "(2019: Q121-200; later years: Q1-80). This guide contains analysis, not questions or answers.",
        10,
    )
    book.text(
        "Historical prompts reveal question design, not verified present-day facts. No answer "
        "keys are used. Examples do not endorse every factual premise in a recollection. "
        "For 2027, update policy values, memberships, ranks and scheme status from the relevant "
        "official source; do not learn old numbers as current facts.", 10,
    )
    book.text("Manual primary-family audit: questions, not forecast marks", 13, True)
    book.text("Year       B       P       E       I       T       N       A       Total", 10, True)
    for year in REVIEWED:
        counts = Counter(row["primary_family"] for row in rows if row["year"] == year)
        book.text(
            f"{year}:  " + " / ".join(f"{key}={counts[key]}" for key in FAMILIES) + "  | total=80",
            10,
        )
    for key, name in FAMILIES.items():
        book.text(f"{key}: {name}.", 9)
    book.text(
        "Each prompt has one primary bucket based on the fact tested. Mixed links are explained "
        "in the subject sections, not double-counted. Financial reports stay in B; environmental "
        "reports stay in N; other social/economic indices generally sit in E. A bank-award "
        "recipient can sit in A rather than B. Borderline classifications are judgement calls, "
        "not an official topic allocation. Repeated prompts are counted as printed, not as "
        "independent unique concepts. The companion CSV exposes every classification.", 9,
    )
    book.text("The central finding", 13, True)
    book.text(
        "Prioritise RBI/finance + major schemes + economy/data for depth and Phase II overlap. "
        "Do not mistake that core for the whole paper. Maintain a bounded breadth layer for "
        "international affairs, environment, technology and general/static current affairs. "
        "Repeated fact templates are more useful than trying to predict exact questions.", 10,
    )
    analysis_sections = SECTIONS + [
        ("Studying GA with mind maps and data tables", VISUAL_GA),
        ("Making visual notes stick: recall and practice", VISUAL_RECALL),
    ]
    for title, paragraphs in analysis_sections:
        book.new_page()
        book.bookmarks.append([1, title, len(book.document)])
        book.text(title, 18, True)
        for heading, paragraph in paragraphs:
            if book.y + 85 > 798:
                book.new_page()
            book.text(heading, 11, True)
            book.text(paragraph, 10)

    book.new_page()
    book.bookmarks.append([1, "Sources and use", len(book.document)])
    book.text("Where to study: a short source stack", 18, True)
    for title, text in [
        ("One exam-focused source",
         "Choose one monthly RBI Grade B current-affairs compilation and one MCQ/mock source. "
         "This guide does not establish that any commercial provider covers everything."),
        ("RBI",
         "Policy releases, reports, payment/banking directions and index releases: https://www.rbi.org.in/"),
        ("Budget and Economic Survey",
         "Budget at a Glance, speech and selected Survey chapters: https://www.indiabudget.gov.in/"),
        ("Schemes",
         "PIB for developments: https://pib.gov.in/ ; discover schemes at https://www.myscheme.gov.in/ "
         "and verify important eligibility/benefits with the implementing ministry."),
        ("Official data",
         "MoSPI for national accounts, CPI/IIP and labour/survey releases: https://mospi.gov.in/ ; "
         "use the relevant ministry for sector data and NITI Aayog for its own publications: "
         "https://www.niti.gov.in/"),
        ("International report issuers",
         "Use the issuer's latest applicable edition: WIPO, UNDP, WEF, IMF, World Bank, IEA and FAO. "
         "Consult summaries/headline tables selectively; these are not instructions to read every report."),
        ("Evidence and limitations",
         "Source folder: PYP. Companion audit: phase1_general_awareness_pattern_audit.csv. "
         "Counts describe supplied compilations, not verified official paper weightages. The "
         "supplied 2025 official syllabus excerpt is Phase II only; it is not evidence for a "
         "complete official Phase I topic list. The guide's study time and revision rules are "
         "recommendations requiring calibration, not measured historical difficulty."),
    ]:
        book.text(title, 12, True)
        book.text(text, 10)
    book.document.set_toc(book.bookmarks)
    book.document.set_metadata({
        "title": "RBI Grade B Phase I - General Awareness - Pattern and Study Analysis",
        "subject": "Historical question patterns, study priorities and 60% strategy; no answers",
        "creator": "Local supplied-paper analysis",
    })
    output = OUTPUT / "phase1_general_awareness_analysis.pdf"
    book.document.save(output, deflate=True, garbage=4)
    book.document.close()
    with pymupdf.open(output) as saved:
        if len(saved.get_toc()) != len(analysis_sections) + 2:
            raise ValueError("Missing analysis bookmarks")
        for page in saved:
            for block in page.get_text("dict")["blocks"]:
                if block["type"] == 0 and block["bbox"][3] > 828:
                    raise ValueError(f"Text exceeds print area on page {page.number + 1}")
        print(f"{output.name}: {len(saved)} pages; 560 prompts audited")
    for year in REVIEWED:
        print(year, dict(Counter(row["primary_family"] for row in rows if row["year"] == year)))


if __name__ == "__main__":
    build()
