import csv
import html
import json
import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path


OUT = Path(__file__).resolve().parent
WORKSPACE = OUT.parent.parent
REPORT_DIR = WORKSPACE / "pyp_analysis"
DATABASE = OUT / "questions.sqlite"
TAXONOMY_FILE = OUT / "topic_taxonomy_2025.csv"
GAPS_FILE = OUT / "extraction_gaps.csv"
REPORT_FILE = REPORT_DIR / "rbi_grade_b_report.html"
NOTES_GRAPH_DATA_FILE = REPORT_DIR / "phase2_notes_graph.json"
NOTES_GRAPH_FILE = REPORT_DIR / "phase2_notes_graph.html"
PHASE_ONE_YEARS = list(range(2021, 2027))
PHASE_TWO_YEARS = list(range(2021, 2026))
COMPLETE_PHASE_ONE_YEARS = {
    "General Awareness": [2021, 2022, 2023, 2024, 2026],
    "Quantitative Aptitude": [2021, 2022, 2023, 2024, 2025, 2026],
    "Reasoning": [2021, 2022, 2023, 2024, 2026],
    "English": [2021, 2022, 2023, 2024, 2026],
}
PHASE_ONE_EXPECTED = {
    "General Awareness": 80,
    "Quantitative Aptitude": 30,
    "Reasoning": 60,
    "English": 30,
}
PHASE_ONE_TAG_ALIASES = {
    "RBI, monetary system and regulation": "RBI and monetary system",
    "Science, technology and AI": "Science and technology",
    "Unclassified / mixed": "Quantitative Aptitude: other/uncategorized",
    "Other / mixed reasoning": "Reasoning: other/uncategorized",
    "Coding and input-output": "Coding and input-output",
    "Logical and critical reasoning": "Logical and critical reasoning",
    "Cloze / fillers": "Cloze and fillers",
    "Other / unresolved": "English: other/uncategorized",
    "Other / unclassified": "General Awareness: other/uncategorized",
}

PHASE_ONE_BOUNDARIES = {
    "General Awareness": {
        "RBI, monetary system and regulation": (
            "RBI mandate and institutional roles; MPC/repo corridor; liquidity and policy transmission; payment rails; current regulations, consumer safeguards and financial-stability signals.",
            "Do not memorise every circular clause or historical rate. Learn the latest live rule, its scope, effective date and policy purpose.",
        ),
        "Banking and financial system": (
            "Regulator-to-entity mapping; bank/NBFC/co-operative-bank distinctions; deposits, credit, priority-sector lending, inclusion, payment systems and major institutional changes.",
            "Skip obscure bank histories, exhaustive balance-sheet values and every product feature unless a current RBI change makes it newsworthy.",
        ),
        "Government schemes and policies": (
            "For high-priority schemes, learn ministry, objective, intended beneficiary, eligibility/exclusions, benefit or delivery, funding/guarantee, target, duration and latest extension/change.",
            "Do not memorise every scheme directory or old allocation. Drop superseded amounts and peripheral clauses; update the latest official status.",
        ),
        "International affairs and institutions": (
            "Mandate and membership of IMF, World Bank, WTO, UN and key regional groups; India’s role, chair/host, headline decisions, reports and trade/energy/financial consequences.",
            "Avoid exhaustive country trivia, every delegation name and speculation. Learn geography only when it explains a current conflict, route, group or agreement.",
        ),
        "Reports, indices and surveys": (
            "Publisher, report edition/year, indicator/methodology, India/state rank or score, top performers, direction of change and the policy implication.",
            "Do not learn every country rank or raw table. Focus on India, major comparators, headline dimensions and changes from the previous edition.",
        ),
        "Indian economy and public finance": (
            "GDP/inflation/jobs, trade, fiscal deficit/debt, receipts and expenditure, capex, agriculture, industry and external buffers; always attach period, source and units.",
            "Avoid unaudited forecasts and long statistic lists. Do not mix nominal with real, budget estimate with actual, or calendar year with fiscal year.",
        ),
        "Science, technology and AI": (
            "Indian mission/platform, implementing institution, purpose/application, one salient feature, status and economic/social/security impact; AI governance and digital public infrastructure.",
            "Skip engineering derivations, product trivia and unverified launch claims. Study risks (privacy, bias, cyber, jobs, concentration) only to explain policy trade-offs.",
        ),
        "Environment and sustainable development": (
            "Convention/body, species/ecosystem/location, climate or disaster event, Indian programme, energy transition and link to agriculture, health, livelihoods or inflation.",
            "Do not memorise every species list or climate statistic. Learn high-profile locations, treaty purpose and verified impact channels.",
        ),
        "Sports, culture and general knowledge": (
            "Major winners, tournament/host, record/first, award, heritage site, important day/person and location; use short spaced-recall cards.",
            "Do not chase low-salience trivia, obscure scores or broad static encyclopaedia chapters. Retain only high-profile India/world facts and recent award/event results.",
        ),
        "Other / unclassified": (
            "Use the mixed-category audit below: schemes/policy, RBI/payments, economy/trade, institutions/geopolitics, environment, technology/infrastructure, defence and static GK.",
            "Do not prepare 'other' as a separate subject or infer a precise subtopic weight from its 70 records. Revisit source-based families and mixed mocks instead.",
        ),
    },
    "Quantitative Aptitude": {
        "Arithmetic": (
            "Percentages, ratios, averages, profit/loss, interest, time/work, speed/distance, mixtures and partnerships; practise translating words to equations and checking units.",
            "Skip lengthy shortcut collections and exotic one-off tricks. Keep standard methods fast and accurate before adding shortcuts.",
        ),
        "Number systems and sequences": (
            "Divisibility, remainders, factors, basic number properties and common missing/wrong-term series patterns.",
            "Do not memorise arbitrary pattern lists; verify a rule across every term and stop after a sensible time limit.",
        ),
        "Data interpretation": (
            "Tables, charts and caselets; ratios, percentage change, averages, comparisons and multi-step arithmetic under time pressure.",
            "Do not infer low importance from the 9 automatic tags: shared-set extraction can hide DI. Avoid advanced statistics outside the exam level.",
        ),
        "Algebra and equations": (
            "Linear/quadratic equations, identities, roots and equation-based word problems.",
            "Skip advanced polynomial theory and lengthy derivations; drill standard forms and setup accuracy.",
        ),
        "Geometry and mensuration": (
            "Core plane-area, perimeter and volume formulas; basic shapes and direct substitutions.",
            "Do not overinvest in rare theorem proofs or complicated constructions; learn formula use and representative timed problems.",
        ),
        "Unclassified / mixed": (
            "Use mixed sets to find hidden arithmetic, DI, approximation, comparison, data sufficiency or calculation patterns; tag every error by cause.",
            "Do not assume the bucket is a single chapter or spend time trying to memorise its count as a study plan.",
        ),
    },
    "Reasoning": {
        "Puzzles and seating arrangements": (
            "Linear/circular seating, floors, scheduling and multi-attribute arrangements; build a clean diagram, place fixed constraints, branch only when needed.",
            "Do not brute-force every possibility or persist with a set after its time ceiling. Avoid assuming unstated circular orientation.",
        ),
        "Syllogisms and deductions": (
            "Venn/possibility logic, definite versus possible conclusions, statement-based deductions and common inequality relations.",
            "Do not import real-world knowledge or treat a possible conclusion as definite.",
        ),
        "Other / mixed reasoning": (
            "Cover direction/distance, blood relations, order/ranking, alphanumeric series, data sufficiency, coding/input-output and critical-reasoning forms through rotating mixed sets.",
            "Do not omit stand-alone formats because the automatic index failed to name them; do not overtrain one puzzle type at the expense of breadth.",
        ),
        "Coding and input-output": (
            "Identify rule transformations and sequence operations; check the rule on all given examples before applying it.",
            "Skip bespoke, lengthy pattern systems after learning common forms; do not infer a 2027 weight from three clean-cycle tags.",
        ),
        "Logical and critical reasoning": (
            "Assumptions, inference, strengthen/weaken and argument conclusions; separate evidence from opinion.",
            "Do not answer from personal beliefs or introduce facts absent from the prompt.",
        ),
    },
    "English": {
        "Reading comprehension": (
            "Main idea, inference, tone, vocabulary-in-context and detail; locate passage evidence before choosing.",
            "Do not use outside knowledge or over-read every option; avoid translating the whole passage word-for-word.",
        ),
        "Grammar and sentence correction": (
            "Agreement, tense, modifiers, parallelism, articles/prepositions, connectors and error diagnosis; keep a rule-based error log.",
            "Do not memorise isolated exceptions without context or choose by what merely sounds familiar.",
        ),
        "Vocabulary and usage": (
            "Meaning in context, collocation, usage and high-frequency academic/current-affairs vocabulary; use spaced review.",
            "Avoid huge low-frequency word lists and standalone memorisation without example usage.",
        ),
        "Sentence arrangement": (
            "Opening sentence, chronology/logic, pronoun references, transitions and paragraph cohesion.",
            "Do not rely only on connector words; confirm that the full sequence is coherent.",
        ),
        "Cloze / fillers": (
            "Grammar plus local and paragraph-level meaning; test each blank in the full sentence and passage.",
            "Do not select a word from grammar alone when context changes the meaning.",
        ),
        "Other / unresolved": (
            "Rotate sentence improvement, phrase replacement, error spotting, connectors, word usage and short passage tasks in mocks; classify each missed format.",
            "Do not treat 63 unresolved markers as one format or infer that untagged task types are absent.",
        ),
    },
}

PHASE_TWO_DEPRIORITIZE = {
    "Growth and Development": "Do not memorise long unsourced indicator lists or generic development slogans; skip advanced econometrics. Use a few dated indicators and explain mechanisms/policy trade-offs.",
    "Indian Economy": "Do not reproduce entire Survey/Budget chapters or memorise every scheme/statistic. Avoid deep historical detail unrelated to policy since 1991 and current sectoral issues.",
    "Globalization": "Do not memorize every trade agreement clause or country tariff. Avoid predicting deal dates; study verified status, institutional roles and transmission channels.",
    "Social Structure in India": "Do not prepare broad sociological theory beyond the syllabus or use unsourced stereotypes. Prefer indicators, causes, policy response and balanced impact.",
    "Financial System": "Do not memorize every circular or institution head. Skip technical payment-message specifications; learn mandates, system flow, risks and current policy changes.",
    "Financial Markets": "Do not pursue advanced pricing mathematics or daily market levels. Focus on instruments, participants, price/yield relationships and policy transmission.",
    "Financial Risk Management + Accounting and Financial Statements": "Do not study advanced valuation/accounting standards or derive complex risk models. Focus on statements, core ratios, risk types, controls and interpretation.",
    "Basics of Derivatives": "Do not learn advanced option pricing or stochastic models. Cover contract types, rights/obligations, payoff direction, hedging and basic risk.",
    "Global Financial Markets and International Banking": "Do not memorize daily FX/market quotes or speculative forecasts. Track broad shocks, institutions, exposure and transmission to India.",
    "Financial Inclusion": "Do not equate account counts with meaningful inclusion or memorize every scheme detail. Study access, usage, quality, barriers, protection and current index dimensions.",
    "Alternate Sources of Finance": "Do not study project-finance legal clauses or advanced appraisal math. Cover PPP rationale, social/private cost-benefit and risk allocation.",
    "Union Budget + Inflation (joint tag)": "Do not infer separate frequency from a joint tag, memorize every tax line, or confuse BE/RE/actuals. Learn core definitions, headline verified numbers and policy implications.",
    "Fundamentals of Management and Organizational Behaviour": "Do not memorize thinker biographies or lists of theory names without application. Learn each model's core idea, workplace example and limitation.",
    "Banking Corporate Governance + Workplace Ethics (joint tag)": "Do not treat six combined tags as six questions in each chapter. Avoid abstract moral-philosophy essays; apply principles to accountability, controls, conflicts and governance.",
    "Unclassified / mixed ESI tags": "Do not treat this as a chapter or infer a specific chapter share. Many records are passage-linked scheme/policy facts; use the manual family map and keep coverage across the four ESI chapters.",
    "Unclassified / mixed Finance and Management tags": "Do not treat this as a chapter or use it to rank chapters. Keep minimum syllabus coverage and let mocks reveal the missing form.",
    "Communication": "Do not memorize communication jargon without scenario use. Focus on process, channel, direction, barriers, feedback and fit.",
    "English Writing Skills": "Do not predict essay prompts from previous years or use ornamental vocabulary. Score relevance, structure, coherence, faithful précis and accurate language.",
    "Unresolved descriptive-English markers": "Do not invent a fourth format from two unresolved tags; continue practicing all three observed task formats and review new mocks.",
}

GA_MIXED_FAMILIES = [
    {
        "family": "Government schemes, benefits and policy delivery",
        "examples": "PM-KUSUM, PM-KISAN, ECLGS, PM SVANidhi, PMAY/CLSS, Mudra, NAPS, RoDTEP, Jal Jeevan, Sagarmala, National Monetisation Pipeline and PLI-related policy.",
        "test": "Objective/beneficiary, nodal ministry, eligibility or exclusions, component, amount/guarantee/subsidy, target/duration, delivery channel, extension or budget change.",
        "priority": "Very high",
    },
    {
        "family": "RBI, banking, payments and financial regulation",
        "examples": "RTGS, RBI payment vision, UCB exposure norms, SHG-bank linkage, digital payment devices, exchange/bond-market mechanisms, forex reserves and financial-sector initiatives.",
        "test": "Institution/regulator, purpose, threshold or limit, covered entity, system feature, policy intent and the distinction between similar payment/market mechanisms.",
        "priority": "Very high",
    },
    {
        "family": "Economy, budget, trade and official data",
        "examples": "GST collections, exports, fiscal allocations, fertilizer subsidy, foreign-trade policy, tax changes, GNI classification, production and public-asset monetisation.",
        "test": "Correct period/unit, latest value or target, source/issuer, budget head or policy instrument, and what the number measures.",
        "priority": "Very high",
    },
    {
        "family": "Institutions, international affairs and geopolitics",
        "examples": "G20/B20, BIMSTEC, IMF/Federal Reserve, WHO, COP coordination, bilateral support, trade corridors and global political developments.",
        "test": "Mandate/member/host/chair, country or region, report issuer, summit outcome, agreement status and relevance to India.",
        "priority": "High",
    },
    {
        "family": "Climate, environment, geography and disasters",
        "examples": "Cyclones and naming, monsoon, Ramsar sites, tiger conservation, biodiversity hotspots, energy transition and strategic petroleum reserves.",
        "test": "Location/basin, convention or body, species/ecosystem, objective, verified event fact and the agriculture/energy/livelihood transmission.",
        "priority": "High",
    },
    {
        "family": "Science, digital systems, infrastructure and defence",
        "examples": "DIGIPIN/QR, railway safety and HR systems, tunnels/logistics, engineering skilling, submarine delivery and military exercises.",
        "test": "Implementing institution, use case, core capability, location/partner, operational status and economic/security application.",
        "priority": "High",
    },
    {
        "family": "Static GK, sports, culture and public observances",
        "examples": "Tournament winners/venues, records, anniversaries, awards, heritage/history, important days, capitals and selected geography.",
        "test": "Who/which place/when, host or winner, record/first and a directly linked institution or event fact.",
        "priority": "Selective but retain",
    },
    {
        "family": "Governance, law, appointments and public institutions",
        "examples": "Constitutional/political offices, commissions, major Acts, award selection, public-sector bodies and judicial data initiatives.",
        "test": "Role, appointing/selecting authority, jurisdiction, key provision or institutional function; distinguish current incumbent from statutory tenure.",
        "priority": "High",
    },
]

GA_SCHEME_CHECKLIST = [
    ("PM-KUSUM", "Farmer/solar components, objective, capacity/implementation target and link to farm power/income."),
    ("PM-KISAN", "Beneficiary and exclusion rules, central-sector funding, instalment/design and budget allocation."),
    ("ECLGS", "Eligible borrowers/sectors, guarantee/credit mechanism, extension and pandemic-recovery rationale."),
    ("PM SVANidhi", "Street-vendor eligibility, loan stages/incentives, extension and urban livelihood objective."),
    ("PMAY-U / CLSS", "Urban housing beneficiary, subsidy/credit-linked mechanism, eligibility and revised version/status."),
    ("PM Mudra", "Borrower segment, loan categories/limits, Tarun progression and current policy change."),
    ("NAPS / apprenticeship support", "Target group, ministry, employer/training role, support and extension period."),
    ("PMSS / scholarships and KGBV", "Beneficiary group, education level, funding period, coverage and inclusion objective."),
    ("RoDTEP / export support", "Eligible exports, remission rationale, implementation date and trade competitiveness."),
    ("Jal Jeevan, Sagarmala, NMP, PLI and PMAY-linked programmes", "Core objective, sector, implementing ministry, target/duration, delivery or financing design and latest progress."),
]

GA_REPORTS_TO_STUDY = [
    {
        "tier": "Must read",
        "name": "Economic Survey of India",
        "publisher": "Ministry of Finance",
        "study": "Growth composition, inflation, employment, agriculture, industry/services, external sector, productivity and the Survey's diagnosis/recommendations; learn a few dated indicators.",
        "skip": "Do not memorize every table. Read overview, relevant chapters and selected data; capture source, period and implication.",
        "url": "https://www.indiabudget.gov.in/economicsurvey/",
    },
    {
        "tier": "Must read",
        "name": "Union Budget: Budget at a Glance, Budget Speech and Expenditure Profile",
        "publisher": "Ministry of Finance",
        "study": "Fiscal deficit/debt, receipts, capex vs revenue expenditure, major allocations, tax changes, schemes, financing and one growth/inclusion implication.",
        "skip": "Do not memorize every demand-for-grants line, minor tax rate or unverified explainer figure; separate BE, RE and actuals.",
        "url": "https://www.indiabudget.gov.in/",
    },
    {
        "tier": "Must read",
        "name": "RBI Annual Report and Monetary Policy Report",
        "publisher": "Reserve Bank of India",
        "study": "RBI functions, monetary-policy rationale, inflation/growth outlook, banking/payments/regulation, currency and financial inclusion; note policy vintage and revision.",
        "skip": "Do not learn every table, circular or old policy rate; prefer latest official stance, key risks and transmission mechanism.",
        "url": "https://www.rbi.org.in/",
    },
    {
        "tier": "Must read",
        "name": "RBI Financial Stability Report",
        "publisher": "Reserve Bank of India",
        "study": "Systemic risks, bank/NBFC soundness, asset quality, capital, stress-test direction, household/corporate vulnerabilities and cyber/payment resilience.",
        "skip": "Skip detailed model assumptions and every institution-level ratio; learn headline risk, direction, source and why it matters.",
        "url": "https://www.rbi.org.in/Scripts/FsReports.aspx",
    },
    {
        "tier": "Must read",
        "name": "Report on Trend and Progress of Banking in India",
        "publisher": "Reserve Bank of India",
        "study": "Banking structure, deposits/credit, inclusion, NPAs, profitability, co-operative banks, NBFCs and regulatory/development trends.",
        "skip": "Do not memorize every bank rank or bank-specific table; use national direction and relevant RBI policy changes.",
        "url": "https://www.rbi.org.in/",
    },
    {
        "tier": "Must read",
        "name": "RBI Financial Inclusion Index and Report on Currency and Finance",
        "publisher": "Reserve Bank of India",
        "study": "FI-Index dimensions (access, usage, quality), latest score/driver, annual theme of the Currency and Finance report and implications for policy.",
        "skip": "Do not memorize component-level data unless explicitly highlighted; understand index construction and what it does not measure.",
        "url": "https://www.rbi.org.in/",
    },
    {
        "tier": "Must read",
        "name": "MoSPI National Accounts, CPI, IIP and Periodic Labour Force Survey",
        "publisher": "Ministry of Statistics and Programme Implementation",
        "study": "GDP growth/base/sector mix, inflation measure, industrial output, unemployment/labour-force participation and the period/reference definition.",
        "skip": "Do not compare incompatible series or memorize monthly noise; use latest release and major trend only.",
        "url": "https://mospi.gov.in/",
    },
    {
        "tier": "Selective, high value",
        "name": "IMF World Economic Outlook and Global Financial Stability Report",
        "publisher": "International Monetary Fund",
        "study": "Global/India growth and inflation outlook, forecast revision, drivers/risks, financial stability and energy/trade/capital-flow channels.",
        "skip": "Do not treat different forecast vintages as contradictory facts; record edition/date and avoid learning a long country table.",
        "url": "https://www.imf.org/en/Publications",
    },
    {
        "tier": "Selective, high value",
        "name": "World Bank World Development Indicators, Global Findex and flagship reports",
        "publisher": "World Bank",
        "study": "Indicator definition, India comparison, financial access/usage, development outcome and the report's central policy theme.",
        "skip": "Avoid memorizing the full indicator database or every country rank; select the relevant concept and India fact.",
        "url": "https://www.worldbank.org/en/publication",
    },
    {
        "tier": "Selective, high value",
        "name": "UNDP Human Development Report, WIPO Global Innovation Index, WEF Global Gender Gap Report",
        "publisher": "UNDP / WIPO / World Economic Forum",
        "study": "Publisher, edition, India rank/score, dimensions, top performer and one reason the metric matters; these mirror rank/dimension-style GA asks.",
        "skip": "Do not memorize all ranks or confuse rank change with score change; check methodology and edition before comparing.",
        "url": "https://hdr.undp.org/",
    },
    {
        "tier": "Selective, India-focused",
        "name": "NITI Aayog SDG India Index, India Innovation Index and Social Progress Index",
        "publisher": "NITI Aayog / partner institutions",
        "study": "State/UT ranking, indicators/dimensions, top and lagging performers, methodology and policy use.",
        "skip": "Do not learn every state position; focus on the top/bottom, major movement and what is measured.",
        "url": "https://www.niti.gov.in/",
    },
    {
        "tier": "PYQ-shaped: rank and dimensions",
        "name": "Global Innovation Index, Global Gender Gap Index, Global Peace Index and Environmental Performance Index",
        "publisher": "WIPO / World Economic Forum / Institute for Economics & Peace / Yale-CIESIN",
        "study": "Edition, publisher, India's rank/score, top country, dimensions and the specific domain measured; the supplied GA papers repeatedly use rank, top performer and dimension formats.",
        "skip": "Do not memorize every country position or confuse a country's score with its rank; verify the edition and methodology.",
        "url": "https://www.wipo.int/web/global-innovation-index/",
    },
    {
        "tier": "PYQ-shaped: India/state indicators",
        "name": "NFHS, Annual Survey of Unincorporated Sector Enterprises (ASUSE), SDG India Index and State Food Safety Index",
        "publisher": "MoHFW / MoSPI / NITI Aayog / FSSAI",
        "study": "Publisher, survey/report year, population or sector covered, headline indicator, state comparison and change from the prior round.",
        "skip": "Do not learn all survey tables, sample-design details or district ranks; focus on the policy-relevant headline and definition.",
        "url": "https://mospi.gov.in/",
    },
    {
        "tier": "PYQ-shaped: global and sector reports",
        "name": "India Energy Outlook, Migration and Development Brief, State of the World's Forests and World Bank Atlas Method",
        "publisher": "IEA / World Bank / FAO / World Bank",
        "study": "Report issuer and year, energy/forest/remittance/development theme, key indicator or classification method and how the finding affects India.",
        "skip": "Do not memorize full report chapters or unreferenced secondary summaries; separate a report's estimate from official Indian statistics.",
        "url": "https://www.worldbank.org/en/publication",
    },
    {
        "tier": "Scan when in current affairs",
        "name": "NFHS, India State of Forest Report, India State of Food Safety Index, PLFS and sectoral ministry reports",
        "publisher": "MoHFW / FSI / FSSAI / MoSPI and relevant ministries",
        "study": "New edition, publisher, one or two headline indicators, India/state comparison and direct syllabus linkage (health, gender, jobs, climate, food safety).",
        "skip": "Do not read all tables or prepare every indicator; promote to must-read only when a major release, policy or PYQ trend makes it salient.",
        "url": "https://pib.gov.in/",
    },
]

STUDY_RESOURCES = {
    "official-syllabus": {
        "name": "Supplied RBI Grade B 2025 Phase II syllabus",
        "url": "../PYP/Latest-RBI-Grade-B-Syllabus-2025-Official-PDF.pdf",
        "kind": "Start here",
        "use": "Use it as the boundary checklist for ESI, Finance/Management and English writing. It is Phase II only; verify the 2027 notification before relying on it.",
    },
    "rbi": {
        "name": "Reserve Bank of India — notifications, FAQs, speeches and publications",
        "url": "https://www.rbi.org.in/",
        "kind": "Primary source",
        "use": "First stop for monetary policy, regulation, banking, payments, inclusion, financial stability, RBI reports and verified policy status.",
    },
    "rbi-bulletin": {
        "name": "RBI Bulletin archive",
        "url": "https://www.rbi.org.in/Scripts/BS_ViewBulletin.aspx",
        "kind": "Primary source",
        "use": "Read the latest MPC resolution, Governor's statement, Monetary Policy Report and short RBI articles; use the archive rather than old copied summaries.",
    },
    "rbi-fsr": {
        "name": "RBI Financial Stability Reports",
        "url": "https://www.rbi.org.in/Scripts/FsReports.aspx",
        "kind": "Primary source",
        "use": "For systemic risk, banks/NBFCs, asset quality, stress tests, cyber and payment resilience. Read summary/key charts, not every model detail.",
    },
    "pib": {
        "name": "Press Information Bureau (PIB)",
        "url": "https://pib.gov.in/",
        "kind": "Primary source",
        "use": "Search the issuing ministry and original release for scheme launches, Cabinet decisions, targets, extensions and official statements. Verify dates and figures at the ministry source.",
    },
    "myscheme": {
        "name": "myScheme — Government scheme discovery",
        "url": "https://www.myscheme.gov.in/",
        "kind": "Primary source / discovery",
        "use": "Find scheme purpose and eligibility by ministry/category; follow through to the implementing ministry's current guidelines for authoritative details.",
    },
    "budget": {
        "name": "Union Budget portal",
        "url": "https://www.indiabudget.gov.in/",
        "kind": "Primary source",
        "use": "Use Budget at a Glance, speech, receipts/expenditure and scheme documents. Compare Budget Estimates, Revised Estimates and actuals correctly.",
    },
    "survey": {
        "name": "Economic Survey",
        "url": "https://www.indiabudget.gov.in/economicsurvey/",
        "kind": "Primary source",
        "use": "Read overview and syllabus-relevant chapters for growth, employment, agriculture, industry, external sector and public finance; extract only a few dated indicators and implications.",
    },
    "mospi": {
        "name": "Ministry of Statistics and Programme Implementation",
        "url": "https://mospi.gov.in/",
        "kind": "Primary source",
        "use": "For national accounts, CPI/IIP, PLFS and official statistical releases. Record the series, reference period, unit and release date with each figure.",
    },
    "niti": {
        "name": "NITI Aayog",
        "url": "https://www.niti.gov.in/",
        "kind": "Primary source",
        "use": "For SDG/state indices, development initiatives and official policy documents; focus on the edition, dimensions, India/state comparison and methodology.",
    },
    "ncert": {
        "name": "NCERT / ePathshala textbooks",
        "url": "https://epathshala.nic.in/",
        "kind": "Static foundation",
        "use": "Select Class XI Indian Economic Development and Class XII Introductory Macroeconomics for ESI/economy foundations. Use only syllabus-relevant chapters; do not read every NCERT subject.",
    },
    "egyankosh": {
        "name": "IGNOU eGyanKosh",
        "url": "https://egyankosh.ac.in/",
        "kind": "Static foundation",
        "use": "Search its repository for introductory management, organisational behaviour, communication and business-ethics material. Treat it as a reference, not a second full course.",
    },
    "imf": {
        "name": "IMF World Economic Outlook",
        "url": "https://www.imf.org/en/Publications/WEO",
        "kind": "Primary source",
        "use": "For global/India outlook, forecast changes and risks. Always note the edition/date; compare direction and drivers, not a long country table.",
    },
    "worldbank": {
        "name": "World Bank Global Findex",
        "url": "https://www.worldbank.org/en/publication/globalfindex",
        "kind": "Primary source",
        "use": "For financial access, use, digital payments and inclusion gaps; pair global findings with RBI's India-specific Financial Inclusion Index.",
    },
    "wto": {
        "name": "World Trade Organization",
        "url": "https://www.wto.org/",
        "kind": "Primary source",
        "use": "For trade rules, dispute/institution basics and official trade developments relevant to globalization and India's external sector.",
    },
    "commerce": {
        "name": "Department of Commerce, Government of India",
        "url": "https://commerce.gov.in/",
        "kind": "Primary source",
        "use": "For India's trade policy, bilateral/regional agreements and official agreement status. Distinguish negotiation, signing, ratification and entry into force.",
    },
    "imd": {
        "name": "India Meteorological Department",
        "url": "https://mausam.imd.gov.in/",
        "kind": "Primary source",
        "use": "For rainfall, monsoon, cyclone and weather releases; distinguish the measured weather fact from its possible agricultural/economic impact.",
    },
    "moefcc": {
        "name": "Ministry of Environment, Forest and Climate Change",
        "url": "https://moef.gov.in/",
        "kind": "Primary source",
        "use": "For Indian environment, biodiversity, climate policy and official programme details; use UNFCCC/Convention sources for treaty facts.",
    },
    "indiaai": {
        "name": "IndiaAI Mission",
        "url": "https://indiaai.gov.in/",
        "kind": "Primary source",
        "use": "For India's AI programmes and ecosystem. Cross-check policy, compute, skilling and governance claims against MeitY/official releases.",
    },
    "meity": {
        "name": "Ministry of Electronics and Information Technology",
        "url": "https://www.meity.gov.in/",
        "kind": "Primary source",
        "use": "For digital public infrastructure, electronics/semiconductor policy, cybersecurity and ministry-issued technology programmes.",
    },
    "nism": {
        "name": "NISM learning and certification resources",
        "url": "https://www.nism.ac.in/certifications/",
        "kind": "Targeted reference",
        "use": "Use the relevant securities-market, mutual-fund, depository or derivatives workbook only for syllabus basics; certification-level depth is not required.",
    },
    "sebi": {
        "name": "Securities and Exchange Board of India",
        "url": "https://www.sebi.gov.in/",
        "kind": "Primary source",
        "use": "For market regulations, investor protection, instruments, recent circulars and official securities-market explanations.",
    },
    "pyp25": {
        "name": "Supplied 2025 memory-based compilation (Phase I + II)",
        "url": "../PYP/2025%20(Phase%201-2).pdf",
        "kind": "Timed practice",
        "use": "Use for timed practice and error analysis—not as a verified official paper or answer-key authority. Its Phase I compilation is incomplete; the other supplied years are in the PYP folder.",
    },
    "pyp26": {
        "name": "Supplied 2026 Phase I paper",
        "url": "../PYP/2026%20(Phase%201).pdf",
        "kind": "Timed practice",
        "use": "Use for recent Phase I practice only; it is a memory-based compilation, not an official paper. No 2026 Phase II paper was supplied.",
    },
    "quant-book": {
        "name": "Quantitative Aptitude for Competitive Examinations — R.S. Aggarwal",
        "url": "",
        "kind": "Optional practice book",
        "use": "Use selected arithmetic, number-series and DI exercises to build speed; stop adding books once you have a representative question set and mocks.",
    },
    "reasoning-book": {
        "name": "Analytical Reasoning — M.K. Pandey",
        "url": "",
        "kind": "Optional practice book",
        "use": "Use selected chapters for arrangement, deduction and critical-reasoning methods; timed mocks and error review matter more than completing the whole book.",
    },
    "english-book": {
        "name": "Oxford Practice Grammar — John Eastwood",
        "url": "",
        "kind": "Optional reference",
        "use": "Use it to resolve repeated grammar errors, not as a cover-to-cover course. Pair it with daily reading and timed practice.",
    },
    "newspaper": {
        "name": "Choose one quality English newspaper",
        "url": "",
        "kind": "Daily reading",
        "use": "Read one editorial/explainer for comprehension, argument structure and context. Verify exam facts separately with official releases; do not make a second full current-affairs source stack.",
    },
    "english-writing": {
        "name": "Your own timed answer practice + RBI syllabus",
        "url": "../PYP/Latest-RBI-Grade-B-Syllabus-2025-Official-PDF.pdf",
        "kind": "Practice method",
        "use": "Write timed essays, précis and comprehension responses; use the guide's rubric and relevant official reports/current affairs as evidence. There is no substitute for repeated writing and review.",
    },
}

PHASE_ONE_SOURCE_MAP = {
    "General Awareness": {
        "RBI, monetary system and regulation": ["rbi", "rbi-bulletin"],
        "Banking and financial system": ["rbi", "rbi-fsr", "rbi-bulletin"],
        "Government schemes and policies": ["pib", "myscheme", "budget"],
        "International affairs and institutions": ["imf", "worldbank", "wto", "commerce"],
        "Reports, indices and surveys": ["survey", "mospi", "niti", "imf"],
        "Indian economy and public finance": ["survey", "budget", "mospi"],
        "Science, technology and AI": ["indiaai", "meity", "pib"],
        "Environment and sustainable development": ["imd", "moefcc", "pib"],
        "Sports, culture and general knowledge": ["pib", "niti"],
        "Other / unclassified": ["pib", "rbi", "myscheme", "survey", "mospi"],
    },
    "Quantitative Aptitude": {
        "Arithmetic": ["quant-book", "pyp25", "pyp26"],
        "Number systems and sequences": ["quant-book", "pyp25", "pyp26"],
        "Data interpretation": ["quant-book", "mospi", "pyp25", "pyp26"],
        "Algebra and equations": ["quant-book", "pyp25", "pyp26"],
        "Geometry and mensuration": ["quant-book", "pyp25", "pyp26"],
        "Unclassified / mixed": ["pyp25", "pyp26"],
    },
    "Reasoning": {
        "Puzzles and seating arrangements": ["reasoning-book", "pyp25", "pyp26"],
        "Syllogisms and deductions": ["reasoning-book", "pyp25", "pyp26"],
        "Other / mixed reasoning": ["reasoning-book", "pyp25", "pyp26"],
        "Coding and input-output": ["reasoning-book", "pyp25", "pyp26"],
        "Logical and critical reasoning": ["reasoning-book", "pyp25", "pyp26"],
    },
    "English": {
        "Reading comprehension": ["newspaper", "pyp25", "pyp26"],
        "Grammar and sentence correction": ["english-book", "pyp25", "pyp26"],
        "Vocabulary and usage": ["newspaper", "pyp25", "pyp26"],
        "Sentence arrangement": ["newspaper", "pyp25", "pyp26"],
        "Cloze / fillers": ["english-book", "pyp25", "pyp26"],
        "Other / unresolved": ["english-book", "newspaper", "pyp25", "pyp26"],
    },
}

PHASE_TWO_SOURCE_MAP = {
    "Growth and Development": ["official-syllabus", "ncert", "survey", "mospi", "pib"],
    "Indian Economy": ["official-syllabus", "ncert", "survey", "budget", "rbi-bulletin", "mospi"],
    "Globalization": ["official-syllabus", "imf", "wto", "commerce", "rbi-bulletin"],
    "Social Structure in India": ["official-syllabus", "ncert", "mospi", "niti", "pib"],
    "Unclassified / mixed ESI tags": ["official-syllabus", "pyp25", "pib", "myscheme", "survey"],
    "Financial System": ["official-syllabus", "rbi", "rbi-bulletin", "rbi-fsr"],
    "Financial Markets": ["official-syllabus", "nism", "sebi", "rbi-bulletin"],
    "Financial Risk Management + Accounting and Financial Statements": ["official-syllabus", "rbi-fsr", "nism"],
    "Basics of Derivatives": ["official-syllabus", "nism", "sebi"],
    "Global Financial Markets and International Banking": ["official-syllabus", "imf", "rbi-bulletin", "rbi-fsr"],
    "Financial Inclusion": ["official-syllabus", "rbi", "worldbank", "pib"],
    "Alternate Sources of Finance": ["official-syllabus", "budget", "nism"],
    "Union Budget + Inflation (joint tag)": ["official-syllabus", "budget", "survey", "rbi-bulletin", "mospi"],
    "Fundamentals of Management and Organizational Behaviour": ["official-syllabus", "egyankosh"],
    "Banking Corporate Governance + Workplace Ethics (joint tag)": ["official-syllabus", "egyankosh", "rbi-fsr"],
    "Unclassified / mixed Finance and Management tags": ["official-syllabus", "pyp25", "rbi", "nism", "egyankosh"],
    "Communication": ["official-syllabus", "egyankosh"],
    "English Writing Skills": ["official-syllabus", "english-writing", "pyp25"],
    "Unresolved descriptive-English markers": ["official-syllabus", "english-writing", "pyp25"],
}

PHASE_ONE_GUIDE = {
    "General Awareness": {
        "target": "48 / 80 correct minimum; practise toward 55–58",
        "priority": "Very high",
        "forecast": "Current affairs plus RBI, banking, government programmes and reports are the safest recurring basket. International affairs and technology deserve more attention after the 2026 compilation. GA is also the fact bank for Phase II ESI/FM examples.",
        "practice": "Build short fact cards: institution / ministry, mandate, launch or report year, target group, latest figure, and one policy implication. Revise the most recent 12–15 months before the exam, then add static background. Reuse each card as a dated Phase II example.",
        "topics": [
            ("RBI, monetary system and regulation", "52 / 400", "Very high", "RBI functions and instruments; monetary-policy decisions; liquidity, payments, regulation, financial stability and consumer protection. Link each new circular to the institution and problem it addresses."),
            ("Banking and financial system", "69 / 400", "Very high", "Banking regulators and institutions; NBFCs; payment systems; inclusion; financial products; important banking-sector reports and changes."),
            ("Government schemes and policies", "79 / 400", "Very high", "Purpose, nodal ministry, beneficiary, delivery channel, eligibility, funding or recent expansion. Prioritise schemes tied to jobs, agriculture, health, education, women and inclusion."),
            ("International affairs and institutions", "38 / 400", "High; rising in 2026", "IMF, World Bank, WTO, UN and regional groupings; membership, mandate, reports, summit outcomes, trade and geopolitical developments affecting India."),
            ("Reports, indices and surveys", "25 / 400", "High", "Publisher, coverage, methodology headline, India's rank or score, top performers and the policy issue measured. Connect the Economic Survey and RBI publications to ESI/FM."),
            ("Indian economy and public finance", "20 / 400", "High", "GDP, inflation, employment, fiscal indicators, trade, agriculture and budget basics; know direction, period and source of a current statistic."),
            ("Science, technology and AI", "10 / 400", "High and rising", "India's AI ecosystem, digital public infrastructure, semiconductors, cyber risks, space and science missions; focus on institution, application, governance and economic/social impact."),
            ("Environment and sustainable development", "7 / 400", "Medium-high", "Climate agreements, extreme weather, energy transition, biodiversity and Indian programmes; connect climate shocks to agriculture, food inflation and livelihoods."),
            ("Sports, culture and general knowledge", "30 / 400", "Selective but retain", "Major international and Indian awards, tournaments, host venues, records, heritage and notable appointments. Use spaced revision rather than broad random trivia."),
            ("Other / unclassified", "70 / 400", "Coverage safeguard", "A large mixed-current-affairs bucket remains broad or unclassified. Preserve coverage across RBI, government, economy, international, science and general awareness; do not treat this as one study chapter."),
        ],
    },
    "Quantitative Aptitude": {
        "target": "18 / 30 correct minimum; practise toward 21–23",
        "priority": "Very high for controllable marks",
        "forecast": "Arithmetic was the strongest identifiable recurring tag in all six searchable cycles (2024 has one missing marker). Data interpretation, algebra and geometry appear less often in the automatic tags, but cannot be safely skipped.",
        "practice": "One timed mixed set most days; keep an error log by concept, setup, calculation and time-pressure error. Re-solve missed items after 48 hours and one week. Optimise net marks and accuracy, not attempted volume.",
        "topics": [
            ("Arithmetic", "92 / 179 observed", "Core", "Percentages, ratios, averages, profit/loss, interest, time/work, speed/distance, mixtures and partnerships. Convert each item into variables/equations before calculating; drill multi-step word problems."),
            ("Number systems and sequences", "33 / 179 observed", "High", "Number properties, divisibility/remainders, missing or wrong-term sequences and pattern identification. Practise fast recognition, but verify the rule across the whole sequence."),
            ("Data interpretation", "9 / 179 observed", "High leverage despite low tag count", "Tables, charts, caselets, percentage change, ratio and weighted averages. The marker-level tags can miss a shared data set, so this count is not a reliable measure of actual DI weight."),
            ("Algebra and equations", "7 / 179 observed", "Selective core", "Linear/quadratic relationships and equation-based word problems. Keep standard identities and root relationships fluent."),
            ("Geometry and mensuration", "4 / 179 observed", "Selective coverage", "Common area, perimeter, volume and shape relationships. Cover formula basics and representative timed problems; do not spend disproportionate time on rare variants."),
            ("Unclassified / mixed", "34 / 179 observed", "Review source-pattern", "Question-level automatic labels do not resolve these markers. Mixed mocks and the original source layout are necessary; do not interpret this as one mathematical chapter."),
        ],
    },
    "Reasoning": {
        "target": "36 / 60 correct minimum; practise toward 42–45",
        "priority": "Very high",
        "forecast": "Puzzles/seating and syllogism/deduction tags recur. Their annual counts swing sharply, and 125 of 300 clean-cycle markers remain in a broad automatic 'other' bucket. Practise the full mix.",
        "practice": "Use timed sets, learn to abandon a slow set early, and protect easy standalone marks. Track accuracy and time separately for each set type; redo failed puzzle diagrams from scratch.",
        "topics": [
            ("Puzzles and seating arrangements", "98 / 300 observed", "Core", "Linear/circular seating, floors, scheduling, comparison and multi-attribute arrangements. Practise translating every condition into a clean grid/diagram and testing cases systematically."),
            ("Syllogisms and deductions", "67 / 300 observed", "Core", "Venn/possibility logic, conclusions, statement-based deductions and—in mixed papers—inequalities. Distinguish definite from possible conclusions; avoid importing outside assumptions."),
            ("Other / mixed reasoning", "125 / 300 observed", "Do not omit", "Automatic tags missed many identifiable forms. Cover direction/distance, blood relations, order/ranking, coding-decoding, input-output, alphanumeric series, data sufficiency and critical reasoning through timed mixed sets."),
            ("Coding and input-output", "3 / 300 observed", "Selective coverage", "Coding-decoding and input-output patterns. Learn a repeatable rule-identification approach and avoid overinvesting in rare bespoke formats."),
            ("Logical and critical reasoning", "7 / 300 observed", "Selective, high accuracy", "Assumptions, inference, strengthen/weaken and argument logic. Treat the text as the complete evidence set; don't solve from personal beliefs."),
        ],
    },
    "English": {
        "target": "18 / 30 correct minimum; practise toward 21–23",
        "priority": "High; improve predictability through daily practice",
        "forecast": "Reading comprehension, grammar and vocabulary recur, but the topic classifier leaves 63 of 146 observed clean-cycle markers unclassified. The 2025 compilation is incomplete; do not interpret missing tags as a real decline.",
        "practice": "Daily reading plus a short grammar/vocabulary set; practise passage accuracy and answer evidence location. Keep a personal error list for grammar rules and recurring word usage.",
        "topics": [
            ("Reading comprehension", "32 / 146 observed", "Core", "Main idea, inference, tone, vocabulary-in-context and detail retrieval. Answer from passage evidence, not assumed outside knowledge."),
            ("Grammar and sentence correction", "25 / 146 observed", "Core", "Agreement, tense, modifiers, parallelism, articles/prepositions and error identification. Diagnose the rule before selecting a correction."),
            ("Vocabulary and usage", "15 / 146 observed", "High", "Contextual meaning, synonym/antonym, collocation and word usage. Review in context with spaced repetition rather than isolated giant lists."),
            ("Sentence arrangement", "7 / 146 observed", "Selective coverage", "Logical sequence, cohesion, pronoun/reference links, transitions and paragraph flow."),
            ("Cloze / fillers", "4 / 146 observed", "Selective coverage", "Grammar plus local and paragraph context. Use elimination and check fit for meaning and syntax."),
            ("Other / unresolved", "63 / 146 observed", "Maintain broad practice", "The keyword rules leave many records unresolved; this is a classification limitation, not evidence that these formats are absent."),
        ],
    },
}

PHASE_TWO_GUIDE = [
    {
        "subject": "ESI",
        "chapter": "Growth and Development",
        "tags": ["Growth and Development", "Sustainable Development and Environment"],
        "priority": "Very high",
        "confidence": "Medium-high",
        "forecast": "A broad recurring area; environment/sustainability tags rose in the last two supplied cycles. High 2027 relevance because it joins static syllabus concepts to jobs, climate and current data.",
        "asked": "Expect concept + application: how growth is measured; poverty, employment and inclusion; whether a policy meets a development objective; and how environmental constraints affect growth and livelihoods.",
        "subtopics": "Growth measurement; poverty alleviation; employment generation; sustainable development; environmental issues.",
        "minimum": "Prepare definitions and indicators, current India figures with source/year, policy tools and one balanced 150–250 word analytical outline for poverty/jobs and climate-growth trade-offs.",
    },
    {
        "subject": "ESI",
        "chapter": "Indian Economy",
        "tags": ["Indian Economy"],
        "priority": "Very high",
        "confidence": "Medium",
        "forecast": "A steady, persistent tag rather than a spike. Budget, Economic Survey, RBI policy and agriculture/manufacturing current affairs keep it central for 2027.",
        "asked": "Questions connect policy and outcomes: monetary/fiscal measures, public finance, banking/RBI's development role, agriculture, industry and services. Be able to explain a mechanism, not just quote a headline.",
        "subtopics": "Economic history; industrial and labour policy; monetary/fiscal policy since 1991; Economic Survey and Union Budget; money/financial markets; banks and RBI in development; public finance; political economy; industry; agriculture; services.",
        "minimum": "Build one-page maps for monetary vs fiscal policy, the 1991 reforms and sectoral structure. Extract only headline indicators and 3–5 policy implications from the latest Economic Survey/Budget.",
    },
    {
        "subject": "ESI",
        "chapter": "Globalization",
        "tags": ["Globalization and International Economic Issues"],
        "priority": "High",
        "confidence": "Medium",
        "forecast": "The tag persisted in all five cycles but at modest counts. 2026 trade/geopolitical uncertainty and India–EU trade talks increase current-affairs linkage.",
        "asked": "Trade and balance-of-payments concepts; how external shocks, institutions or regional agreements affect India; role/mandate of IMF, World Bank and WTO.",
        "subtopics": "Opening of the economy; balance of payments; export-import policy; IMF, World Bank, WTO; regional cooperation; international economic issues.",
        "minimum": "Know current-account vs capital/financial-account logic, trade balance vs BoP, exchange-rate channels, WTO basics, IMF/World Bank roles, and the verified status—not just expected timeline—of major trade agreements.",
    },
    {
        "subject": "ESI",
        "chapter": "Social Structure in India",
        "tags": ["Social Structure in India"],
        "priority": "High",
        "confidence": "Medium-low (small counts)",
        "forecast": "Small but present in every cycle; 2025 had a relative spike. Current jobs, migration, gender and demographic change can produce applied questions.",
        "asked": "Interpret social indicators or connect a policy to gender, migration, urbanisation, social justice and inclusion; avoid treating social topics as definitions alone.",
        "subtopics": "Multiculturalism; demographic trends; urbanisation and migration; gender; social justice.",
        "minimum": "Make compact notes on population/demographic dividend, labour-force participation, migration/urbanisation and gender inequality; pair each with one current indicator and one policy response.",
    },
    {
        "subject": "ESI",
        "chapter": "Unclassified / mixed ESI tags",
        "tags": ["Economic and Social Issues: other/uncategorized"],
        "priority": "Coverage safeguard",
        "confidence": "High that the bucket is large; no chapter inference",
        "forecast": "79 of 180 indexed markers remain in the broad tag. Source-page review shows many are not truly unstructured: they are shared-context sets on schemes, benefits, regulation, reports and policy facts, plus some uncategorised descriptive topics.",
        "asked": "Recognise an initiative from a passage; match scheme to objective/beneficiary; test eligibility, amounts, tenure, extension, implementing law or regulator; interpret a report/indicator or link policy to a group/state. Descriptive prompts span reform, disinvestment, entrepreneurship and applied policy.",
        "subtopics": "Mixed across Growth/Development, Indian Economy, Globalization and Social Structure; especially welfare and social-security schemes, agriculture, housing, health, education, labour, rural development, financial inclusion, trade and report-based indicators.",
        "minimum": "Prepare one crosswalk for scheme/policy → objective → beneficiary → design → measured outcome; keep a compact scheme/fact bank and core coverage of all four ESI chapters. For descriptive answers, practice mechanism + evidence + trade-off, not lists.",
    },
    {
        "subject": "Finance",
        "chapter": "Financial System",
        "tags": ["Financial System and Banking"],
        "priority": "Very high",
        "confidence": "High for broad chapter",
        "forecast": "Broad banking/system tags increased to 13 of 30 objective markers in the 2025 compilation and are the strongest identified Finance theme. RBI regulation, inclusion, digital payments and cyber-resilience make it a leading 2027 bet.",
        "asked": "Institution/function/regulator matching; how banks, NBFCs and payment systems work; RBI's role; development-finance institutions; digital payment/inclusion mechanisms; policy application.",
        "subtopics": "RBI and banking system; SIDBI, EXIM Bank, NABARD, NHB, NaBFID; non-bank system; global system developments; IT in banking; digital payments.",
        "minimum": "Create a regulator/institution matrix (mandate, regulated entities, core tool); understand bank balance-sheet basics, NBFC distinctions, payment rails, inclusion, fraud controls and current RBI rules.",
    },
    {
        "subject": "Finance",
        "chapter": "Financial Markets",
        "tags": ["Financial Markets and Instruments"],
        "priority": "High",
        "confidence": "Medium",
        "forecast": "A smaller but stable tag, with a 2024 bump. Budget 2026 market-making and bond-market measures make this a current-affairs bridge.",
        "asked": "Market purpose and participants; primary vs secondary; money, bond, equity and forex markets; instrument features and how changes in rates/expectations affect prices.",
        "subtopics": "Primary/secondary markets; forex, money, bond and equity markets; functions; instruments; recent developments.",
        "minimum": "Compare market segments, instruments, issuer/investor and risk; know bond-price/yield direction, basic forex concepts, and current market-development facts from primary sources.",
    },
    {
        "subject": "Finance",
        "chapter": "Financial Risk Management + Accounting and Financial Statements",
        "tags": ["Risk, Accounting and Financial Analysis"],
        "priority": "High core; chapter-level count is joint",
        "confidence": "Medium-low",
        "forecast": "The automatic tag is smaller and volatile, but the syllabus explicitly includes both areas and current cybersecurity/operational risk strengthens application relevance. No defensible separate count for risk vs accounting.",
        "asked": "Likely concept identification or applied interpretation: risk type/control; what a ratio or statement signals; how an event changes liquidity, profitability, leverage or solvency.",
        "subtopics": "Risk-management concepts; balance sheet; profit/loss; cash flow; ratio analysis.",
        "minimum": "Prepare statement structure and a small set of liquidity, leverage, profitability and efficiency ratios; learn what each means and limitations. Cover credit, market, liquidity and operational/cyber risk plus mitigation.",
    },
    {
        "subject": "Finance",
        "chapter": "Basics of Derivatives",
        "tags": [],
        "priority": "Core syllabus coverage",
        "confidence": "No separate count",
        "forecast": "A separate frequency cannot be isolated by the current broad tags. Keep the basics: derivatives are a named syllabus chapter and market-risk events make them relevant.",
        "asked": "Instrument purpose, underlying, buyer/seller obligations, hedging/speculation, payoff direction and basic futures/options/forward/swap distinctions.",
        "subtopics": "General topics in basics of derivatives.",
        "minimum": "Know contract types, long/short exposure, call/put rights, intrinsic payoff at expiry and hedging purpose. Avoid advanced pricing math unless mocks demand it.",
    },
    {
        "subject": "Finance",
        "chapter": "Global Financial Markets and International Banking",
        "tags": [],
        "priority": "High current-affairs overlay",
        "confidence": "No separate count",
        "forecast": "No separate historical tag; global conflict, trade/energy shocks, FX exposure and BRICS cross-border payment discussions make it a strong watchlist rather than a count-backed recurrence claim.",
        "asked": "Understand transmission from global rates, exchange rates, sanctions, capital flows and cross-border banking to domestic stability and policy.",
        "subtopics": "Broad trends and latest developments in global markets and international banking.",
        "minimum": "Maintain a one-page global dashboard: IMF outlook, major central-bank direction, oil/energy shock, FX/capital-flow channel, international banking risk and verified cross-border payment initiatives.",
    },
    {
        "subject": "Finance",
        "chapter": "Financial Inclusion",
        "tags": [],
        "priority": "Very high current-affairs overlay",
        "confidence": "No separate count",
        "forecast": "Not independently tagged in the current rule set, but the RBI FI-Index and usage-led inclusion story directly match the official chapter and recur across GA/ESI/finance.",
        "asked": "Access vs usage vs quality; barriers, policy design, digital access and whether inclusion is meaningful and safe—not account-opening alone.",
        "subtopics": "Financial inclusion.",
        "minimum": "Know FI-Index dimensions and latest verified release; link Jan-Dhan, digital public infrastructure, SHGs/microfinance, consumer protection, literacy, gender/rural access and cyber safety.",
    },
    {
        "subject": "Finance",
        "chapter": "Alternate Sources of Finance",
        "tags": [],
        "priority": "Selective core",
        "confidence": "No separate count",
        "forecast": "No independent frequency. Budget/public-infrastructure financing keeps PPP and risk-sharing relevant; cover basics without letting it displace high-return banking/accounting work.",
        "asked": "Compare public/private financing, risk allocation, value-for-money and social versus private costs/benefits.",
        "subtopics": "Private/social cost-benefit; public-private partnership.",
        "minimum": "Know PPP rationale, common risk-allocation principles, contingent liabilities and why project appraisal includes external/social benefits.",
    },
    {
        "subject": "Finance",
        "chapter": "Union Budget + Inflation (joint tag)",
        "tags": ["Inflation, Budget and Public Finance"],
        "priority": "Very high static + current priority",
        "confidence": "Low separate count; one joint tag",
        "forecast": "Only five joint inflation/budget/public-finance tags; count cannot be split between the two chapters. Both remain high-value static and annual current-affairs areas.",
        "asked": "Interpret fiscal receipts/expenditure, deficit and financing, capex versus revenue expenditure, CPI/WPI, inflation drivers, RBI response and growth/inflation trade-offs.",
        "subtopics": "Union Budget: concepts, approach and broad trends. Inflation: definition, trends, estimates, consequences/remedies, WPI/CPI and monetary/fiscal balance between inflation and growth.",
        "minimum": "Read the Budget at a glance and speech; capture verified deficit/debt, capex and fiscal-policy implications. Separately master CPI vs WPI, demand/cost drivers, policy transmission, expectations and distributional impacts.",
    },
    {
        "subject": "Management",
        "chapter": "Fundamentals of Management and Organizational Behaviour",
        "tags": ["Management and Organizational Behaviour"],
        "priority": "Very high",
        "confidence": "Medium-high",
        "forecast": "The largest identified FM/management theme after banking: 37 tags across objective and descriptive sections. Recurs every year, although the objective-tag count has eased in the last two.",
        "asked": "Recognise theory/thinker and apply it to a workplace situation; motivation, leadership, personality, perception, reinforcement, conflict, change and group behaviour.",
        "subtopics": "Management thought/functions/roles; nudge; personality; reinforcement; perception; motivation; leadership; emotional intelligence; relationships; conflict; change/development.",
        "minimum": "Make a one-line theory → key idea → workplace application → limitation card for each named model/thinker; use scenario drills rather than memorising names alone.",
    },
    {
        "subject": "Finance / Management",
        "chapter": "Banking Corporate Governance + Workplace Ethics (joint tag)",
        "tags": ["Ethics and Corporate Governance"],
        "priority": "High syllabus coverage",
        "confidence": "Low-medium (combined tag)",
        "forecast": "Sparse automatic tag, but explicitly named syllabus content and highly applicable to banking, AI/data and cyber governance.",
        "asked": "Ethical principle/theory recognition; conflict-of-interest and accountability; codes, board structures and governance mechanisms in a scenario.",
        "subtopics": "Finance: corporate governance in banking. Management: ethical theories/principles; business ethics; organisation structure; boards; ethics programmes/codes; governance factors/mechanisms.",
        "minimum": "Compare major ethical approaches in plain language; practise stakeholder, duty, consequence, fairness and transparency analysis; link to board, audit and controls.",
    },
    {
        "subject": "Finance",
        "chapter": "Unclassified / mixed Finance and Management tags",
        "tags": ["Finance and Management: other/uncategorized"],
        "priority": "Coverage safeguard",
        "confidence": "High that the bucket is large; no chapter inference",
        "forecast": "49 of 180 markers remain broad/unclassified. Source-page review shows this bucket mixes missed Finance chapters, management applications and passage-linked current affairs; it is not a low-priority chapter.",
        "asked": "Recall a regulator/instrument/threshold, compare a product or market feature, read a basic financial statement, identify a management theory in a scenario, or connect a current policy passage to a financial rule.",
        "subtopics": "Mixed across markets/instruments, banking/regulation, budget/public finance, financial statements, inclusion and management/OB; examples include CSR thresholds, commercial paper, depositories, IPO/SEBI rules, UPI/payment systems, scheme-linked finance and behavioral theory.",
        "minimum": "Use a rotating mixed set across every named syllabus chapter. Make compact comparison cards (instrument, issuer, maturity, regulator, risk) and theory → scenario cards; do not let unclassified counts displace syllabus coverage.",
    },
    {
        "subject": "Management",
        "chapter": "Communication",
        "tags": ["Communication and Interpersonal Relations"],
        "priority": "Medium-high",
        "confidence": "Medium-low",
        "forecast": "Communication tags appear in four cycles but trend lower in the latest two; retain concise coverage of barriers, channels and direction.",
        "asked": "Choose an appropriate channel/direction, identify a barrier or communication failure, and distinguish verbal/non-verbal or formal/informal communication.",
        "subtopics": "Communication process/channels; oral/written; verbal/non-verbal; upward/downward/lateral; barriers; IT.",
        "minimum": "Know the communication process, channel fit, feedback, noise/barriers and directional flows; practise short scenario identification.",
    },
    {
        "subject": "English Writing Skills",
        "chapter": "English Writing Skills",
        "tags": ["Essay writing", "Precis writing", "Reading comprehension"],
        "priority": "Very high score lever",
        "confidence": "High for format recurrence",
        "forecast": "Each 2021–2025 compilation lists the same three task types. This is format recurrence, not a prediction of the exact 2027 prompts.",
        "asked": "Clear understanding of a prompt or passage; concise précis preserving central argument; structured essay with relevant evidence, balance and conclusion.",
        "subtopics": "Expression and understanding of topic; essay, précis, comprehension.",
        "minimum": "Write one timed essay and one précis weekly, plus a short comprehension response. Score for relevance, structure, coherence, grammar, precision and time control.",
    },
    {
        "subject": "English Writing Skills",
        "chapter": "Unresolved descriptive-English markers",
        "tags": ["Descriptive English: other/uncategorized"],
        "priority": "Coverage safeguard",
        "confidence": "Low; two markers unresolved",
        "forecast": "Two of 15 indexed descriptive tasks were not assigned to a distinct format by the keyword rules.",
        "asked": "No reliable format-specific ask can be inferred for these markers.",
        "subtopics": "Unresolved among the supplied descriptive English task markers.",
        "minimum": "Practise all three recurring formats and use timed mocks to diagnose other writing or comprehension requirements.",
    },
]

CURRENT_AFFAIRS = [
    {
        "date": "Jan–Jul 2026",
        "topic": "Global growth, inflation, technology investment and geopolitical/energy shocks",
        "evidence": "IMF's January WEO update projected global growth of 3.3% in 2026 and 3.2% in 2027. Its July update described cross-currents of war and technology, with 3.0% and 3.4% projections; the releases are different vintages, not interchangeable facts.",
        "map": "ESI: Globalization, Indian Economy, Growth & Development · FM: global markets, inflation, markets · GA: IMF, outlook, energy/trade",
        "study": "Compare forecast revisions, drivers and downside risks; explain the energy-import, inflation, exchange-rate and capital-flow transmission to India. Cite the vintage/date with every forecast.",
        "priority": "Very high",
        "source": "IMF WEO January 2026",
        "url": "https://www.imf.org/en/Publications/WEO/Issues/2026/01/19/world-economic-outlook-update-january-2026",
        "source2": "IMF WEO July 2026",
        "url2": "https://www.imf.org/en/Publications/WEO/Issues/2026/07/08/world-economic-outlook-update-july-2026",
    },
    {
        "date": "Jan 2026",
        "topic": "Economic Survey 2025–26: growth, inflation, fiscal consolidation, agriculture, banking, external resilience",
        "evidence": "A secondary summary reports FY26 real GDP growth estimate of 7.4%, FY27 range of 6.8–7.2%, and April–December 2025 CPI inflation of 1.7%. Treat these as provisional study leads and verify every figure, base/period and revision in the official Survey.",
        "map": "ESI: Growth, Indian Economy, employment/agriculture · FM: inflation, budget, financial system · GA: reports, indices, economy",
        "study": "Prioritise the Survey's official narrative and selected headline indicators: growth composition, consumption/investment, fiscal quality, employment, agriculture, inflation and external buffers. Avoid memorising long statistic lists.",
        "priority": "Very high",
        "source": "Economic Survey 2025–26 explainer (secondary)",
        "url": "https://www.insightsonindia.com/2026/01/30/economic-survey-2025-26-complete-highlights-and-summary-for-upsc/",
        "source2": "Official Union Budget / Survey portal",
        "url2": "https://www.indiabudget.gov.in/",
    },
    {
        "date": "Feb 2026",
        "topic": "Union Budget 2026–27: public capex, banking-sector review, markets, AI/semiconductors and infrastructure",
        "evidence": "A secondary Budget explainer reports ₹12.2 lakh crore public capex, a high-level banking committee, bond-market measures and targeted manufacturing/technology initiatives. Confirm amounts, scheme names and fiscal numbers in the Budget speech and official documents before using them.",
        "map": "ESI: fiscal policy, public finance, industry/jobs · FM: Union Budget, markets, financial system, alternate finance · GA: schemes, economy, AI/tech",
        "study": "Prepare fiscal deficit/debt and capex distinction, the financing and growth rationale, banking reform objectives, bond-market design and the AI/semiconductor industrial-policy rationale.",
        "priority": "Very high",
        "source": "Union Budget 2026–27 explainer (secondary)",
        "url": "https://www.insightsonindia.com/2026/02/01/union-budget-2026-27-highlights-upsc/",
        "source2": "Official India Budget portal",
        "url2": "https://www.indiabudget.gov.in/",
    },
    {
        "date": "Feb 2026",
        "topic": "India AI Impact Summit and the New Delhi Declaration: trusted AI, access, human capital and social/economic benefit",
        "evidence": "News18 reports a voluntary, non-binding declaration endorsed by at least 88 countries, emphasising secure/trustworthy AI, accessible approaches, international cooperation and social empowerment.",
        "map": "GA: AI, international affairs · ESI: development, employment, social inclusion · FM: financial-system AI, governance/risk · Management: ethics and governance",
        "study": "Know the summit/declaration, host and broad principles; prepare balanced opportunities/risks: productivity, access, skills, bias, privacy, IP, compute concentration and accountability. Keep numbers secondary to the policy debate.",
        "priority": "High",
        "source": "News18 summit declaration report",
        "url": "https://www.news18.com/india/india-ai-impact-summit-2026-adopts-delhi-declaration-endorsed-by-88-nations-secure-trusted-ai-ws-l-9922090.html",
        "source2": "Official IndiaAI portal",
        "url2": "https://indiaai.gov.in/",
    },
    {
        "date": "Jul 2026",
        "topic": "Financial inclusion measured as access, usage and quality",
        "evidence": "Business Standard reports the RBI Financial Inclusion Index at 70.0 for March 2026 versus 67.0 in March 2025, with usage a key driver. Verify the RBI's primary release for the exact component scores and release date.",
        "map": "FM: Financial Inclusion, Financial System · ESI: development, inequality, social structure · GA: RBI, financial inclusion",
        "study": "Understand why inclusion is more than account access: use, quality, literacy, affordability and consumer protection. Connect digital rails to last-mile access and fraud/exclusion risks.",
        "priority": "Very high",
        "source": "Business Standard report on RBI FI-Index",
        "url": "https://www.business-standard.com/industry/banking/rbi-s-financial-inclusion-index-rises-to-70-in-fy26-on-higher-usage-126071601414_1.html",
        "source2": "RBI financial inclusion portal",
        "url2": "https://www.rbi.org.in/",
    },
    {
        "date": "Sep 2026",
        "topic": "BRICS New Delhi Declaration: global governance, trade/energy resilience, AI governance and cross-border payments",
        "evidence": "Forbes India reports the declaration covered UN/IMF reform, trade and energy flows, AI governance, and continued work on cross-border payment interoperability and local-currency settlement. Treat detailed commitments as article-level leads; consult the declaration text before memorising wording.",
        "map": "GA: BRICS/international institutions · ESI: globalization, trade, international economic issues · FM: global markets, international banking, payment systems",
        "study": "Track who participated, the chair/host, headline economic and financial themes, and what was agreed versus only discussed. Link payment interoperability to correspondent banking, settlement risk and currency choice.",
        "priority": "High",
        "source": "Forbes India declaration analysis",
        "url": "https://www.forbesindia.com/article/news/brics-summit-2026-11-key-takeaways-from-the-new-delhi-declaration/2998249/1",
        "source2": "BRICS official portal",
        "url2": "https://brics2026.gov.in/",
    },
    {
        "date": "Oct 2026",
        "topic": "India–EU FTA status, market access, customs and supply-chain integration",
        "evidence": "Recent reporting describes an expected implementation timeline, but such dates are contingent and reports can vary. Do not treat the reported target as an accomplished agreement; recheck signature, ratification and entry-into-force status near the exam.",
        "map": "ESI: Globalization, trade policy and regional cooperation · GA: India–EU relations · FM: forex, markets and international banking",
        "study": "Learn what an FTA changes (tariffs, services, rules of origin, standards, market access), negotiation versus signing versus ratification, and likely opportunities/adjustment costs for India.",
        "priority": "High watchlist",
        "source": "Free Press Journal report on expected timeline",
        "url": "https://www.freepressjournal.in/business/india-eu-free-trade-agreement-likely-to-take-effect-in-q1-2027-says-piyush-goyal",
        "source2": "Department of Commerce",
        "url2": "https://commerce.gov.in/",
    },
    {
        "date": "Oct–Nov 2026",
        "topic": "Monsoon variability, El Niño, agricultural stress and food-price transmission",
        "evidence": "An ETV Bharat report citing IMD describes 2026 southwest-monsoon rainfall at 759.4 mm against an 868.6 mm long-period average (12.6% deficit), with substantial regional variation. Recheck final IMD updates; a seasonal shortfall is not by itself a crop-loss estimate.",
        "map": "ESI: agriculture, growth, poverty/employment, sustainability · GA: climate/environment · FM: inflation and policy response",
        "study": "Connect rainfall and regional variation to reservoirs, irrigation, crop choice, rural income, food supply and CPI; distinguish El Niño influence from a deterministic forecast.",
        "priority": "High",
        "source": "ETV Bharat report citing IMD",
        "url": "https://www.etvbharat.com/en/opinion/el-nino-indias-deficient-2026-monsoon-and-risks-ahead-climate-change-winter-rainfall-humidity-enn26101605007",
        "source2": "India Meteorological Department",
        "url2": "https://mausam.imd.gov.in/",
    },
    {
        "date": "Nov 2026",
        "topic": "Cyber resilience in non-bank payment operators; vendor, audit and incident-reporting controls",
        "evidence": "Rediff reports new consolidated RBI directions for non-bank payment system operators, including annual system audit, third-party oversight, vulnerability/source-code controls and six-hour incident reporting. Check the actual RBI Master Direction for scope and effective dates.",
        "map": "FM: Financial System, Risk Management, Banking Governance · GA: RBI, digital payments, cyber/technology · Management: accountability and controls",
        "study": "Know operational/cyber risk, third-party concentration, business continuity, incident reporting, audit and consumer trust. Understand the regulatory objective and trade-off between resilience and compliance cost.",
        "priority": "Very high",
        "source": "Rediff report on RBI payment-system cyber directions",
        "url": "https://www.rediff.com/business/report/rbis-new-cyber-resilience-rules-for-non-bank-payment-operators-what-you-need-to-know/20261106.htm",
        "source2": "RBI notifications",
        "url2": "https://www.rbi.org.in/",
    },
]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def rows_as_dicts(connection, query, parameters=()):
    cursor = connection.execute(query, parameters)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def build_data():
    taxonomy = read_csv(TAXONOMY_FILE)
    gaps = read_csv(GAPS_FILE)
    connection = sqlite3.connect(DATABASE)
    try:
        phase_one_counts = rows_as_dicts(
            connection,
            """SELECT q.year,q.subject,t.topic,COUNT(DISTINCT q.question_id) AS count
               FROM questions q
               JOIN question_taxonomy qt
                 ON qt.question_id=q.question_id AND qt.tag_role='primary'
               JOIN taxonomy t ON t.taxonomy_id=qt.taxonomy_id
               WHERE q.phase='Phase 1' AND q.year BETWEEN 2021 AND 2026
               GROUP BY q.year,q.subject,t.topic
               ORDER BY q.subject,t.topic,q.year""",
        )
        phase_one_series = defaultdict(lambda: {year: 0 for year in PHASE_ONE_YEARS})
        for row in phase_one_counts:
            phase_one_series[(row["subject"], row["topic"])][row["year"]] = row["count"]

        phase_one_coverage = []
        for year in PHASE_ONE_YEARS:
            subject_rows = []
            for subject, expected in PHASE_ONE_EXPECTED.items():
                observed = connection.execute(
                    """SELECT COUNT(DISTINCT original_question_number)
                       FROM questions
                       WHERE year=? AND phase='Phase 1' AND subject=?""",
                    (year, subject),
                ).fetchone()[0]
                subject_rows.append({
                    "subject": subject,
                    "expected": expected,
                    "observed": observed,
                })
            phase_one_coverage.append({"year": year, "subjects": subject_rows})

        phase_two_counts = rows_as_dicts(
            connection,
            """SELECT q.year,q.subject,q.section,t.topic,
                      COUNT(DISTINCT q.question_id) AS count
               FROM questions q
               JOIN question_taxonomy qt
                 ON qt.question_id=q.question_id AND qt.tag_role='primary'
               JOIN taxonomy t ON t.taxonomy_id=qt.taxonomy_id
               WHERE q.phase='Phase 2' AND q.year BETWEEN 2021 AND 2025
               GROUP BY q.year,q.subject,q.section,t.topic
               ORDER BY q.subject,q.section,t.topic,q.year""",
        )
        phase_two_series = defaultdict(
            lambda: {
                year: {"Objective": 0, "Descriptive": 0}
                for year in PHASE_TWO_YEARS
            }
        )
        for row in phase_two_counts:
            phase_two_series[
                (row["subject"], row["topic"])
            ][row["year"]][row["section"]] = row["count"]

        for item in PHASE_TWO_GUIDE:
            subjects = {
                "ESI": "Economic and Social Issues",
                "Finance": "Finance and Management",
                "Finance / Management": "Finance and Management",
                "Management": "Finance and Management",
                "English Writing Skills": "Descriptive English",
            }
            paper_subject = subjects[item["subject"]]
            annual = {}
            for year in PHASE_TWO_YEARS:
                obj = 0
                desc = 0
                for tag in item["tags"]:
                    counts = phase_two_series[(paper_subject, tag)][year]
                    obj += counts["Objective"]
                    desc += counts["Descriptive"]
                annual[year] = {
                    "objective": obj,
                    "descriptive": desc,
                    "total": obj + desc,
                }
            item["annual"] = annual
            item["objective_total"] = sum(x["objective"] for x in annual.values())
            item["descriptive_total"] = sum(x["descriptive"] for x in annual.values())
            item["total"] = item["objective_total"] + item["descriptive_total"]
            item["annual_totals"] = [annual[year]["total"] for year in PHASE_TWO_YEARS]
            item["do_not_study"] = PHASE_TWO_DEPRIORITIZE[item["chapter"]]
            item["source_ids"] = PHASE_TWO_SOURCE_MAP.get(
                item["chapter"], ["official-syllabus"]
            )

        p1_totals = {}
        for subject in PHASE_ONE_GUIDE:
            rows = []
            for topic, history, priority, focus in PHASE_ONE_GUIDE[subject]["topics"]:
                taxonomy_topic = PHASE_ONE_TAG_ALIASES.get(topic, topic)
                values = {
                    year: phase_one_series[(subject, taxonomy_topic)][year]
                    for year in PHASE_ONE_YEARS
                }
                rows.append({
                    "topic": topic,
                    "history": history,
                    "priority": priority,
                    "focus": focus,
                    "study": PHASE_ONE_BOUNDARIES[subject][topic][0],
                    "do_not_study": PHASE_ONE_BOUNDARIES[subject][topic][1],
                    "source_ids": PHASE_ONE_SOURCE_MAP.get(subject, {}).get(topic, []),
                    "annual": values,
                    "complete_cycle_total": sum(
                        values[year] for year in COMPLETE_PHASE_ONE_YEARS[subject]
                    ),
                    "annual_vector": [values[year] for year in PHASE_ONE_YEARS],
                })
            PHASE_ONE_GUIDE[subject]["topic_data"] = rows
            p1_totals[subject] = sum(
                item["complete_cycle_total"] for item in rows
            )

        for entry in CURRENT_AFFAIRS:
            entry["checked_on"] = "9 Nov 2026"

        phase_two_rows = [
            row for row in gaps if row["phase"] == "Phase 2"
            and row["year"] in {str(year) for year in PHASE_TWO_YEARS}
            and (row["missing_question_numbers"] or row["duplicate_question_numbers"])
        ]
        return {
            "generated": date.today().strftime("%d %b %Y"),
            "source_cutoff": "9 Nov 2026",
            "years_p1": PHASE_ONE_YEARS,
            "complete_p1_years": COMPLETE_PHASE_ONE_YEARS,
            "phase_one_coverage": phase_one_coverage,
            "phase_one_guide": PHASE_ONE_GUIDE,
            "phase_one_clean_tag_totals": p1_totals,
            "study_resources": STUDY_RESOURCES,
            "ga_mixed_families": GA_MIXED_FAMILIES,
            "ga_scheme_checklist": GA_SCHEME_CHECKLIST,
            "ga_reports_to_study": GA_REPORTS_TO_STUDY,
            "phase_two_years": PHASE_TWO_YEARS,
            "phase_two_guide": PHASE_TWO_GUIDE,
            "taxonomy": taxonomy,
            "current_affairs": CURRENT_AFFAIRS,
            "phase_two_gaps": phase_two_rows,
        }
    finally:
        connection.close()


def json_script(data):
    return (
        json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def build_html(data):
    title = "RBI Grade B 2027 | Focused Study & Prediction Guide"
    content = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Evidence-weighted RBI Grade B 2027 preparation priorities, historical topic trends, score targets and current-affairs syllabus mapping.">
<title>__TITLE__</title>
<style>
:root{color-scheme:light;--ink:#172b3b;--muted:#607487;--line:#dfe7eb;--paper:#f3f6f7;--card:#fff;--navy:#102a3e;--teal:#007f78;--blue:#3474ad;--amber:#c9831d;--red:#a84e55;--green:#287d59;--shadow:0 7px 22px rgba(19,42,59,.055)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.58 "Segoe UI",Inter,system-ui,-apple-system,sans-serif}a{color:#126d79}.shell{max-width:1240px;margin:auto;padding:26px 28px 68px}.hero{background:radial-gradient(circle at 88% 18%,rgba(0,177,163,.22),transparent 25%),linear-gradient(125deg,#102a3e 0%,#153d51 70%,#145b62 100%);border-radius:21px;padding:31px 37px 34px;color:#fff;box-shadow:var(--shadow)}.topline{display:flex;justify-content:space-between;align-items:center;gap:14px;color:#c5d6de;font-size:12px;letter-spacing:.13em;text-transform:uppercase}.hero h1{margin:30px 0 9px;max-width:850px;font-size:clamp(34px,5vw,56px);line-height:1.04;letter-spacing:-.045em}.hero p{margin:0;max-width:820px;color:#d6e5e9;font-size:16px}.hero-meta{margin-top:22px;display:flex;flex-wrap:wrap;gap:8px}.pill{border:1px solid rgba(255,255,255,.25);border-radius:99px;color:#e8f1f3;padding:6px 10px;font-size:12px}.date{margin-left:auto;color:#c5d6de;font-size:12px}.nav{display:flex;flex-wrap:wrap;gap:8px;margin:17px 0 26px}.nav a{text-decoration:none;color:var(--ink);background:#fff;border:1px solid var(--line);border-radius:8px;padding:7px 11px;font-size:12px}section{margin:30px 0;scroll-margin-top:14px}.head{display:flex;align-items:end;justify-content:space-between;gap:14px;margin:0 0 13px}.eyebrow{color:var(--teal);font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin-bottom:5px}h2{font-size:24px;line-height:1.2;letter-spacing:-.025em;margin:0}h3{font-size:18px;margin:0}.note{max-width:820px;color:var(--muted);font-size:13px;margin:5px 0 0}.topic-study{background:#edf6f3;padding:8px 10px;border-radius:8px}.topic-skip{background:#fff0ed;padding:8px 10px;border-radius:8px}.mixed-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.family{padding:13px 14px;border:1px solid var(--line);border-radius:10px;background:#fff}.family h3{font-size:14px}.family p{margin:7px 0;color:#526577;font-size:12px}.report-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.report-card{padding:13px 14px;border:1px solid var(--line);border-radius:10px;background:#fff}.report-card h3{font-size:14px}.report-meta{font-size:11px;color:#607487;margin-top:3px}.report-card p{font-size:12px;color:#526577;margin:7px 0}.scheme-table{min-width:900px;width:100%;border-collapse:collapse;font-size:12px}.scheme-table th,.scheme-table td{padding:9px 10px;border-bottom:1px solid #edf0f2;text-align:left;vertical-align:top}.scheme-table th{color:#66798a;background:#f7f9fa;text-transform:uppercase;font-size:10px;letter-spacing:.06em}.allocation{grid-template-columns:repeat(5,minmax(0,1fr))}
.grid{display:grid;gap:13px}.grid>*{min-width:0}.four{grid-template-columns:repeat(4,minmax(0,1fr))}.three{grid-template-columns:repeat(3,minmax(0,1fr))}.two{grid-template-columns:repeat(2,minmax(0,1fr))}
.card{min-width:0;background:var(--card);border:1px solid var(--line);border-radius:13px;box-shadow:var(--shadow)}.pad{padding:19px 21px}.kpi{padding:17px 18px}.kpi .value{font-size:26px;font-weight:750;line-height:1.1;letter-spacing:-.04em}.kpi .label{margin-top:7px;color:var(--muted);font-size:12px}
.callout{border-left:4px solid var(--amber);background:#fff4e1;color:#664b22;border-radius:8px;padding:13px 15px;font-size:13px}.good{border-left-color:var(--teal);background:#e8f4f1;color:#235653}.bad{border-left-color:var(--red);background:#fbebeb;color:#714045}.small{color:var(--muted);font-size:12px}.strong{font-weight:750}
.subject{padding:18px}.subject-header{display:flex;justify-content:space-between;gap:12px;align-items:start}.target{border-radius:8px;background:#e6f4f1;color:#145850;padding:7px 9px;font-size:12px;font-weight:750;white-space:nowrap}.priority{display:inline-flex;align-items:center;border-radius:99px;background:#e8f3ef;color:#276b4f;font-weight:700;font-size:11px;padding:3px 8px;white-space:nowrap}.priority.high{background:#e9f1f8;color:#2d5a80}.priority.medium{background:#fff1dc;color:#825819}
.topic-list{display:grid;gap:10px;margin-top:14px}.topic{border-top:1px solid #edf0f2;padding-top:10px}.topic-top{display:flex;align-items:start;justify-content:space-between;gap:10px}.topic-name{font-weight:700;font-size:14px}.topic-count{font:12px ui-monospace,Consolas,monospace;color:#536879;white-space:nowrap}.topic p{margin:5px 0 0;color:#526577;font-size:12px}
.chart-wrap,.table-wrap{overflow-x:auto}.chart-wrap svg{display:block;width:100%;min-width:680px;height:auto}.chart-legend{display:flex;flex-wrap:wrap;gap:11px;margin-top:8px;color:var(--muted);font-size:12px}.chart-legend span{display:inline-flex;gap:6px;align-items:center}.dot{width:9px;height:9px;border-radius:3px;display:inline-block}
.trend-table{min-width:760px;width:100%;border-collapse:collapse;font-size:12px}.trend-table th{text-align:left;color:#66798a;background:#f7f9fa;text-transform:uppercase;font-size:10px;letter-spacing:.06em;white-space:nowrap}.trend-table th,.trend-table td{padding:9px 10px;border-bottom:1px solid #edf0f2;vertical-align:top}.trend-table td.num,.trend-table th.num{text-align:right;font-variant-numeric:tabular-nums}.table-filter{width:min(360px,100%);padding:9px 11px;border:1px solid var(--line);border-radius:8px;font:inherit}
.score-formula{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin:12px 0}.score-box{padding:12px;border:1px solid var(--line);border-radius:9px;background:#fff}.score-box b{display:block;font-size:19px}.score-box span{font-size:11px;color:var(--muted)}
.chapter-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:13px}.chapter{background:#fff;border:1px solid var(--line);border-radius:11px;overflow:hidden}.chapter[open]{box-shadow:var(--shadow)}.chapter summary{list-style:none;cursor:pointer;padding:13px 14px;display:flex;justify-content:space-between;gap:12px;align-items:start}.chapter summary::-webkit-details-marker{display:none}.chapter-title{font-weight:750;font-size:14px}.chapter-meta{color:#526879;white-space:nowrap;font-size:11px}.chapter-body{padding:0 14px 14px;border-top:1px solid var(--line)}.chapter-body p{font-size:12px;margin:10px 0;color:#4f6273}.chapter-body .subtopics{color:#506477;background:#f2f5f6;padding:8px 10px;border-radius:8px;font-size:12px}.chapter-body .ask{background:#eef5f8;padding:9px 10px;border-radius:8px}.annual{font:11px ui-monospace,Consolas,monospace;color:#385b67}.trend-label{font-size:11px;font-weight:750}
.filterbar{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap;margin:14px 0}.news-list{display:grid;gap:11px}.news{padding:15px 16px}.news-header{display:flex;justify-content:space-between;gap:10px}.news-title{font-weight:750}.news-date{color:#6b7c8b;font-size:11px;white-space:nowrap}.news p{margin:7px 0;color:#4f6273;font-size:12px}.news-links{display:flex;gap:10px;flex-wrap:wrap;font-size:11px}.news-map{color:#1e6570;font-size:12px;font-weight:650}.subhead{margin:18px 0 10px}
.anomalies{display:grid;gap:8px}.anomaly{padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:white;font-size:12px;color:#506173}.anomaly b{color:#8a5918}.sources{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}.source{padding:11px 12px;border:1px solid var(--line);border-radius:9px;background:#fff;font-size:12px}.source p{font-size:11px;color:var(--muted);margin:4px 0 0}.resource-links{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.resource-links a,.resource-links span{display:inline-block;border:1px solid #d5e4e6;background:#f4f9f8;border-radius:6px;padding:4px 7px;font-size:11px;text-decoration:none}.resource-links span{color:#536879}.resource-details{margin-top:13px;border:1px solid var(--line);border-radius:10px;background:#f8fafb;padding:12px}.resource-details summary{cursor:pointer;font-size:13px;font-weight:700}.resource-details .sources{margin-top:12px}.footer{border-top:1px solid var(--line);padding-top:16px;margin-top:38px;color:var(--muted);font-size:11px}.print{border:1px solid #ffffff50;border-radius:7px;background:#ffffff12;color:white;padding:7px 10px;font:inherit;cursor:pointer}.tabs{display:flex;gap:6px;flex-wrap:wrap}.tabs button{border:1px solid var(--line);border-radius:7px;background:white;padding:7px 10px;font:inherit;font-size:12px;color:var(--ink);cursor:pointer}.tabs button.active{background:#133d50;color:white;border-color:#133d50}
@media(max-width:850px){.four{grid-template-columns:repeat(2,minmax(0,1fr))}.three,.two,.mixed-grid,.report-grid{grid-template-columns:1fr}.allocation{grid-template-columns:repeat(3,minmax(0,1fr))}.sources{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:620px){.shell{padding:13px 13px 40px}.hero{padding:23px 19px;border-radius:15px}.hero h1{margin-top:22px}.date{margin-left:0;width:100%}.four{grid-template-columns:repeat(2,minmax(0,1fr))}.chapter-grid{grid-template-columns:1fr}.score-formula{grid-template-columns:repeat(2,minmax(0,1fr))}.subject-header{display:block}.target{display:inline-block;margin-top:8px}.sources{grid-template-columns:1fr}.head{align-items:start;flex-direction:column}}
@media print{body{background:white;font-size:11px}.shell{max-width:none;padding:0}.hero{border-radius:0;box-shadow:none;print-color-adjust:exact;-webkit-print-color-adjust:exact}.nav,.print,.table-filter,.tabs{display:none!important}.card,.chapter,.news{box-shadow:none;break-inside:avoid}.chapter:not([open]) .chapter-body{display:block}section{break-inside:avoid}a{color:inherit;text-decoration:none}}
</style>
</head>
<body>
<main class="shell">
<header class="hero">
  <div class="topline"><span>RBI Grade B · 2027 preparation intelligence</span><button class="print" onclick="window.print()">Print / save PDF</button></div>
  <h1>Study less randomly.<br>Prepare with a return.</h1>
  <p>A focused preparation guide built from the supplied 2019 and 2021–2026 memory-based compilations, the supplied 2025 Phase II syllabus excerpt, and current-affairs developments checked through 9 November 2026. It gives priorities and practice targets—not exact-paper promises.</p>
  <div class="hero-meta"><span class="pill">No question stems or answer keys</span><span class="pill">Frequency ≠ probability</span><span class="pill">2027 predictions are evidence-weighted</span><span class="date">Updated __GENERATED__ · news cutoff __CUTOFF__</span></div>
</header>
<nav class="nav"><a href="#decision">Priority map</a><a href="#where">Where to study</a><a href="phase1_question_bank.html" target="_blank" rel="noopener noreferrer">Phase I questions by topic ↗</a><a href="phase2_notes_graph.html" target="_blank" rel="noopener noreferrer">Phase II notes graph ↗</a><a href="phase2_deep_analysis.html" target="_blank" rel="noopener noreferrer">Phase II 75–80% deep analysis ↗</a><a href="../study_library/index.html" target="_blank" rel="noopener noreferrer">Study Studio ↗</a><a href="#phase1">Phase I targets</a><a href="#ga-command">GA deep dive</a><a href="#phase1-trends">Phase I trends</a><a href="#phase2">Phase II chapters</a><a href="#current">Current-affairs watchlist</a><a href="#plan">Minimal plan</a><a href="#method">Evidence & limits</a></nav>

<section id="decision">
  <div class="head"><div><div class="eyebrow">01 · Executive decisions</div><h2>What to prepare first</h2><p class="note">The aim is breadth with selective depth: secure repeated, syllabus-core marks first; then use current affairs to add specificity and descriptive relevance.</p></div></div>
  <div class="grid four">
    <article class="card kpi"><div class="value">60%+</div><div class="label">Minimum raw correct-rate objective in each Phase I section</div></article>
    <article class="card kpi"><div class="value">70%</div><div class="label">Phase I overall raw-score ambition; use net marks if negative marking applies</div></article>
    <article class="card kpi"><div class="value">75–80%</div><div class="label">Phase II target range; validate official paper weights and rubric for 2027</div></article>
    <article class="card kpi"><div class="value">Core first</div><div class="label">Arithmetic · puzzles/deductions · RBI/banking · growth/economy · management · writing</div></article>
  </div>
  <div class="grid two" style="margin-top:13px">
    <article class="card pad"><div class="eyebrow">The strongest historical signals</div><ul class="small"><li>Phase I uses four large sections; arithmetic is the most consistently identifiable Quant tag.</li><li>Reasoning is a mixed-set paper: puzzles/seating and syllogism/deduction repeat, but many markers are not resolved by the current tags.</li><li>GA repeatedly mixes government programmes, banking/RBI, reports and global affairs. Recent international and technology coverage makes current-affairs breadth important.</li><li>Phase II ESI and Finance & Management are indexed at 30 objective + 6 descriptive markers per supplied cycle from 2021–2025; tags are useful for relative prioritisation, not exact marks.</li><li>ESI growth/development and Finance banking/system are the largest mapped chapter signals. Large unclassified groups require syllabus-wide minimum coverage.</li></ul></article>
    <article class="card pad"><div class="eyebrow">Prediction discipline</div><div class="callout good"><b>My 2027 call:</b> the best bets are recurring formats plus current-affairs extensions of the syllabus—banking/payment regulation and cyber resilience; inclusion; inflation/fiscal-growth trade-offs; employment/agriculture/climate; global trade/energy; AI productivity and governance. Confidence is highest in broad themes, lowest in exact subtopics or counts.</div><p class="small">A five-year frequency is a sample from memory-based papers and rule-based tags. It is not a calibrated probability. A topic absent from the tags may be hidden in “other,” mixed wording or shared-context extraction.</p></article>
  </div>
</section>

<section id="where">
  <div class="head"><div><div class="eyebrow">02 · Where to study</div><h2>A small, reliable source stack for every topic</h2><p class="note">Use the topic-level links in the Phase I and Phase II maps below. The source shelf here tells you what each source is good for—and keeps the plan deliberately small.</p></div></div>
  <div class="grid two">
    <article class="card pad"><div class="eyebrow">The 2 + 1 rule</div><ol class="small"><li><b>Learn the concept:</b> one static foundation or the exact syllabus scope; do not collect multiple full courses.</li><li><b>Update and verify:</b> use the responsible official institution for current rules, figures, schemes and report editions.</li><li><b>Practise:</b> use the supplied memory-based papers, one practice book or one mock series, then maintain an error log. The papers are useful practice, not official RBI papers.</li></ol><p class="small">For GA, make the official release the fact source; use one newspaper/explainer only to understand context. A monthly compilation can be an index, not a second authority.</p></article>
    <article class="card pad"><div class="eyebrow">Minimal source stack by need</div><ul class="small"><li><b>Phase I GA + Phase II ESI/FM:</b> RBI, PIB/myScheme, Budget/Economic Survey, MoSPI and a focused report list.</li><li><b>Static ESI:</b> selected NCERT economics chapters; update arguments and figures from Survey/Budget/MoSPI.</li><li><b>Finance:</b> RBI and SEBI/NISM for institutions, markets, regulation and risk; skip certification-level detail.</li><li><b>Management:</b> official syllabus plus selective IGNOU eGyanKosh material; one standard text only if a concept remains unclear.</li><li><b>Phase I aptitude/English:</b> one practice reference per weak subject, supplied PYPs and timed mocks. No paid course is required by this guide.</li></ul></article>
  </div>
  <div class="callout good" style="margin-top:12px"><b>Use the links where they appear:</b> every mapped Phase I topic and Phase II chapter has a short “Study here” source strip. Official syllabus links refer only to the supplied 2025 Phase II syllabus; recheck the 2027 notification before fixing scope. <a href="phase2_notes_graph.html" target="_blank" rel="noopener noreferrer">Open the connected graph of your Phase II notes in a separate tab ↗</a></div>
  <details class="resource-details"><summary>Open the curated source shelf and usage notes</summary><div id="resource-catalog" class="sources"></div></details>
</section>

<section id="phase1">
  <div class="head"><div><div class="eyebrow">03 · Phase I score design</div><h2>Protect the 60% floor in every section</h2><p class="note">Reference ranges below match the 200-number layout used in the searchable supplied compilations, not a guarantee of the 2027 official structure.</p></div></div>
  <div class="grid two">
    <article class="card pad">
      <div class="table-wrap"><table class="trend-table" id="score-table"></table></div>
      <div class="callout" style="margin-top:12px"><b>70% overall arithmetic:</b> if the 2027 Phase I remains 80 GA + 30 Quant + 60 Reasoning + 30 English = 200 equally weighted one-mark items, 140 net marks is a 70% goal. A balanced practice profile near 56/80, 21/30, 42/60 and 21/30 is 140 raw correct only if unanswered/wrong responses incur no penalty. With negative marking, score to the official net formula and keep an accuracy buffer; confirm the notification's marks and penalty.</div>
    </article>
    <article class="card pad">
      <div class="eyebrow">Guardrails against over-attempting</div>
      <ul class="small"><li>Track <b>net marks, accuracy and time</b> for each section separately; raw attempts can hide a negative-marking problem.</li><li>For GA, answer known facts and strong eliminations; do not turn uncertainty into blind guesses.</li><li>For Quant and Reasoning, set a time ceiling per item/set. Leave a time sink and collect easier marks elsewhere.</li><li>For English, passage evidence and grammar rules beat intuition. Maintain an error log.</li><li>Use two consecutive full mocks to decide whether the weakest section needs more time; don't redistribute study time based on one bad test.</li></ul>
      <div class="callout bad"><b>2025 Phase I is incomplete:</b> 155 of the reference 200 distinct marker positions are present (GA 46/80, Reasoning 51/60 distinct with a repeated Q155, English 28/30, Quant 30/30). It is not a reliable paper-weight trend.</div>
    </article>
  </div>
  <div class="grid two" id="subject-guides" style="margin-top:13px"></div>
</section>

<section id="ga-command">
  <div class="head"><div><div class="eyebrow">04 · General Awareness command center</div><h2>Make the vast section finite—and reusable in Phase II</h2><p class="note">Treat GA as a retrieval system: identify the institution, fact, date/source and policy consequence. The same compact note should feed Phase I recall and Phase II ESI/FM examples.</p></div></div>
  <div class="grid four">
    <article class="card kpi"><div class="value">Across phases</div><div class="label">RBI, Budget, Survey, jobs, inclusion, climate and global shocks recur as objective facts and descriptive evidence.</div></article>
    <article class="card kpi"><div class="value">One-page</div><div class="label">Keep one theme sheet: issuer · event · 1–3 facts · mechanism · syllabus links · update date.</div></article>
    <article class="card kpi"><div class="value">12–15 mo</div><div class="label">Prioritise the final current-affairs window before the exam; retain a small static base.</div></article>
    <article class="card kpi"><div class="value">70 / 400</div><div class="label">Indexed clean-cycle GA markers fell into automatic “other”; manual review shows a mix, not one topic.</div></article>
  </div>
  <div class="grid two" style="margin-top:13px">
    <article class="card pad"><div class="eyebrow">What the paper actually tests</div><ul class="small"><li><b>Identity:</b> institution, ministry, regulator, report publisher, scheme or programme.</li><li><b>Precise attributes:</b> objective, beneficiary, eligibility, component, limit/threshold, date, place, partner, host or chair.</li><li><b>Data literacy:</b> rank/score, source, period, unit, top performer, measured dimension and change from the previous release.</li><li><b>Policy facts:</b> target, budget/funding, extension, implementation channel, latest rule/status and intended outcome.</li><li><b>Phase II bridge:</b> explain why the fact matters—growth, inflation, employment, inclusion, fiscal space, stability, climate or external-sector transmission.</li></ul></article>
    <article class="card pad"><div class="eyebrow">GA study method that maximises recall</div><ol class="small"><li><b>Collect selectively:</b> use primary releases first; retain a story only if it maps to RBI/banking, economy, government policy, reports, international affairs, social development, climate or major science/technology.</li><li><b>Compress:</b> make one card per event/report/scheme, with a 20–40 word fact core and one “why it matters” line.</li><li><b>Retrieve:</b> hide the notes; recall issuer, purpose, date, beneficiary/metric, one number and syllabus link. Revisit after 1, 3, 7, 21 days.</li><li><b>Interleave:</b> mix static banking/economy concepts with current-affairs cards; do a timed GA set and audit misses by fact type.</li><li><b>Update:</b> replace stale forecasts/amounts with the latest official release; keep publication vintage and reference period visible.</li></ol></article>
  </div>
  <div class="subhead"><h3>Manual decomposition of the GA “other / unclassified” bucket</h3><p class="note">Review of the source-page summaries shows these recurring families hiding under the broad tag. The 70/400 is an automatic indexed-marker count, not a clean unique-item weight; families overlap, and duplicate/missing markers exist, so no invented subtopic counts or shares are shown.</p></div>
  <div id="ga-mixed-families" class="mixed-grid"></div>
  <div class="callout" style="margin-top:12px"><b>Audit caution:</b> the automatic “Government schemes” and “Reports/indices” labels are also broad and sometimes absorb adjacent policy or static-GK facts. The 79 scheme-tag and 25 report-tag markers are not counts of pure scheme/report questions. Use the actual families below; don't assume every marker in those categories is one.</div>
  <div class="subhead"><h3>One current-affairs note, three exam uses</h3></div>
  <article class="card pad"><div class="table-wrap"><table class="scheme-table"><thead><tr><th>GA fact family</th><th>Phase I retrieval</th><th>Phase II ESI/FM application</th></tr></thead><tbody>
    <tr><td><b>RBI / banking / payments</b></td><td>Issuer, circular or institution, feature/limit, effective date</td><td>Financial System, inclusion, risk/cyber controls, financial stability and consumer protection</td></tr>
    <tr><td><b>Budget / Survey / official data</b></td><td>Publisher, year, value, unit, period, rank/definition</td><td>Growth, fiscal space, inflation, employment, sectoral composition and policy trade-offs</td></tr>
    <tr><td><b>Government schemes</b></td><td>Ministry, objective, beneficiary, eligibility, benefit, target and latest status</td><td>Poverty, employment, social justice, human development, agriculture, inclusion and implementation quality</td></tr>
    <tr><td><b>Climate / food / energy</b></td><td>Event/location, agency, verified measure, programme or convention</td><td>Sustainable development, agriculture, livelihoods, food inflation, energy security and fiscal response</td></tr>
    <tr><td><b>Trade / global institutions</b></td><td>Body/member/host, agreement status, report or current headline</td><td>Globalization, balance of payments, exchange-rate/capital-flow channel and international banking</td></tr>
    <tr><td><b>AI / digital / technology</b></td><td>Mission/platform, department, purpose, application and status</td><td>Productivity, labour-market change, inclusion, financial-sector efficiency, privacy, bias and governance</td></tr>
  </tbody></table></div></article>
  <div class="subhead"><h3>Schemes: learn the decision-relevant facts, not a catalogue</h3><p class="note">Scheme-related paper items repeatedly reduce to a small set of factual dimensions. The examples below are names/themes seen in the supplied compilations, not a frequency ranking.</p></div>
  <article class="card pad"><div class="table-wrap"><table class="scheme-table" id="scheme-table"></table></div></article>
  <div class="grid two" style="margin-top:13px">
    <article class="card pad"><div class="eyebrow">How to answer scheme questions</div><p class="small"><b>Build a 7-field card:</b> full name/acronym · ministry/implementer · objective · beneficiary and exclusions · benefit/component · funding/target/duration · latest change/status. Add one cross-link to jobs, agriculture, health, education, women, MSMEs, exports, energy, housing or financial inclusion.</p><p class="small"><b>High-return contrast:</b> central-sector vs centrally sponsored; grant/subsidy vs credit/guarantee; announced vs operational; original vs extended/restructured; target vs achievement.</p></article>
    <article class="card pad"><div class="eyebrow">What not to do with schemes</div><ul class="small"><li>Do not memorise a long scheme list without beneficiary, ministry and delivery mechanism.</li><li>Do not use stale allocations/eligibility; amounts and extension dates change yearly.</li><li>Do not overlearn state-level micro-schemes absent major national relevance.</li><li>Do not treat every budget line, law, campaign or public-sector programme as a scheme; confirm official design and current status.</li></ul></article>
  </div>
  <div class="subhead"><h3>Reports and indices worth the reading time</h3><p class="note">Prioritise the official executive summary, headline tables and India/state comparisons—not the entire document.</p></div>
  <div id="ga-reports" class="report-grid"></div>
  <div class="callout good" style="margin-top:12px"><b>Report recall template:</b> issuer → report/edition → what it measures → India/state score or rank → top performer → major change → one policy implication. The PYP trend is strongest for publisher/rank/metric/dimension-style recall, not full-report detail.</div>
</section>

<section id="phase1-trends">
  <div class="head"><div><div class="eyebrow">05 · Phase I trends</div><h2>What the searchable papers repeatedly surface</h2><p class="note">Tag counts exclude 2019 OCR. The chart uses 2021–24 and 2026 for GA, Reasoning and English; Quant retains its complete 2025 section. Counts are automated broad-theme matches, not a manual recount of official topic weights.</p></div></div>
  <article class="card pad">
    <div class="filterbar"><div class="tabs" id="phase-tabs"></div><span class="small">2025 is shown for reference but excluded from partial sections; Quant includes 2025. Denominators use observed markers, not expected exam weight.</span></div>
    <div class="chart-wrap"><svg id="phase-chart" role="img" aria-label="Phase I topic trend chart"></svg></div>
    <div class="chart-legend" id="phase-legend"></div>
    <div class="table-wrap" style="margin-top:13px"><table class="trend-table" id="phase-trend-table"></table></div>
  </article>
</section>

<section id="phase2">
  <div class="head"><div><div class="eyebrow">06 · Phase II chapter-by-chapter map</div><h2>Build a 75–80% answer base</h2><p class="note">Open a chapter for official subtopic scope, broad frequency by year, what the tagged papers tend to test, what to study and what to deprioritise. A joint tag is not split into made-up chapter counts.</p></div></div>
  <div class="grid three" style="margin-bottom:13px">
    <article class="card kpi"><div class="value">75–80</div><div class="label">ESI target marks out of 100; build mechanism-based answers with dated evidence.</div></article>
    <article class="card kpi"><div class="value">78–83</div><div class="label">Finance &amp; Management target marks out of 100; prioritise banking, markets, core management and risk.</div></article>
    <article class="card kpi"><div class="value">72–77</div><div class="label">English target marks out of 100; train essay, précis and comprehension to a consistent rubric.</div></article>
  </div>
  <div class="callout good" style="margin-bottom:13px"><b>Score model (conditional):</b> if 2027 retains three equally weighted 100-mark Phase II papers, these bands sum to 225–240/300 (75–80%). Confirm the actual 2027 paper weights, descriptive/objective split and evaluation scheme before using the arithmetic.</div>
  <div class="callout">Frequency is a primary broad-tag count across 2021–2025. ESI and FM each have 150 objective and 30 descriptive marker records in the supplied set (with the 2021 ESI gap/duplicate noted below). Tagging is automatic and the 2025 syllabus is a reference crosswalk, not retroactive proof of older syllabus wording.</div>
  <div class="filterbar"><input id="chapter-filter" class="table-filter" type="search" placeholder="Filter by chapter, subtopic or priority"><span class="small">Order: syllabus sequence. Chapters without clean separate frequency still receive a minimum-coverage recommendation.</span></div>
  <div id="phase2-chapters" class="chapter-grid"></div>
  <div class="subhead"><h3>Frequency and direction at a glance</h3><p class="note">Annual totals combine objective and descriptive primary tags. “Joint” category counts stay joint and are not added to multiple chapters in the frequency chart.</p></div>
  <article class="card pad"><div class="table-wrap"><table class="trend-table" id="phase2-table"></table></div></article>
  <div class="subhead"><h3>Descriptive English: treat the format as a recurring skill</h3></div>
  <article class="card pad"><p class="small">Each supplied cycle 2021–2025 lists essay, précis and comprehension tasks. Over those 15 task markers, the keyword index labels 5 essays, 5 précis, 3 comprehension and 2 unresolved. Prepare all three formats; do not infer a 2027 prompt from the five repeats.</p><div class="grid three"><div class="score-box"><b>Essay</b><span>Thesis → 2–3 arguments → evidence/examples → balanced conclusion</span></div><div class="score-box"><b>Précis</b><span>Central argument, faithful logic, concise wording, no new opinion</span></div><div class="score-box"><b>Comprehension</b><span>Evidence-led answers, precise paraphrase, controlled length and grammar</span></div></div></article>
</section>

<section id="current">
  <div class="head"><div><div class="eyebrow">07 · Current-affairs to syllabus map</div><h2>High-yield 2026 developments to convert into study notes</h2><p class="note">These are candidates for the 2027 question environment, not predictions of specific items. Facts and forecasts have dates; update releases and status before the exam.</p></div></div>
  <div id="news-list" class="news-list"></div>
</section>

<section id="plan">
  <div class="head"><div><div class="eyebrow">08 · Minimal, high-return operating plan</div><h2>Study a small set deeply; keep the rest warm</h2><p class="note">Use percentages of your available study time so the routine scales to your schedule.</p></div></div>
  <div class="grid two">
    <article class="card pad"><div class="eyebrow">Weekly allocation</div>
      <div class="score-formula allocation"><div class="score-box"><b>30%</b><span>Phase II static core: ESI + FM + management</span></div><div class="score-box"><b>25%</b><span>Phase I Quant + Reasoning timed practice</span></div><div class="score-box"><b>25%</b><span>GA: current affairs, RBI, reports and schemes</span></div><div class="score-box"><b>10%</b><span>English: daily reading, grammar and vocab</span></div><div class="score-box"><b>10%</b><span>Mocks, descriptive writing and error review</span></div></div>
      <p class="small">This deliberately gives GA a dedicated quarter because its breadth feeds both phases. After two mocks, move up to 10 percentage points toward the weakest section only if its net score is below target; preserve GA recall and Phase II writing even while Phase I speed work intensifies.</p>
    </article>
    <article class="card pad"><div class="eyebrow">One repeatable study loop</div><ol class="small"><li><b>Learn:</b> one syllabus subtopic from a primary source and concise notes.</li><li><b>Retrieve:</b> close the notes and explain the concept, mechanism and current example from memory.</li><li><b>Apply:</b> timed practice or a short analytical paragraph.</li><li><b>Correct:</b> record error cause, correct rule and the next review date.</li><li><b>Space:</b> revisit after 1, 3, 7 and 21 days; drop material only after repeated accurate retrieval.</li></ol></article>
  </div>
  <div class="grid two" style="margin-top:13px">
    <article class="card pad"><div class="eyebrow">Phase II answer standard</div><ul class="small"><li>Open with a direct thesis/definition; structure with short headings and linked arguments.</li><li>Use one or two precise, dated indicators; explain the mechanism and limitation rather than stacking statistics.</li><li>Balance growth with inclusion, stability, fiscal capacity, rights or sustainability where relevant.</li><li>End with feasible policy measures and a concise conclusion.</li><li>For FM, add regulator/institution, instrument, risk and control; for Management, name the theory only when it explains the scenario.</li></ul></article>
    <article class="card pad"><div class="eyebrow">Current-affairs workflow (minimal)</div><ul class="small"><li>Use a weekly primary-source sweep: RBI, Ministry of Finance/PIB, Economic Survey/Budget, IMF/World Bank, Commerce, IMD and relevant regulator releases.</li><li>Keep one page per theme—not one page per headline: event, date, issuer, mechanism, one figure, syllabus link, likely analytical angle.</li><li>Review monthly and again in the final 12–15 months before the exam; correct old forecasts with the newest vintage.</li><li>Do not memorise a news explainer's numbers until confirmed in the original release. The links below identify leads and primary verification routes.</li></ul></article>
  </div>
</section>

<section id="method">
  <div class="head"><div><div class="eyebrow">09 · Confidence, completeness and audit trail</div><h2>Where this forecast is strong—and where it isn't</h2></div></div>
  <div class="grid two">
    <article class="card pad"><div class="eyebrow">Confidence rubric</div><ul class="small"><li><b>High:</b> broad syllabus area recurs across most searchable cycles and is corroborated by the supplied syllabus or a current policy stream.</li><li><b>Medium:</b> repeated tag, but topic mapping is coarse or counts fluctuate.</li><li><b>Low:</b> few tags, mixed/joint labels, poor source coverage or only a current-affairs rationale. These remain syllabus topics, not historical winners.</li></ul><p class="small"><b>Not a statistical forecast:</b> no official sample, full paper keys, manually verified question-to-syllabus coding, marks distribution or calibrated probability model exists in the supplied evidence.</p></article>
    <article class="card pad"><div class="eyebrow">Known source limits</div><ul class="small"><li>Supplied papers are memory-based/recollected compilations; accepted as useful by the user, but not official RBI papers.</li><li>2019 has 224 OCR-derived records, all flagged for review; do not use it as a numeric trend baseline.</li><li>No 2020 paper supplied; 2026 is Phase I only.</li><li>2025 Phase I has substantial missing markers; exclude it from the clean multi-year topic comparison.</li><li>Automated Phase II tags leave 79/180 ESI records and 49/180 FM records unclassified. Separate syllabus-subtopic frequencies cannot be honestly inferred from those broad tags.</li><li>Official syllabus supplied covers Phase II only; Phase I priorities are from the papers and common task forms, not an official Phase I topic taxonomy.</li></ul></article>
  </div>
  <div class="subhead"><h3>Observed Phase II numbering anomalies</h3></div>
  <div id="gaps" class="anomalies"></div>
  <div class="subhead"><h3>Reusable files</h3></div>
  <div class="sources">
    <div class="source"><a href="../PYP/analysis/master_questions.csv">Source-page index</a><p>Metadata and theme labels; no copied stems.</p></div>
    <div class="source"><a href="../PYP/analysis/questions.sqlite">Question-index database</a><p>Local database and page-audit tables.</p></div>
    <div class="source"><a href="../PYP/analysis/extraction_gaps.csv">Coverage and gap audit</a><p>Missing/duplicate numbering and absent coverage.</p></div>
    <div class="source"><a href="../PYP/analysis/topic_taxonomy_2025.csv">Supplied-syllabus taxonomy</a><p>Chapter scope used for the Phase II map.</p></div>
    <div class="source"><a href="../PYP/analysis/year_subject_frequency.csv">Section coverage counts</a><p>Indexed counts by year, phase and subject.</p></div>
    <div class="source"><a href="../PYP/analysis/frequency_by_theme.csv">Preliminary theme counts</a><p>Automated broad-theme tags and denominators.</p></div>
  </div>
</section>
<footer class="footer">Prepared from user-supplied memory-based/recollected PDFs and the supplied 2025 RBI Phase II syllabus excerpt. The HTML intentionally contains no question wording or answer keys. All 2027 priorities are study-planning judgments; recheck RBI's 2027 notification, syllabus and marking scheme before locking targets.</footer>
</main>
<script>
const D=__DATA__;
document.querySelector(".date").textContent=`Updated ${D.generated} · news cutoff ${D.source_cutoff}`;
const esc=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const fmt=value=>Number(value).toLocaleString("en-IN");
function resourceLinks(ids){
 const wrap=document.createElement("div");wrap.className="resource-links";wrap.setAttribute("aria-label","Where to study");
 ids.forEach(id=>{
  const resource=D.study_resources[id];if(!resource)return;
  const link=resource.url?document.createElement("a"):document.createElement("span");
  if(resource.url){link.href=resource.url;if(/^https:/i.test(resource.url)){link.target="_blank";link.rel="noopener noreferrer"}}
  link.textContent=resource.name;link.title=resource.use;wrap.append(link)
 });
 return wrap
}
const resourceCatalog=document.querySelector("#resource-catalog");
Object.values(D.study_resources).forEach(resource=>{
 const card=document.createElement("article");card.className="source";
 const heading=document.createElement("div");
 if(resource.url){const link=document.createElement("a");link.href=resource.url;link.textContent=resource.name;if(/^https:/i.test(resource.url)){link.target="_blank";link.rel="noopener noreferrer"}heading.append(link)}
 else{heading.textContent=resource.name}
 const kind=document.createElement("div");kind.className="report-meta";kind.textContent=resource.kind;
 const use=document.createElement("p");use.textContent=resource.use;
 card.append(heading,kind,use);resourceCatalog.append(card)
});
const score=document.querySelector("#score-table");
score.innerHTML="<thead><tr><th>Phase I section</th><th class='num'>Reference positions</th><th class='num'>60% floor</th><th class='num'>Practice buffer (~70%)</th><th>Best return focus</th></tr></thead>";
const scoreBody=document.createElement("tbody");
const scoreFocus={"General Awareness":"Schemes · RBI/banking · reports · international","Quantitative Aptitude":"Arithmetic · DI · number patterns","Reasoning":"Puzzles · syllogism · mixed standalone types","English":"RC · grammar · vocabulary/context"};
const targets={"General Awareness":[80,48,56],"Quantitative Aptitude":[30,18,21],"Reasoning":[60,36,42],"English":[30,18,21]};
Object.entries(targets).forEach(([subject,values])=>{const tr=document.createElement("tr");[subject,...values,scoreFocus[subject]].forEach((value,i)=>{const td=document.createElement("td");td.textContent=value;if(i>0&&i<4)td.className="num";tr.append(td)});scoreBody.append(tr)});score.append(scoreBody);

const p1Root=document.querySelector("#subject-guides");
Object.entries(D.phase_one_guide).forEach(([subject,item])=>{
 const article=document.createElement("article");article.className="card subject";
 const title=document.createElement("h3");title.textContent=subject;
 const target=document.createElement("div");target.className="target";target.textContent=item.target;
 const header=document.createElement("div");header.className="subject-header";header.append(title,target);article.append(header);
 const forecast=document.createElement("p");forecast.className="small";forecast.textContent=item.forecast;article.append(forecast);
 const practice=document.createElement("div");practice.className="callout good";practice.textContent=item.practice;article.append(practice);
 const topics=document.createElement("div");topics.className="topic-list";
 item.topic_data.forEach(t=>{
  const row=document.createElement("div");row.className="topic";
  const top=document.createElement("div");top.className="topic-top";
  const name=document.createElement("div");name.className="topic-name";name.textContent=t.topic;
  const count=document.createElement("div");count.className="topic-count";count.textContent=t.history;
  top.append(name,count);
  const detail=document.createElement("p");detail.textContent=t.focus;
  detail.className="small";
  const study=document.createElement("p");study.className="topic-study small";study.textContent="What to study: "+t.study;
  const skip=document.createElement("p");skip.className="topic-skip small";skip.textContent="Deprioritise: "+t.do_not_study;
  const priority=document.createElement("span");priority.className="priority high";priority.textContent=t.priority;
  row.append(top,detail,study,skip,priority,resourceLinks(t.source_ids));topics.append(row);
 });article.append(topics);p1Root.append(article);
});

const mixedRoot=document.querySelector("#ga-mixed-families");
D.ga_mixed_families.forEach(item=>{
 const card=document.createElement("article");card.className="family";
 const title=document.createElement("h3");title.textContent=item.family;
 const examples=document.createElement("p");examples.innerHTML=`<b>Examples in the supplied papers:</b> ${esc(item.examples)}`;
 const tested=document.createElement("p");tested.innerHTML=`<b>Typical fact tested:</b> ${esc(item.test)}`;
 const priority=document.createElement("span");priority.className="priority high";priority.textContent=item.priority;
 card.append(title,examples,tested,priority);mixedRoot.append(card);
});

const schemeTable=document.querySelector("#scheme-table");
schemeTable.innerHTML="<thead><tr><th>Scheme / policy family</th><th>What to know and what the papers probe</th></tr></thead>";
const schemeBody=document.createElement("tbody");
D.ga_scheme_checklist.forEach(([name,focus])=>{const row=document.createElement("tr");const left=document.createElement("td");left.innerHTML=`<b>${esc(name)}</b>`;const right=document.createElement("td");right.textContent=focus;row.append(left,right);schemeBody.append(row)});
schemeTable.append(schemeBody);

const reportRoot=document.querySelector("#ga-reports");
D.ga_reports_to_study.forEach(item=>{
 const card=document.createElement("article");card.className="report-card";
 const title=document.createElement("h3");const link=document.createElement("a");link.href=item.url;link.target="_blank";link.rel="noopener noreferrer";link.textContent=item.name;title.append(link);
 const meta=document.createElement("div");meta.className="report-meta";meta.textContent=`${item.tier} · ${item.publisher}`;
 const study=document.createElement("p");study.innerHTML=`<b>Read for:</b> ${esc(item.study)}`;
 const skip=document.createElement("p");skip.innerHTML=`<b>Skip/deprioritise:</b> ${esc(item.skip)}`;
 card.append(title,meta,study,skip);reportRoot.append(card);
});

const phaseTabs=document.querySelector("#phase-tabs");
const phaseChart=document.querySelector("#phase-chart");
const phaseTable=document.querySelector("#phase-trend-table");
const phaseColors=["#008b85","#3474ad","#ce871e","#b95a66","#667c8d","#856bb3","#42a37b","#a66d43","#3c8d9f","#827b54"];
let selectedSubject="General Awareness";
Object.keys(D.phase_one_guide).forEach((subject,index)=>{const button=document.createElement("button");button.textContent=subject;button.className=index===0?"active":"";button.addEventListener("click",()=>{selectedSubject=subject;phaseTabs.querySelectorAll("button").forEach(b=>b.classList.toggle("active",b===button));renderPhaseChart()});phaseTabs.append(button)});
function renderPhaseChart(){
 const rows=D.phase_one_guide[selectedSubject].topic_data.filter(t=>t.complete_cycle_total>0).sort((a,b)=>b.complete_cycle_total-a.complete_cycle_total);
 const width=940,height=320,left=250,right=48,top=18,rowH=30,innerW=width-left-right;
 phaseChart.setAttribute("viewBox",`0 0 ${width} ${top+rows.length*rowH+18}`);phaseChart.replaceChildren();
 const max=Math.max(1,...rows.map(r=>r.complete_cycle_total));
 rows.forEach((row,i)=>{
  const y=top+i*rowH;
  const label=document.createElementNS("http://www.w3.org/2000/svg","text");label.setAttribute("x",left-10);label.setAttribute("y",y+15);label.setAttribute("text-anchor","end");label.setAttribute("font-size","11");label.setAttribute("fill","#526778");label.textContent=row.topic;phaseChart.append(label);
  const bg=document.createElementNS("http://www.w3.org/2000/svg","rect");bg.setAttribute("x",left);bg.setAttribute("y",y+3);bg.setAttribute("width",innerW);bg.setAttribute("height",15);bg.setAttribute("rx",4);bg.setAttribute("fill","#edf1f3");phaseChart.append(bg);
  const bar=document.createElementNS("http://www.w3.org/2000/svg","rect");bar.setAttribute("x",left);bar.setAttribute("y",y+3);bar.setAttribute("width",innerW*row.complete_cycle_total/max);bar.setAttribute("height",15);bar.setAttribute("rx",4);bar.setAttribute("fill",phaseColors[i%phaseColors.length]);phaseChart.append(bar);
  const value=document.createElementNS("http://www.w3.org/2000/svg","text");value.setAttribute("x",left+innerW*row.complete_cycle_total/max+6);value.setAttribute("y",y+15);value.setAttribute("font-size","10");value.setAttribute("fill","#44596a");value.textContent=row.complete_cycle_total;phaseChart.append(value);
 });
 phaseTable.innerHTML="<thead><tr><th>Observed broad tag</th><th>2021</th><th>2022</th><th>2023</th><th>2024</th><th>2025*</th><th>2026</th><th class='num'>Included-cycle sum</th></tr></thead>";
 const body=document.createElement("tbody");
 D.phase_one_guide[selectedSubject].topic_data.slice().sort((a,b)=>b.complete_cycle_total-a.complete_cycle_total).forEach(row=>{
  const tr=document.createElement("tr");
  [row.topic,...D.years_p1.map(y=>row.annual[y]),row.complete_cycle_total].forEach((value,index)=>{const td=document.createElement("td");td.textContent=value;if(index===7)td.className="num";tr.append(td)});
  body.append(tr);
 });phaseTable.append(body);
}
renderPhaseChart();

function trendLabel(row){
 if(row.total===0)return "No clean separate count";
 if(row.subject==="ESI"&&row.chapter==="Growth and Development")return "Rising to 2024; lower in 2025";
 if(row.subject==="Finance"&&row.chapter==="Financial System")return "Strong 2025 increase";
 if(row.subject==="Finance"&&row.chapter==="Financial Markets")return "Mostly steady; 2024 bump";
 if(row.subject==="Management"&&row.chapter==="Fundamentals of Management and Organizational Behaviour")return "Recurring; objective tags eased";
 if(row.subject==="ESI"&&row.chapter==="Social Structure in India")return "Small, volatile; 2025 spike";
 if(row.subject==="ESI"&&row.chapter==="Globalization")return "Persistent, low-to-moderate";
 if(row.subject==="English Writing Skills")return "Same three formats in each cycle";
 if(row.chapter.includes("Corporate Governance + Workplace Ethics"))return "Sparse, cross-chapter joint tag";
 if(row.chapter.includes("Union Budget + Inflation"))return "Joint count; split unavailable";
 if(row.subject==="Finance"&&row.chapter.includes("Risk Management"))return "Joint count; variable";
 return "Recurring / coarse evidence";
}
const chapterRoot=document.querySelector("#phase2-chapters");
D.phase_two_guide.forEach(item=>{
 const details=document.createElement("details");details.className="chapter";details.dataset.search=[item.subject,item.chapter,item.subtopics,item.asked,item.priority].join(" ").toLowerCase();
 const summary=document.createElement("summary");
 const left=document.createElement("span");const subject=document.createElement("span");subject.className="small";subject.textContent=item.subject;const title=document.createElement("div");title.className="chapter-title";title.textContent=item.chapter;left.append(subject,title);
 const meta=document.createElement("span");meta.className="chapter-meta";
 meta.textContent=item.total?`${item.objective_total} objective · ${item.descriptive_total} descriptive`:item.priority;
 summary.append(left,meta);
 const body=document.createElement("div");body.className="chapter-body";
 const pri=document.createElement("p");const badge=document.createElement("span");badge.className=`priority ${item.priority.includes("Selective")||item.priority.includes("Medium")?"medium":""}`;badge.textContent=`${item.priority} · ${item.confidence} confidence`;pri.append(badge);
 const freq=document.createElement("p");freq.innerHTML=`<span class="strong">Five-cycle primary-tag frequency:</span> ${item.total?`${fmt(item.objective_total)} objective + ${fmt(item.descriptive_total)} descriptive = ${fmt(item.total)} total`:"No distinct reliable tag count; covered within broad or unclassified tags."}`;
 const annual=document.createElement("div");annual.className="annual";annual.textContent=item.total?D.phase_two_years.map(y=>`${y}: ${item.annual[y].objective}O/${item.annual[y].descriptive}D`).join(" · "):"Annual subtopic-specific count unavailable";
 const trend=document.createElement("p");trend.innerHTML=`<span class="strong">Trend:</span> ${esc(trendLabel(item))}.`;
 const sub=document.createElement("p");sub.className="subtopics";sub.innerHTML=`<b>Official syllabus scope:</b> ${esc(item.subtopics)}`;
 const ask=document.createElement("p");ask.className="ask";ask.innerHTML=`<b>What to be ready to do:</b> ${esc(item.asked)}`;
 const outlook=document.createElement("p");outlook.innerHTML=`<b>2027 relevance:</b> ${esc(item.forecast)}`;
 const minimum=document.createElement("p");minimum.innerHTML=`<b>What to study (minimum high-return preparation):</b> ${esc(item.minimum)}`;
 const skip=document.createElement("p");skip.className="topic-skip";skip.innerHTML=`<b>What not to study / deprioritise:</b> ${esc(item.do_not_study)}`;
 body.append(pri,freq,annual,trend,sub,ask,outlook,minimum,skip,resourceLinks(item.source_ids));details.append(summary,body);chapterRoot.append(details);
});
document.querySelector("#chapter-filter").addEventListener("input",e=>{const query=e.target.value.trim().toLowerCase();chapterRoot.querySelectorAll(".chapter").forEach(card=>card.hidden=!card.dataset.search.includes(query))});

const phase2Table=document.querySelector("#phase2-table");
phase2Table.innerHTML="<thead><tr><th>Subject / chapter or tag</th><th>Trend signal</th><th>2021</th><th>2022</th><th>2023</th><th>2024</th><th>2025</th><th class='num'>Five-year total (O+D)</th></tr></thead>";
const p2body=document.createElement("tbody");
D.phase_two_guide.forEach(item=>{
 const tr=document.createElement("tr");const label=document.createElement("td");label.innerHTML=`<b>${esc(item.chapter)}</b><div class="small">${esc(item.subject)}</div>`;tr.append(label);
 const trend=document.createElement("td");trend.textContent=trendLabel(item);tr.append(trend);
 for(const year of D.phase_two_years){const td=document.createElement("td");td.textContent=item.total?`${item.annual[year].objective} + ${item.annual[year].descriptive}`:"—";tr.append(td)}
 const total=document.createElement("td");total.className="num";total.textContent=item.total?`${item.objective_total} + ${item.descriptive_total} = ${item.total}`:"—";tr.append(total);p2body.append(tr)
});phase2Table.append(p2body);

const newsRoot=document.querySelector("#news-list");
D.current_affairs.forEach(item=>{
 const article=document.createElement("article");article.className="card news";
 const header=document.createElement("div");header.className="news-header";
 const title=document.createElement("div");title.className="news-title";title.textContent=item.topic;
 const date=document.createElement("div");date.className="news-date";date.textContent=`${item.date} · ${item.priority}`;
 header.append(title,date);
 const evidence=document.createElement("p");evidence.textContent=item.evidence;
 const map=document.createElement("div");map.className="news-map";map.textContent="Syllabus map: "+item.map;
 const study=document.createElement("p");study.textContent="Study angle: "+item.study;
 const links=document.createElement("div");links.className="news-links";
 [[item.source,item.url],[item.source2,item.url2]].forEach(([label,url])=>{const a=document.createElement("a");a.href=url;a.textContent=label;a.target="_blank";a.rel="noopener noreferrer";links.append(a)});
 article.append(header,evidence,map,study,links);newsRoot.append(article)
});

const gaps=document.querySelector("#gaps");
D.phase_two_gaps.forEach(row=>{const div=document.createElement("div");div.className="anomaly";div.innerHTML=`<b>${esc(row.year)} · ${esc(row.subject)} ${esc(row.section)}</b> — missing ${esc(row.missing_question_numbers||"none")}; repeated ${esc(row.duplicate_question_numbers||"none")}. ${esc(row.status)}.`;gaps.append(div)});
</script>
</body>
</html>"""
    content = content.replace("__TITLE__", html.escape(title))
    content = content.replace("__GENERATED__", html.escape(data["generated"]))
    content = content.replace("__CUTOFF__", html.escape(data["source_cutoff"]))
    content = content.replace("__DATA__", json_script(data))
    return content


def build_notes_graph_html(graph_data):
    template = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Interactive topic-to-material graph for the supplied RBI Grade B Phase II study PDFs.">
<title>Phase II Notes Graph | RBI Grade B</title>
<style>
:root{color-scheme:light;--ink:#172b3b;--muted:#607487;--line:#dfe7eb;--paper:#f3f6f7;--card:#fff;--navy:#102a3e;--teal:#007f78;--blue:#3474ad;--amber:#c9831d;--shadow:0 7px 22px rgba(19,42,59,.055)}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.5 "Segoe UI",Inter,system-ui,-apple-system,sans-serif}.shell{max-width:1500px;margin:auto;padding:22px}.hero{background:linear-gradient(125deg,#102a3e,#145b62);color:#fff;padding:22px 26px;border-radius:16px}.hero h1{font-size:clamp(26px,4vw,40px);margin:0 0 6px}.hero p{margin:0;color:#d6e5e9}.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}.toolbar input,.toolbar select,.toolbar button{font:inherit;border:1px solid var(--line);border-radius:8px;background:#fff;padding:9px 11px;color:var(--ink)}.toolbar input{flex:1;min-width:220px}.toolbar select{width:260px;max-width:100%;min-width:0}.toolbar button{cursor:pointer}.stats{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 14px}.stat{background:#fff;border:1px solid var(--line);border-radius:8px;padding:7px 10px;color:var(--muted);font-size:12px}.layout{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(310px,.85fr);gap:13px;align-items:start}.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);overflow:hidden}.panel h2{font-size:17px;margin:0;padding:14px 16px;border-bottom:1px solid var(--line)}.graph-caption{padding:10px 15px;color:var(--muted);font-size:12px}.graph{width:100%;height:min(76vh,760px);display:block;background:radial-gradient(#dfe8eb 1px,transparent 1px);background-size:18px 18px;touch-action:none}.edge{stroke:#b7c8ce;stroke-width:1.5;opacity:.62}.edge.highlight{stroke:var(--teal);stroke-width:2.8;opacity:.95}.node{cursor:pointer}.node-shape{stroke:#fff;stroke-width:2;filter:drop-shadow(0 2px 3px #18364820)}.node-label{font-size:11px;fill:#263f50;pointer-events:none}.document-node .node-label{font-size:9px}.node-label.selected{font-weight:800;fill:#006f69}.subject-node .node-shape{fill:#12374d}.topic-node .node-shape{fill:#07857d}.concept-node .node-shape{fill:#c9811a}.document-node .node-shape{fill:#7d6aa8}.other-node .node-shape{fill:#7d6aa8}.graph-note{padding:0 15px 13px;color:var(--muted);font-size:11px}.details{padding:14px 16px}.details h3{margin:0 0 4px;font-size:16px}.details .muted{color:var(--muted);font-size:12px;margin:4px 0 10px}.chips{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0}.chip{font-size:10px;border-radius:99px;background:#edf5f4;color:#24655f;padding:3px 7px}.materials{max-height:60vh;overflow:auto;display:grid;gap:8px;margin-top:10px;padding-right:3px}.material{padding:10px 11px;border:1px solid var(--line);border-radius:9px;background:#fff}.material a{font-weight:700;color:#126d79;text-decoration:none}.material a:hover{text-decoration:underline}.material p{margin:4px 0 0;color:#596c7a;font-size:11px}.empty{padding:12px;background:#f5f7f8;border-radius:8px;color:var(--muted);font-size:12px}.legend{display:flex;flex-wrap:wrap;gap:12px;padding:10px 15px;border-top:1px solid var(--line);font-size:11px;color:var(--muted)}.legend span{display:inline-flex;align-items:center;gap:6px}.swatch{width:10px;height:10px;border-radius:50%;display:inline-block}.warn{border-left:4px solid var(--amber);background:#fff4e1;padding:11px 13px;margin:12px 0;border-radius:7px;color:#664b22;font-size:12px}.back{color:#d8f1ed}.footer{color:var(--muted);font-size:11px;padding:14px 2px}
@media(max-width:850px){.shell{padding:12px}.toolbar>*{max-width:100%;min-width:0}.toolbar input{flex:1 1 100%;width:100%}.toolbar select{flex:1 1 145px;width:100%}.layout{grid-template-columns:1fr}.graph{height:56vh}.materials{max-height:48vh}}@media print{.toolbar{display:none}.layout{display:block}.panel{box-shadow:none;break-inside:avoid}.graph{height:700px}}
.layout{grid-template-columns:1fr}@media(min-width:1500px){.layout{grid-template-columns:minmax(0,1.65fr) minmax(350px,.85fr)}}.graph-scroll{max-height:78vh;overflow:auto;overscroll-behavior:contain;border-bottom:1px solid var(--line);background:radial-gradient(#dfe8eb 1px,transparent 1px);background-size:18px 18px}.graph{width:max-content;max-width:none;height:auto;touch-action:auto}.node-label{font-size:15px}.document-node .node-label{font-size:13px}.subject-node .node-label{fill:#fff}.graph-note{font-size:12px}.graph-scroll svg{display:block}.edge.related{stroke:#c9811a;stroke-dasharray:8 7}.edge.highlight{stroke-width:3.6;opacity:1}
.index-panel{margin-top:14px}.table-wrap{overflow:auto;max-height:75vh}.resource-table{width:100%;border-collapse:collapse;min-width:900px}.resource-table th,.resource-table td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.resource-table th{position:sticky;top:0;background:#f7fafb;color:#435b6c;font-size:12px;z-index:1}.resource-table td:first-child{font-weight:650}.resource-table button{font:inherit;text-align:left;border:0;background:none;color:#08766f;padding:0;cursor:pointer;font-weight:700}.resource-table button:hover{text-decoration:underline}.resource-table details summary{cursor:pointer;color:#126d79;font-weight:650}.table-materials{display:grid;gap:7px;min-width:240px;padding:8px 0}.table-materials a{color:#126d79;font-weight:650;text-decoration:none}.table-materials a:hover{text-decoration:underline}.table-materials span{display:block;color:var(--muted);font-size:11px}.table-count{padding:10px 13px;color:var(--muted);font-size:12px}.connection-summary{display:grid;gap:5px;min-width:200px;font-size:12px}.connection-summary span{color:#42596b}
.mindmap-tabs{display:flex;flex-wrap:wrap;gap:8px;padding:10px 14px;border-bottom:1px solid var(--line)}.mindmap-tabs button{border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--ink);padding:8px 13px;font:inherit;cursor:pointer}.mindmap-tabs button[aria-pressed="true"]{background:var(--navy);color:#fff;border-color:var(--navy)}.relation-guide{display:flex;flex-wrap:wrap;gap:9px;padding:10px 14px;border-bottom:1px solid var(--line);font-size:12px;color:var(--muted)}.relation-guide span{display:inline-flex;align-items:center;gap:6px}.line-key{width:24px;border-top:2px solid #3474ad}.line-key.related{border-top-style:dashed;border-color:#c9811a}.connection-list{display:grid;gap:7px;padding-left:18px;margin:9px 0 0}.connection-list li{font-size:12px;color:#42596b}.connection-list strong{color:#17665f}.selected-connection{fill:#fff;stroke:#fff;stroke-width:6px;paint-order:stroke;stroke-linejoin:round;font-size:13px;font-weight:700}
</style>
</head>
<body>
<main class="shell">
<header class="hero"><h1>Phase II notes: graph and study index</h1><p>Browse your notes, short notes, objective/descriptive practice and infographics by syllabus topic. Use the connected graph for relationships or the searchable table below for direct access to materials. The source PDFs stay in their original folder.</p><p style="margin-top:9px"><a class="back" href="rbi_grade_b_report.html">← Back to the RBI Grade B 2027 report</a> · <a class="back" href="#topic-index">Jump to topic table ↓</a></p></header>
<div class="toolbar">
 <input id="search" type="search" placeholder="Search a topic, concept, filename or resource type">
 <select id="subject-filter" aria-label="Filter by Phase II subject"><option value="">All Phase II subjects</option></select>
 <select id="type-filter" aria-label="Filter by material type"><option value="">All material types</option></select>
 <select id="topic-filter" aria-label="Filter by topic"><option value="">Choose a topic or concept</option></select>
 <button id="clear" type="button">Clear filters</button>
</div>
<div class="stats" id="stats"></div>
<div class="warn" id="coverage-note"></div>
<div class="layout">
 <section class="panel">
  <h2>Subject mind maps</h2>
  <div class="graph-caption">Choose one subject at a time. Each map shows the syllabus root, its topics, and related concepts. Study PDFs stay in the table and materials list to keep the map readable. Scroll inside the map vertically or horizontally when needed.</div>
  <div class="mindmap-tabs" id="mindmap-tabs" role="group" aria-label="Choose a subject mind map"></div>
  <div class="relation-guide"><span><i class="line-key"></i>Solid: official syllabus topic belongs to the subject</span><span><i class="line-key related"></i>Dashed: topic is cross-linked to a related concept</span><span>Select any node to see its direct connections below.</span></div>
  <div class="graph-scroll"><svg class="graph" id="graph" role="img" aria-label="Interactive graph of Phase II subjects, topics, and related concepts"></svg></div>
  <div class="legend"><span><i class="swatch" style="background:#12374d"></i>Subject</span><span><i class="swatch" style="background:#07857d"></i>Syllabus topic</span><span><i class="swatch" style="background:#c9811a"></i>Connected concept</span></div>
  <div class="graph-note" id="graph-note">Choose a node to see exactly what it connects to; use the table below for study material PDFs.</div>
 </section>
 <aside class="panel">
  <h2 id="material-heading">Matching study materials</h2>
  <div class="details" id="details"><div class="empty">Select a subject, topic or concept to inspect its direct connections and linked resources.</div></div>
  <div class="details"><div id="materials-count" class="muted"></div><div class="materials" id="materials"></div></div>
 </aside>
</div>
<section class="panel index-panel" id="topic-index" aria-labelledby="index-heading">
 <h2 id="index-heading">Topic-to-materials table</h2>
 <div class="graph-caption">A simpler index of syllabus topics and connected concepts. Expand a row to open its PDFs; use the filters above to narrow the list.</div>
 <div class="table-count" id="table-count" aria-live="polite"></div>
 <div class="table-wrap"><table class="resource-table">
  <thead><tr><th scope="col">Phase II subject</th><th scope="col">Topic or concept</th><th scope="col">Kind</th><th scope="col">How it connects</th><th scope="col">Matching materials</th></tr></thead>
  <tbody id="resource-table-body"></tbody>
 </table></div>
</section>
<footer class="footer">Each PDF is represented as a resource record and linked to its likely syllabus topics using filename, metadata and extractable text. Classification confidence varies by PDF quality and source detail; inspect the original file when a connection is marked tentative. No question stems or answer keys are reproduced here.</footer>
</main>
<script>
const G=__GRAPH_DATA__;
const nodes=Array.isArray(G.nodes)?G.nodes:[];
const edges=Array.isArray(G.edges)?G.edges:[];
const nodeMap=new Map(nodes.map(n=>[String(n.id),n]));
const edgeEnds=e=>[String(e.source??e.from??""),String(e.target??e.to??"")];
const norm=s=>String(s??"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
const valueList=v=>Array.isArray(v)?v.map(String):v?[String(v)]:[];
const typeOf=n=>String(n.type??n.kind??"other").toLowerCase();
const isDoc=n=>["document","resource","file","pdf","material"].some(x=>typeOf(n).includes(x));
const isSubject=n=>typeOf(n).includes("subject")||typeOf(n).includes("paper");
const isTopic=n=>typeOf(n).includes("topic")||typeOf(n).includes("chapter")||typeOf(n).includes("syllabus");
const labelOf=n=>String(n.label??n.name??n.title??n.filename??n.id);
const subjectsFor=n=>valueList(n.subjects??n.subject??n.phase_two_subject);
const topicsFor=n=>valueList(n.topics??n.topic??n.subtopics);
const mappedTopicLabels=n=>topicsFor(n).map(id=>labelOf(nodeMap.get(String(id))??{id}));
const docs=nodes.filter(isDoc);
const graphNodes=nodes.filter(n=>!isDoc(n));
const subjectNodes=graphNodes.filter(isSubject);
const topicNodes=graphNodes.filter(isTopic);
const conceptNodes=graphNodes.filter(n=>!isSubject(n)&&!isTopic(n));
const subjectNames=[...new Set([...subjectNodes.map(labelOf),...docs.flatMap(subjectsFor)])].sort();
const materialTypes=[...new Set(docs.map(n=>String(n.resource_type??n.material_type??n.category??"Other")))].sort();
const $=s=>document.querySelector(s), svg=$("#graph"), detail=$("#details"), materials=$("#materials");
const subjectSelect=$("#subject-filter"), typeSelect=$("#type-filter"), topicSelect=$("#topic-filter"), search=$("#search");
subjectNames.forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;subjectSelect.append(o)});
const initialSubject=labelOf(subjectNodes[0]??{label:subjectNames[0]??""});
const tabs=$("#mindmap-tabs");
subjectNames.forEach((name,index)=>{
 const button=document.createElement("button");
 button.type="button";button.textContent=name;button.dataset.subject=name;
 button.setAttribute("aria-pressed",String(name===initialSubject));
 button.addEventListener("click",()=>{
  subjectSelect.value=name;topicSelect.value="";activeId="";
  tabs.querySelectorAll("button").forEach(tab=>tab.setAttribute("aria-pressed",String(tab.dataset.subject===name)));
  renderGraph();renderMaterials();renderTable();
 });
 tabs.append(button);
});
materialTypes.forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;typeSelect.append(o)});
const topicChoices=[...topicNodes,...conceptNodes].sort((a,b)=>labelOf(a).localeCompare(labelOf(b)));
topicChoices.forEach(n=>{const o=document.createElement("option");o.value=String(n.id);o.textContent=labelOf(n);topicSelect.append(o)});
const meta=G.metadata??{};
const counts=meta.counts??{};
[
 `${docs.length} PDFs indexed`,
 `${topicNodes.length} syllabus topic nodes`,
 `${conceptNodes.length} connected concepts`,
 `${edges.length} relationships`,
 `${subjectNames.length} subject groupings`
].forEach(t=>{const e=document.createElement("span");e.className="stat";e.textContent=t;$("#stats").append(e)});
const topicLinkedDocs=new Set(edges.filter(e=>isDoc(nodeMap.get(String(e.source))??{})&&isTopic(nodeMap.get(String(e.target))??{})).map(e=>String(e.source)));
const failedExtraction=(counts.documents_with_no_ocr_text??0)+(counts.pdf_open_or_page_failure_count??0);
$("#coverage-note").textContent=`Coverage: ${counts.document_count??docs.length} PDFs inventoried; ${topicLinkedDocs.size} linked to syllabus topics. ${counts.official_syllabus_topic_node_count??topicNodes.length} official syllabus topics represented; ${counts.topic_document_link_counts?Object.values(counts.topic_document_link_counts).filter(v=>v>0).length:topicNodes.filter(n=>assocIds(n).some(id=>isDoc(nodeMap.get(id)??{}))).length} have at least one linked PDF. ${counts.native_text_layer_missing_count??0} needed scan/OCR handling; ${failedExtraction} ended with no recoverable text or a read/page failure. ${counts.ambiguous_document_count??0} documents have an ambiguous classification; check low-confidence matches against the original.`;
const related=new Map();
edges.forEach(e=>{const [a,b]=edgeEnds(e);if(!a||!b)return;for(const [x,y] of [[a,b],[b,a]]){if(!related.has(x))related.set(x,new Set());related.get(x).add(y)}});
function assocIds(n){
 const ids=new Set(related.get(String(n.id))??[]);
 if(!isDoc(n)&&!isTopic(n)){
  [...ids].forEach(id=>{
   const neighbor=nodeMap.get(id);
   if(neighbor&&(!isDoc(neighbor)||isTopic(neighbor))){
    (related.get(id)??new Set()).forEach(next=>{if(isDoc(nodeMap.get(next)??{}))ids.add(next)});
   }
  });
 }
 const names=[norm(labelOf(n)),...topicsFor(n).map(norm)];
 docs.forEach(d=>{
  if((related.get(String(d.id))??new Set()).has(String(n.id)))ids.add(String(d.id));
  const vals=[...mappedTopicLabels(d),...subjectsFor(d)].map(norm);
  if(names.some(v=>v&&vals.includes(v)))ids.add(String(d.id));
 });
 return [...ids].filter(id=>nodeMap.has(id));
}
function subjectForTopic(n){
 const direct=[...related.get(String(n.id))??[]].map(id=>nodeMap.get(id)).filter(Boolean).filter(isSubject);
 if(direct.length)return labelOf(direct[0]);
 const parentTopic=!isTopic(n)?[...related.get(String(n.id))??[]].map(id=>nodeMap.get(id)).filter(Boolean).find(isTopic):null;
 if(parentTopic)return subjectForTopic(parentTopic);
 const stated=subjectsFor(n);if(stated.length)return stated[0];
 const docSubjects=assocIds(n).map(id=>nodeMap.get(id)).filter(Boolean).flatMap(subjectsFor);
 return docSubjects[0]??subjectNames[0]??"";
}
function relationName(edge,current,other){
 if(edge.type==="part_of")return isSubject(current)?"Contains official syllabus topic":"Official syllabus topic within";
 if(edge.type==="cross_link")return isTopic(other)?"Cross-linked to topic":"Cross-linked to related concept";
 if(edge.type==="covers_topic")return isDoc(current)?"Study PDF mapped to topic":"Topic mapped to study PDF";
 if(edge.type==="belongs_to_subject")return isDoc(current)?"Study PDF belongs to subject":"Subject includes study PDF";
 if(edge.type==="duplicate_content")return "Duplicate-content link";
 return String(edge.label??edge.type??"Connected to");
}
function connectionRows(n,includeDocuments=false){
 return edges.flatMap(edge=>{
  const [a,b]=edgeEnds(edge);
  const otherId=a===String(n.id)?b:b===String(n.id)?a:"";
  if(!otherId)return [];
  const other=nodeMap.get(otherId);
  if(!other||(!includeDocuments&&isDoc(other)))return [];
  return [{edge,other,relation:relationName(edge,n,other)}];
 });
}
function connectionSummary(n){
 const rows=connectionRows(n);
 if(!rows.length)return ["No other graph node linked"];
 return rows.map(({relation,other})=>`${relation} → ${labelOf(other)}`);
}
function topicKeyForDoc(d){
 const linked=[...related.get(String(d.id))??[]].map(id=>nodeMap.get(id)).filter(Boolean).filter(isTopic);
 const stated=topicsFor(d).map(t=>topicNodes.find(n=>norm(labelOf(n))===norm(t)||String(n.id)===t)).filter(Boolean);
 return linked[0]??stated[0]??null;
}
let activeId="";
function nodeClass(n){return isDoc(n)?"document-node":isSubject(n)?"subject-node":isTopic(n)?"topic-node":typeOf(n).includes("concept")?"concept-node":"other-node"}
function renderGraph(){
 svg.replaceChildren();
 const chosenSubject=subjectSelect.value||initialSubject;
 const root=subjectNodes.find(n=>norm(labelOf(n))===norm(chosenSubject));
 const visibleTopics=topicNodes.filter(n=>subjectForTopic(n)===chosenSubject).sort((a,b)=>labelOf(a).localeCompare(labelOf(b)));
 const visibleTopicIds=new Set(visibleTopics.map(n=>String(n.id)));
 const visibleConcepts=conceptNodes.filter(n=>subjectForTopic(n)===chosenSubject&&[...(related.get(String(n.id))??[])].some(id=>visibleTopicIds.has(id))).sort((a,b)=>{
  const yFor=n=>[...(related.get(String(n.id))??[])].map(id=>visibleTopics.find(t=>String(t.id)===id)).filter(Boolean).map(t=>labelOf(t)).sort()[0]??"";
  return yFor(a).localeCompare(yFor(b))||labelOf(a).localeCompare(labelOf(b));
 });
 const visibleGraphNodes=[...(root?[root]:[]),...visibleTopics,...visibleConcepts];
 const positions=new Map();
 const rowGap=92,top=105;
 visibleTopics.forEach((n,i)=>positions.set(String(n.id),{x:680,y:top+i*rowGap}));
 if(root)positions.set(String(root.id),{x:170,y:top+Math.max(0,visibleTopics.length-1)*rowGap/2});
 visibleConcepts.forEach((n,i)=>positions.set(String(n.id),{x:1370,y:top+i*rowGap}));
 const graphHeight=Math.max(visibleTopics.length,visibleConcepts.length,1)*rowGap+190;
 const graphWidth=2250;
 svg.setAttribute("viewBox",`0 0 ${graphWidth} ${graphHeight}`);
 svg.setAttribute("width",String(graphWidth));
 svg.setAttribute("height",String(graphHeight));
 const visible=visibleGraphNodes;
 const visibleIds=new Set(visible.map(n=>String(n.id)));
 const ns="http://www.w3.org/2000/svg";
 const edgeLayer=document.createElementNS(ns,"g");
 edges.forEach(e=>{
  if(!["part_of","cross_link"].includes(String(e.type)))return;
  const [a,b]=edgeEnds(e);if(!visibleIds.has(a)||!visibleIds.has(b))return;
  const p=positions.get(a),r=positions.get(b);if(!p||!r)return;
  const line=document.createElementNS(ns,"line");line.setAttribute("x1",p.x);line.setAttribute("y1",p.y);line.setAttribute("x2",r.x);line.setAttribute("y2",r.y);line.setAttribute("class",`edge${e.type==="cross_link"?" related":""}${a===activeId||b===activeId?" highlight":""}`);edgeLayer.append(line);
 });
 svg.append(edgeLayer);
 visible.forEach(n=>{
  const isDocument=isDoc(n);
  const p=positions.get(String(n.id));if(!p)return;
  const group=document.createElementNS(ns,"g");group.setAttribute("class",`node ${nodeClass(n)}`);group.setAttribute("transform",`translate(${p.x},${p.y})`);
  const shape=document.createElementNS(ns,isSubject(n)?"rect":"circle");
  if(isSubject(n)){shape.setAttribute("x",-130);shape.setAttribute("y",-31);shape.setAttribute("width",260);shape.setAttribute("height",62);shape.setAttribute("rx",13)}
  else{shape.setAttribute("r",isDocument?9:isTopic(n)?13:10)}
  shape.setAttribute("class","node-shape");group.append(shape);
  const text=document.createElementNS(ns,"text");
  text.setAttribute("class",`node-label${String(n.id)===activeId?" selected":""}`);
  const centered=isSubject(n);
  const labelX=centered?0:isDocument?18:22;
  text.setAttribute("x",labelX);
  text.setAttribute("text-anchor",centered?"middle":"start");
  const maxChars=isSubject(n)?23:isDocument?64:54;
  const words=labelOf(n).split(/\s+/);
  const lines=[];
  let line="";
  words.forEach(word=>{
   if(line&&`${line} ${word}`.length>maxChars){lines.push(line);line=word}else line=line?`${line} ${word}`:word;
  });
  if(line)lines.push(line);
  const lineHeight=19;
  text.setAttribute("y",-((lines.length-1)*lineHeight)/2+5);
  lines.forEach((value,i)=>{
   const tspan=document.createElementNS(ns,"tspan");
   tspan.setAttribute("x",labelX);
   if(i)tspan.setAttribute("dy",String(lineHeight));
   tspan.textContent=value;
   text.append(tspan);
  });
  group.append(text);
  const title=document.createElementNS(ns,"title");title.textContent=`${labelOf(n)} · ${typeOf(n)}`;group.append(title);
  group.addEventListener("click",()=>selectNode(n));svg.append(group);
 });
 $("#graph-note").textContent=`${chosenSubject}: ${visibleTopics.length} syllabus topic(s) and ${visibleConcepts.length} cross-linked concept(s). PDF nodes are intentionally kept in the expandable study index to make the mind map easier to read. Select a node to see its direct connections.`;
}
function safePath(p){
 const clean=String(p??"").replace(/\\/g,"/").replace(/^\/+/,"");
 const parts=clean.split("/");
 if(parts[0]!=="SubjectNotesForPhase2"||parts.some(part=>!part||part==="."||part===".."))return "#";
 return "../"+parts.map(encodeURIComponent).join("/");
}
function docsMatching(){
 const chosen=topicSelect.value||activeId;
 const selected=chosen?nodeMap.get(String(chosen)):null;
 const sub=subjectSelect.value;
 const material=typeSelect.value;
 const q=norm(search.value);
 let candidates=selected?(isDoc(selected)?[selected]:assocIds(selected).map(id=>nodeMap.get(id)).filter(isDoc)):docs;
 if(selected&&isSubject(selected))candidates=docs.filter(d=>subjectsFor(d).some(s=>norm(s)===norm(labelOf(selected))));
 if(sub)candidates=candidates.filter(d=>subjectsFor(d).some(s=>norm(s)===norm(sub))||(selected&&!isDoc(selected)&&norm(subjectForTopic(selected))===norm(sub)));
 if(material)candidates=candidates.filter(d=>String(d.resource_type??d.material_type??d.category??"Other")===material);
 if(q)candidates=candidates.filter(d=>norm(`${labelOf(d)} ${d.path??d.relative_path??""} ${Array.isArray(d.notes)?d.notes.join(" "):d.notes??""} ${subjectsFor(d).join(" ")} ${mappedTopicLabels(d).join(" ")}`).includes(q));
 return [...new Map(candidates.map(d=>[String(d.id),d])).values()].sort((a,b)=>labelOf(a).localeCompare(labelOf(b)));
}
function selectNode(n){
 activeId=String(n.id);topicSelect.value=isDoc(n)?"":activeId;
 if(!isDoc(n)){
  subjectSelect.value=isSubject(n)?labelOf(n):subjectForTopic(n);
  tabs.querySelectorAll("button").forEach(tab=>tab.setAttribute("aria-pressed",String(tab.dataset.subject===subjectSelect.value)));
 }
 const connected=assocIds(n).map(id=>nodeMap.get(id)).filter(isDoc);
 const briefNotes=Array.isArray(n.notes)?n.notes.slice(0,2).join("; "):String(n.notes??"");
 const metaLines=[n.type??"Node",subjectsFor(n).join(" · "),mappedTopicLabels(n).join(" · "),n.description??briefNotes].filter(Boolean);
 detail.replaceChildren();
 const h=document.createElement("h3");h.textContent=labelOf(n);detail.append(h);
 const desc=document.createElement("div");desc.className="muted";desc.textContent=metaLines.join(" · ");detail.append(desc);
 const connections=document.createElement("div");
 const connectionHeading=document.createElement("strong");connectionHeading.textContent="How this node connects";connections.append(connectionHeading);
 const connectionList=document.createElement("ul");connectionList.className="connection-list";
 const nodeConnections=connectionRows(n);
 if(nodeConnections.length){
  nodeConnections.forEach(({edge,other,relation})=>{
   const item=document.createElement("li"),label=document.createElement("strong");
   label.textContent=relation+" ";item.append(label);
   const neighbor=document.createElement("button");neighbor.type="button";neighbor.textContent=labelOf(other);neighbor.addEventListener("click",()=>selectNode(other));item.append(neighbor);
   if(edge.type==="cross_link"&&edge.label){const context=document.createElement("div");context.className="muted";context.textContent=edge.label;item.append(context)}
   connectionList.append(item);
  });
 }else{
  const item=document.createElement("li");item.textContent="No direct subject/topic/concept link recorded.";connectionList.append(item);
 }
 connections.append(connectionList);detail.append(connections);
 const chips=document.createElement("div");chips.className="chips";
 [...subjectsFor(n),...topicsFor(n)].forEach(v=>{const c=document.createElement("span");c.className="chip";c.textContent=v;chips.append(c)});
 if(chips.childNodes.length)detail.append(chips);
 if(isDoc(n)){
  const a=document.createElement("a");a.href=safePath(n.path??n.relative_path??n.file_path??"");a.target="_blank";a.rel="noopener noreferrer";a.textContent="Open original PDF ↗";detail.append(a);
 }
 $("#materials-count").textContent=`${connected.length} directly connected PDF(s)${connected.length?" · choose a material below to open its original file":""}`;
 renderGraph();renderMaterials();
}
function renderMaterials(){
 const list=docsMatching();materials.replaceChildren();
 $("#materials-count").textContent=`${list.length} matching PDF resource(s)`;
 if(!list.length){const empty=document.createElement("div");empty.className="empty";empty.textContent="No matching PDFs. Clear a filter or choose another topic.";materials.append(empty);return}
 list.forEach(d=>{
  const card=document.createElement("article");card.className="material";
  const a=document.createElement("a");a.href=safePath(d.path??d.relative_path??d.file_path??"");a.target="_blank";a.rel="noopener noreferrer";a.textContent=labelOf(d);card.append(a);
  const metaText=[d.resource_type??d.material_type??"PDF",d.page_count?`${d.page_count} pages`:"",d.confidence?`match ${d.confidence}`:""].filter(Boolean).join(" · ");
  const p=document.createElement("p");p.textContent=metaText;card.append(p);
  const topics=mappedTopicLabels(d);if(topics.length){const t=document.createElement("p");t.textContent="Mapped to: "+topics.join(" · ");card.append(t)}
  if(d.notes){const noteText=Array.isArray(d.notes)?d.notes.slice(0,2).join("; "):String(d.notes);if(noteText){const notes=document.createElement("p");notes.textContent=noteText.slice(0,280);card.append(notes)}}
  materials.append(card);
 });
}
function renderTable(){
 const body=$("#resource-table-body");
 body.replaceChildren();
 const query=norm(search.value);
 const selectedId=topicSelect.value||activeId;
 const selectedNode=selectedId?nodeMap.get(String(selectedId)):null;
 const candidates=[...topicNodes,...conceptNodes]
  .filter(n=>!subjectSelect.value||subjectForTopic(n)===subjectSelect.value||subjectsFor(n).includes(subjectSelect.value))
  .filter(n=>!selectedNode||String(n.id)===String(selectedNode.id)||isSubject(selectedNode)&&subjectForTopic(n)===labelOf(selectedNode));
 const rows=candidates.map(n=>{
  let linked=assocIds(n).map(id=>nodeMap.get(id)).filter(isDoc);
  if(typeSelect.value)linked=linked.filter(d=>String(d.resource_type??d.material_type??d.category??"Other")===typeSelect.value);
  if(query&&!norm(`${labelOf(n)} ${subjectsFor(n).join(" ")} ${linked.map(labelOf).join(" ")}`).includes(query)){
   linked=linked.filter(d=>norm(`${labelOf(d)} ${d.path??d.relative_path??""} ${Array.isArray(d.notes)?d.notes.join(" "):d.notes??""}`).includes(query));
   if(!linked.length)return null;
  }
  return {node:n,linked};
 }).filter(Boolean).filter(row=>!typeSelect.value||row.linked.length);
 rows.sort((a,b)=>subjectForTopic(a.node).localeCompare(subjectForTopic(b.node))||labelOf(a.node).localeCompare(labelOf(b.node)));
 $("#table-count").textContent=`Showing ${rows.length} topic/concept rows · ${rows.reduce((sum,row)=>sum+row.linked.length,0)} matching topic-material links`;
 if(!rows.length){
  const tr=document.createElement("tr"),td=document.createElement("td");
  td.colSpan=5;td.className="empty";td.textContent="No matching topics. Clear a filter or try a broader search.";tr.append(td);body.append(tr);return;
 }
 rows.forEach(({node,linked})=>{
  const tr=document.createElement("tr");
  const subjectCell=document.createElement("td");subjectCell.textContent=subjectForTopic(node);tr.append(subjectCell);
  const nameCell=document.createElement("td");
  const choose=document.createElement("button");choose.type="button";choose.textContent=labelOf(node);
  choose.addEventListener("click",()=>selectNode(node));nameCell.append(choose);tr.append(nameCell);
  const kindCell=document.createElement("td");kindCell.textContent=isTopic(node)?"Syllabus topic":"Connected concept";tr.append(kindCell);
  const connectionCell=document.createElement("td"),connectionList=document.createElement("div");connectionList.className="connection-summary";
  connectionSummary(node).forEach(text=>{const line=document.createElement("span");line.textContent=text;connectionList.append(line)});
  connectionCell.append(connectionList);tr.append(connectionCell);
  const materialsCell=document.createElement("td");
  if(!linked.length){materialsCell.textContent="No matching PDFs";tr.append(materialsCell);body.append(tr);return}
  const disclosure=document.createElement("details");
  const summary=document.createElement("summary");summary.textContent=`${linked.length} PDF${linked.length===1?"":"s"} — expand`;disclosure.append(summary);
  let populated=false;
  disclosure.addEventListener("toggle",()=>{
   if(!disclosure.open||populated)return;
   populated=true;
   const list=document.createElement("div");list.className="table-materials";
   linked.forEach(doc=>{
    const item=document.createElement("div");
    const link=document.createElement("a");link.href=safePath(doc.path??doc.relative_path??doc.file_path??"");link.target="_blank";link.rel="noopener noreferrer";link.textContent=labelOf(doc);item.append(link);
    const meta=document.createElement("span");meta.textContent=[doc.resource_type??doc.material_type??"PDF",doc.page_count?`${doc.page_count} pages`:"",doc.confidence?`match ${doc.confidence}`:""].filter(Boolean).join(" · ");item.append(meta);
    list.append(item);
   });
   disclosure.append(list);
  });
  materialsCell.append(disclosure);tr.append(materialsCell);body.append(tr);
 });
}
function applyFilters(){
 const tid=topicSelect.value;
 if(tid){const n=nodeMap.get(tid);if(n){selectNode(n);renderTable();return}}
 renderGraph();renderMaterials();renderTable();
}
subjectSelect.addEventListener("change",()=>{topicSelect.value="";activeId="";tabs.querySelectorAll("button").forEach(tab=>tab.setAttribute("aria-pressed",String(tab.dataset.subject===(subjectSelect.value||initialSubject))));renderGraph();renderMaterials();renderTable()});
typeSelect.addEventListener("change",()=>{renderMaterials();renderTable()});
topicSelect.addEventListener("change",applyFilters);
search.addEventListener("input",()=>{renderGraph();renderMaterials();renderTable()});
$("#clear").addEventListener("click",()=>{search.value="";subjectSelect.value="";typeSelect.value="";topicSelect.value="";activeId="";tabs.querySelectorAll("button").forEach(tab=>tab.setAttribute("aria-pressed",String(tab.dataset.subject===initialSubject)));detail.innerHTML='<div class="empty">Select a subject, topic or concept to inspect its direct connections and linked resources.</div>';renderGraph();renderMaterials();renderTable()});
renderGraph();renderMaterials();renderTable();
</script>
</body>
</html>"""
    return template.replace("__GRAPH_DATA__", json_script(graph_data))


def validate_notes_graph(graph_data):
    nodes = graph_data["nodes"]
    edges = graph_data["edges"]
    ids = [str(node.get("id", "")) for node in nodes]
    if not all(ids) or len(ids) != len(set(ids)):
        raise ValueError(f"Notes graph node IDs are missing or duplicated: {NOTES_GRAPH_DATA_FILE}")
    node_ids = set(ids)
    invalid_edges = [
        edge for edge in edges
        if str(edge.get("source", "")) not in node_ids
        or str(edge.get("target", "")) not in node_ids
    ]
    if invalid_edges:
        raise ValueError(
            f"Notes graph contains {len(invalid_edges)} edge(s) with missing endpoints: "
            f"{NOTES_GRAPH_DATA_FILE}"
        )

    notes_folder = (WORKSPACE / "SubjectNotesForPhase2").resolve()
    document_nodes = [
        node for node in nodes
        if any(kind in str(node.get("type", "")).lower()
               for kind in ("document", "resource", "file", "pdf", "material"))
    ]
    document_ids = {str(node["id"]) for node in document_nodes}
    linked_ids = defaultdict(set)
    for edge in edges:
        source, target = str(edge["source"]), str(edge["target"])
        linked_ids[source].add(target)
        linked_ids[target].add(source)
    unconnected_documents = [
        node["id"] for node in document_nodes
        if not (linked_ids[str(node["id"])] - document_ids)
    ]
    if unconnected_documents:
        raise ValueError(
            f"{len(unconnected_documents)} PDF node(s) are not linked to any topic/concept: "
            f"{NOTES_GRAPH_DATA_FILE}"
        )
    for node in document_nodes:
        raw_path = str(node.get("path", "")).replace("\\", "/")
        path = Path(raw_path)
        if not raw_path or path.is_absolute():
            raise ValueError(f"Invalid document path for graph node {node['id']}: {raw_path!r}")
        if path.parts[0] != "SubjectNotesForPhase2" or any(
            part in {"", ".", ".."} for part in path.parts
        ):
            raise ValueError(f"Document path is outside the notes folder: {raw_path!r}")
        source = (WORKSPACE / path).resolve()
        try:
            source.relative_to(notes_folder)
        except ValueError as exc:
            raise ValueError(f"Document path is outside the notes folder: {raw_path!r}") from exc
        if source.suffix.lower() != ".pdf" or not source.is_file():
            raise FileNotFoundError(f"Notes graph PDF does not exist: {source}")
        node["path"] = path.as_posix()
    metadata = graph_data.get("metadata", {})
    counts = metadata.get("counts", {})
    scanned = counts.get(
        "document_count",
        metadata.get("files_scanned", metadata.get("pdf_count")),
    )
    if scanned is not None and int(scanned) != len(document_nodes):
        raise ValueError(
            f"Graph metadata lists {scanned} scanned PDFs but contains "
            f"{len(document_nodes)} document nodes: {NOTES_GRAPH_DATA_FILE}"
        )
    return len(document_nodes)


def main():
    from build_question_bank import build_html as build_question_bank_html

    if not NOTES_GRAPH_DATA_FILE.is_file():
        raise FileNotFoundError(
            f"Phase II notes graph data not found: {NOTES_GRAPH_DATA_FILE}"
        )
    graph_data = json.loads(NOTES_GRAPH_DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(graph_data.get("nodes"), list) or not isinstance(
        graph_data.get("edges"), list
    ):
        raise ValueError(f"Invalid notes graph structure: {NOTES_GRAPH_DATA_FILE}")
    document_count = validate_notes_graph(graph_data)
    data = build_data()
    content = build_html(data)
    graph_content = build_notes_graph_html(graph_data)
    question_data_file = REPORT_DIR / "phase1_question_bank.json"
    if not question_data_file.is_file():
        raise FileNotFoundError(
            f"Generate the Phase I question excerpts with build_question_bank.py first: "
            f"{question_data_file}"
        )
    question_data = json.loads(question_data_file.read_text(encoding="utf-8"))
    for question in question_data["questions"]:
        for path in question["images"] + question["contexts"]:
            if not (REPORT_DIR / path).is_file():
                raise FileNotFoundError(f"Question excerpt not found: {REPORT_DIR / path}")
    question_content = build_question_bank_html(question_data["questions"], question_data["audit"])
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(content, encoding="utf-8")
    NOTES_GRAPH_FILE.write_text(graph_content, encoding="utf-8")
    (REPORT_DIR / "phase1_question_bank.html").write_text(question_content, encoding="utf-8")
    print(f"Wrote {REPORT_FILE} ({REPORT_FILE.stat().st_size:,} bytes)")
    print(f"Wrote {NOTES_GRAPH_FILE} ({NOTES_GRAPH_FILE.stat().st_size:,} bytes)")
    print(f"Mapped {document_count:,} Phase II note PDFs")
    print(f"Published {len(question_data['questions']):,} Phase I practice questions")


if __name__ == "__main__":
    main()
