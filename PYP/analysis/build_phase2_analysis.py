"""Build syllabus-wide Phase II study analysis and traceable descriptive audits.

Run with Python and PyMuPDF. Data below are paraphrased from the supplied papers;
priorities and practice thresholds are recommendations, not official rubrics.

Run with --html-only to preserve the original subject PDFs while updating the
combined HTML, chapter roadmap and evidence inventories. The extension requires
the persisted objective/descriptive weightage CSVs and essay-theme audit in
PYP_Analysis. It validates complete question and supplied-chapter coverage before
publishing. Validate with python -m unittest discover -s PYP\\analysis -p test_phase2_evidence.py.
The modern reader embeds phase2_report.css and phase2_report.js, so search,
subject navigation, text-size controls and printing work entirely offline.
The topper section embeds the persisted rbi_topper_tips_traps_evidence.json review,
including its partial-coverage caveat, source register and practical recommendations.
"""

import argparse
import csv
import html
import json
from pathlib import Path

import pymupdf

from build_question_pdfs import Book, OUTPUT, BOTTOM
from phase2_evidence_inventory import render_evidence_extension
from phase2_chapter_roadmap import render_chapter_roadmap
from phase2_topper_findings import render_topper_findings


ROOT = OUTPUT.parent
YEARS = range(2021, 2026)
PAGES = {
    2021: {"English": (70, 72), "ESI": (73, 82), "FM": (83, 90)},
    2022: {"English": (65, 69), "ESI": (70, 80), "FM": (81, 89)},
    2023: {"English": (71, 73), "ESI": (74, 84), "FM": (85, 93)},
    2024: {"English": (68, 71), "ESI": (72, 82), "FM": (83, 92)},
    2025: {"English": (65, 68), "ESI": (69, 80), "FM": (81, 90)},
}

# Six available prompts per year, not six attempted answers.
DESCRIPTIVE = {
    "ESI": {
        2021: [
            ("Public finance", "Finance Commission horizontal and vertical transfers"),
            ("Poverty and measurement", "Poverty measures: merits, limitations and safety nets"),
            ("Globalisation", "Changes in globalisation after the 2008 financial crisis"),
            ("Reforms and public finance", "Strategic/non-strategic disinvestment: rationale and impact"),
            ("Social structure", "Demography and economic transition"),
            ("Climate and development", "Climate commitments alongside development and health needs"),
        ],
        2022: [
            ("Social structure", "Protective discrimination amid urbanisation, caste and gender inequality"),
            ("Reforms", "Economic-policy reforms since the 1990s"),
            ("Financial resilience", "FSR-linked resilience, pandemic challenges and reforms"),
            ("Employment and enterprise", "Rural entrepreneurship and social problems"),
            ("Monetary policy", "India's monetary-policy framework"),
            ("Financial system", "NBFCs versus banks and NBFC categories"),
        ],
        2023: [
            ("Social structure", "Gender sensitisation linked to UNDP strategy and social norms"),
            ("Social structure and globalisation", "Migration policy and World Development Report recommendations"),
            ("Climate and development", "Currency and Finance report: climate macro-effects and global cooperation"),
            ("Poverty and employment", "Three poverty-alleviation/employment programmes"),
            ("Monetary policy", "Monetary policy and at least eight instruments"),
            ("Employment and enterprise", "Startup constraints in tier-2/3 cities"),
        ],
        2024: [
            ("Employment", "Youth employment: challenges and solutions"),
            ("Digital development", "Budget digital initiatives and the Digital India journey"),
            ("Climate and development", "Growth versus sustainable-development tensions"),
            ("Social structure", "Women-led rural development"),
            ("Industry", "Industrial-corridor objectives and significance"),
            ("Digital finance", "Benefits and risks of AI in banking"),
        ],
        2025: [
            ("Welfare and development", "Quality welfare in relation to a World Development Report"),
            ("Social structure", "Beijing+30 priorities and the Gender Snapshot"),
            ("Climate, poverty and growth", "Environment, poverty and growth linkages in sustainable development"),
            ("Urbanisation", "Smart cities and inclusive urban growth, including Visakhapatnam"),
            ("Monetary policy", "A specified monetary-policy assessment and its growth/credit implications"),
            ("Social structure", "Multiculturalism: opportunities and challenges"),
        ],
    },
    "FM": {
        2021: [
            ("Finance", "Five Union Budget announcements"),
            ("Management", "Transactional versus transformational leadership"),
            ("Management", "Corporate governance: need and principles"),
            ("Finance", "Roles of SIDBI, NHB, NABARD, RRBs and EXIM"),
            ("Finance", "Basel norms and Basel III pillars"),
            ("Management", "Positive and negative behavioural reinforcement"),
        ],
        2022: [
            ("Management", "Communication barriers and managerial remedies"),
            ("Management", "Resistance to change and corrective measures"),
            ("Finance", "Blockchain and banking disruption"),
            ("Finance", "Long-term repo operations"),
            ("Finance", "India's response to the 2008 financial crisis"),
            ("Management", "Managerial promotion of ethical behaviour"),
        ],
        2023: [
            ("Management", "Fayol's contribution and fourteen principles"),
            ("Management", "Big Five personality model"),
            ("Finance", "RBI Retail Direct scheme"),
            ("Finance", "ONDC and competition with established platforms"),
            ("Management", "Code of conduct and implementation"),
            ("Finance", "Pre-sanctioned credit lines on UPI and inclusion"),
        ],
        2024: [
            ("Finance", "Derivatives: types, participants, significance and risks"),
            ("Management", "Communication channels and organisational importance"),
            ("Management", "Trait versus behavioural leadership theories"),
            ("Management", "Factors influencing business ethics"),
            ("Finance", "AT1-bond features and comparison with other bonds"),
            ("Finance", "Value versus growth investing"),
        ],
        2025: [
            ("Finance", "Capital markets, growth and SEBI measures"),
            ("Management", "Resistance to change and a systematic change approach"),
            ("Management", "Non-verbal communication in leadership, culture and collaboration"),
            ("Finance", "Budget concepts and monetary-fiscal inflation/growth balance"),
            ("Finance", "RBI supervision and regulation of financial markets"),
            ("Finance; ethics overlap", "AI risks, new challenges and financial-sector ethical standards"),
        ],
    },
}

ENGLISH_AUDIT = {
    2021: {
        "essay": "Coding in schools; BPO industry; creative thinking in business; prevention versus cure",
        "precis": "Sand scarcity, urbanisation and extraction damage",
        "rc": "Agorism passage, but insurance-sector subquestions: mismatched in supplied PDF",
        "limits": "Essay about 300 words; precis 170 words",
    },
    2022: {
        "essay": "Renewable energy and grids; women entrepreneurs; peace through understanding; medical tourism",
        "precis": "Space exploration and the space race",
        "rc": "FMC-SEBI merger and commodity-market regulation",
        "limits": "Essay about 300 words; precis 170 words",
    },
    2023: {
        "essay": "Climate economics; e-rupee; employee motivation; multilingual business social media",
        "precis": "AI and women's economic empowerment",
        "rc": "Inflation, business profits and distribution",
        "limits": "Essay about 600-620 words; precis 180-200 words",
    },
    2024: {
        "essay": "Olympics impacts; climate migration; employee mental health; lifelong learning",
        "precis": "AI as CEO: advantages, limitations and ethics",
        "rc": "CRM systems: functions, collaboration, deployment and implementation",
        "limits": "Essay about 600-620 words; precis 180-200 words",
    },
    2025: {
        "essay": "Emissions-intensity commitment; digital advertising; intergenerational education; startup adaptation",
        "precis": "Amazon climate regime, drought and forest risk",
        "rc": "Desalination, osmosis and power generation",
        "limits": "Essay about 600-620 words; precis 180-200 words",
    },
}


ESI = [
    ("1. Evidence and the 75-80% score requirement", [
        ("What was reviewed",
         "Modern-format sample: all 150 objective prompts and 30 offered descriptive prompts in "
         "the five supplied 2021-2025 papers. Counts are questions offered, not attempts or marks. "
         "The 2019 ESI section is legacy objective-style evidence, not pooled with the modern mix. "
         "There is no supplied 2026 Phase II paper and no 2020 paper."),
        ("The real recurring pattern",
         "Objective ESI often asks external knowledge around a passage, not comprehension from "
         "the passage alone. Reports, social programmes, benefit eligibility and regulatory "
         "overlap are prominent. Descriptive ESI demands explanation, evaluation, specific "
         "report/policy knowledge and multi-part coverage."),
        ("Breadth must protect descriptive choice",
         "Social/demographic/gender/migration themes occur among descriptive choices in all five "
         "years. Climate/sustainability choices occur in four of five (2021, 2023-2025). "
         "Explicit monetary-policy descriptive prompts occur in three of five (2022, 2023, 2025). "
         "These overlapping theme observations are not exclusive chapter shares or forecasts."),
        ("Score engineering",
         "Using the supplied guidebook's recent 50 objective + 50 descriptive structure: "
         "40 net objective + 35 descriptive = 75; 43 + 37 = 80. With objective 40, reaching "
         "80 requires 40/50 descriptive. A weak writing section cannot be assumed away. "
         "Confirm the actual 2027 structure, marking and choice rules from RBI."),
        ("Objective scoring must be mark-weighted",
         "With quarter-mark penalty per question value: net = correct-mark value - 0.25 x "
         "wrong-mark value. Example: 18 correct two-mark + 7 correct one-mark questions = "
         "43 positive marks; two wrong two-mark + two wrong one-mark questions deduct 1.5, "
         "giving 41.5/50 with one one-mark item left blank. Do not equate 80% of "
         "30 questions with 40 marks."),
        ("The minimum breadth layer",
         "Cover every supplied official syllabus heading at definition + mechanism + one example "
         "level. Then deepen recurring policy/report/beneficiary patterns. A high target is not "
         "compatible with treating the least frequent syllabus chapter as safely skippable."),
    ]),
    ("2. Growth, poverty, jobs and sustainability: core depth", [
        ("National income and measurement",
         "Study GDP/GVA, nominal/real, deflator, per-capita income, growth versus development, "
         "stock/flow, base/reference period and limits of aggregate growth. Be able to interpret "
         "a simple indicator and explain why GDP growth need not improve employment or welfare. "
         "Stop before advanced national-accounting derivations and econometrics."),
        ("Poverty and welfare",
         "Compare monetary and multidimensional poverty, incidence versus intensity, targeting "
         "errors, exclusion/inclusion, transfers versus public services and social protection. "
         "Depth test: explain a measure's merits and limitations, then connect a policy to an "
         "outcome. Evidence: 2021 descriptive Q2; 2023 Q4; 2025 Q1/Q3."),
        ("Employment and demographic transition",
         "Study LFPR, WPR, unemployment definitions and survey reference periods; distinguish "
         "levels, participation, quality, informality, skills and underemployment. Explain female "
         "participation, youth jobs, MSMEs and labour-intensive growth. Evidence: 2021 Q5; "
         "2022 Q4; 2023 Q6; 2024 Q1. Use latest comparable PLFS data, not mixed series."),
        ("Climate-growth mechanisms",
         "Trace physical shocks -> farm output/food prices/health/productivity -> income, fiscal "
         "costs and financial risk. Distinguish mitigation/adaptation, intensity/absolute emissions, "
         "transition risk, green finance, just transition and SDGs. Evidence: 2021 Q6; "
         "2023 Q3; 2024 Q3; 2025 Q3."),
        ("Exact depth needed",
         "For each theme prepare: definition, causal chain, two or three distinct challenges, "
         "policy mechanisms, two dated evidence anchors, one implementation trade-off and a "
         "practical conclusion. Facts support an argument; they do not substitute for one."),
        ("What not to over-study",
         "Avoid committee chronologies, advanced growth models, every poverty-line estimate, "
         "environmental treaty clauses and dozens of unverified figures. Retain the main "
         "measurement debates and current policy relevance; do not omit the underlying concepts."),
    ]),
    ("3. Indian economy: the full breadth map", [
        ("History, reforms, industrial and labour policy",
         "Know the broad pre-/post-1991 transition: liberalisation, trade/financial opening, "
         "public/private roles, competition, disinvestment and labour-market formalisation. "
         "Prepare reform -> intended channel -> outcome/limitation. Evidence: 2021 DQ4, "
         "2022 DQ2, 2024 DQ5; 2021 objective Q30 on labour-code objectives. "
         "Skip year-by-year historical narration unrelated to an argument."),
        ("Monetary and fiscal policy",
         "Explain policy rates, liquidity tools, transmission, inflation targeting, lags and "
         "supply-side limits; tax/spending/borrowing, deficits, debt sustainability, fiscal "
         "multipliers and crowding in/out. Prepare coordinated and conflicting-policy cases. "
         "Evidence: 2021 objective Q14-17; 2022 DQ5; 2023 DQ5; 2025 DQ5."),
        ("Budget, Survey, public finance and political economy",
         "Know BE/RE/actuals, revenue/capital, fiscal/revenue/primary deficit, transfers and "
         "federal finance. Read priorities and recommendations, not just allocations. "
         "Explain who benefits, financing and implementation incentives. Evidence: 2021 DQ1; "
         "2024 objective Q9-13. Public finance includes Centre-state relations, not merely tax rates."),
        ("Agriculture, industry and services",
         "Agriculture: productivity, water, market access, storage, diversification and price risk. "
         "Industry: MSME scale, credit, logistics, employment, corridors and competitiveness. "
         "Services: exports, digital/business services, jobs and unequal skill access. Use one "
         "sector map with bottleneck -> intervention -> trade-off; no crop encyclopaedia."),
        ("Money/financial markets, banks and RBI in development",
         "Know the credit/intermediation channel, inclusion, NBFC-bank distinctions, savings, "
         "payment infrastructure and productive investment. Evidence: 2022 DQ3/Q6 and "
         "2024 DQ6. ESI can cross into FM; narrow subject silos are unsafe."),
        ("Digital economy",
         "Explain interoperability, access/usage, public digital rails, productivity, privacy, "
         "cyber risk and exclusion. Connect technology to outcomes and safeguards, not slogans. "
         "Evidence: 2024 DQ2/Q6 and 2025 objective MSME/formalisation cluster Q11-14."),
    ]),
    ("4. Globalisation and social structure: do not leave gaps", [
        ("Globalisation syllabus coverage",
         "Study opening-up, trade creation/diversion, comparative advantage at an intuitive level, "
         "BoP/current-versus-financial flows, FDI/FPI, exchange-rate channels, reserves, WTO, "
         "IMF/World Bank, regional cooperation and contemporary fragmentation. Explain a "
         "global shock's path into India's inflation, trade, capital flows and growth."),
        ("Exact question forms",
         "2021 DQ3 asks post-crisis globalisation, not a generic essay on trade. 2022 objective "
         "Q11-14 links a trade agreement to provisions/law; 2023 Q5-12 combines WTO facts "
         "and WEO/IMF knowledge. Learn mandate, framework and India application; "
         "skip every tariff line or treaty clause."),
        ("Demography, urbanisation and migration",
         "Cover demographic dividend/ageing, jobs and human capital, rural-urban movement, "
         "housing, urban services, portability, remittances and migrant protection. "
         "Evidence: 2021 DQ5; 2023 DQ2; 2025 DQ4. Migration answers should consider "
         "both origin and destination and distinguish voluntary from distress migration."),
        ("Gender, social justice and multiculturalism",
         "Cover unpaid care, safety, education/health, labour/asset access, discrimination, "
         "protective policy, participation and social cohesion. Multiculturalism is an explicit "
         "syllabus item, not disposable 'static sociology'. Evidence: 2022 DQ1; 2023 DQ1; "
         "2024 DQ4; 2025 DQ2/Q6."),
        ("Breadth checkpoint",
         "For each of the four official ESI headings, produce a closed-book concept map and "
         "a usable outline on an unseen subtopic. A recognised chapter title is not coverage. "
         "Use syllabus-based checks to compensate for the small five-year descriptive sample."),
    ]),
    ("5. Objective ESI: scheme/report depth and linked sets", [
        ("Three distinct tasks",
         "Identify a scheme/report from context; recall facts not stated in the passage; apply "
         "rules to a person or case. Practise all three. A familiar passage does not mean its "
         "linked questions are answerable from the text."),
        ("Beneficiary and exception cases",
         "Examples: PM-Kisan exclusions (2021 Q13; 2024 Q29), PM-KMY cases (2022 Q22; "
         "2024 Q23), PM-JAY household coverage (2023 Q21), PMSBY accident/age cases "
         "(2025 Q1), adoption eligibility (2025 Q6). Learn boundaries, not only objectives."),
        ("Rules, components and operational detail",
         "Examples: AMRUT Q6-10 in 2021; ONORC legal/delivery framework Q1-4 in 2022; "
         "women's savings Q30 in 2023; AIF eligible projects Q26 in 2024; "
         "PMAY-U 2.0 verticals/special groups Q25-26 in 2025. Major schemes sometimes "
         "require detail beyond a GA-level flashcard."),
        ("Report depth",
         "World Bank Human Capital material (2022 Q15-17); WEO/IMF (2023 Q9-12); "
         "WDR middle-income-trap strategies (2024 Q5-8); Economic Survey sector/jobs "
         "material (2024 Q9-13); forests/report facts (2025 Q19/Q22). "
         "Prepare publisher, edition, framework, findings, India relevance and recommendations."),
        ("Boundary spillover",
         "SGB/financial products recur in ESI (2021 Q24; 2022 Q21; 2023 Q24; 2024 Q30). "
         "The 2025 ESI compilation includes SIF Q10 and equity-derivatives/MWPL Q27-30. "
         "Treat these as observed cross-domain prompts, not grounds to relabel ESI as only schemes."),
        ("Two-level notes",
         "Level 1 scheme card: ministry, objective, beneficiary/exclusion, benefit, funding, "
         "duration and latest change. Level 2 for selected major schemes: age/income/land "
         "thresholds, interactions with other benefits, components, delivery, withdrawal or "
         "grievance details as applicable. Add an eligible/ineligible mini-case."),
        ("Reports and schemes to prioritise",
         "Latest applicable Budget/Survey, RBI Annual Report/RCF/FSR, World Bank WDR, "
         "IMF WEO, UNDP HDR, SDG/MPI, PLFS/NFHS and gender evidence; major jobs, "
         "agriculture, health, education, housing, pension, women/child and inclusion schemes. "
         "Read official summaries and relevant chapters selectively; update editions for the exam."),
    ]),
    ("6. Descriptive ESI: turn knowledge into marks", [
        ("Decode the demand before writing",
         "Break a prompt into verb, topic, scope, named report/date and subparts. 'Evaluate' "
         "requires criteria and a judgement; 'discuss' requires a reasoned treatment; "
         "'compare' needs common dimensions; 'explain' needs mechanisms. A report-specific "
         "prompt needs that report, not any relevant statistic."),
        ("A dependable answer architecture",
         "Give a direct definition/context and thesis; organise the body to match subparts; "
         "explain mechanisms; use a few accurate evidence anchors; address implementation "
         "constraints/counterarguments; conclude with a prioritised way forward. Use headings "
         "where helpful, not a mechanical template that ignores the question."),
        ("Example: youth employment",
         "Separate job availability from employability, participation and job quality. Connect "
         "skills mismatch, labour demand, MSME constraints and gender barriers to mechanisms. "
         "Match solutions to each constraint, name responsible actors and implementation "
         "conditions, and use comparable labour data. A scheme list alone is not analysis."),
        ("Evidence discipline",
         "For each issue keep two or three reliable anchors: statistic + source/reference "
         "period, scheme/mechanism, and report recommendation or example. Never invent a "
         "rank, exact quotation or report finding. When an exact number is uncertain, make "
         "a defensible qualitative statement without pretending precision."),
        ("Self-review rubric - not RBI's marking scheme",
         "Review demand coverage, conceptual accuracy, mechanism/analysis, relevant evidence, "
         "balance/feasibility and clarity/completion. Score each 0-2 for diagnosis, then rewrite "
         "the weakest part. This rubric does not convert reliably into official marks."),
        ("Time and word control",
         "Under the recent 90-minute descriptive format, a starting budget is 5 minutes "
         "selection/planning, about 25 minutes for each 15-marker, 15 minutes for each "
         "10-marker and 5 minutes review. Practise that mix in a keyboard interface. "
         "The recollections show 600/400-word labels; obey actual instructions, not a desire to pad."),
        ("Selection and readiness",
         "Choose by all-subpart coverage and evidence, not topic familiarity alone. Keep "
         "enough breadth to have credible options among both mark bands. Judge readiness "
         "using fresh objective sets plus timed, externally reviewed writing; remembered "
         "PYQ outlines and generous self-scoring are weak evidence."),
    ]),
]

FM = [
    ("1. Evidence and the 75-80% score requirement", [
        ("Reviewed sample",
         "All 150 objective prompts and 30 offered descriptive prompts in supplied 2021-2025 "
         "FM papers were reviewed. No FM section is listed in the supplied 2019 compilation; "
         "2026 is Phase I only. Modern descriptive choices cannot be projected from older ESI data."),
        ("Both halves are necessary",
         "Each 2021-2024 compilation offers three finance and three management descriptive "
         "prompts. The 2025 compilation offers four finance-oriented prompts, including "
         "AI/ethics overlap, and two management prompts. This is offered-question classification, "
         "not an official fixed finance/management mark split or permission to omit a half."),
        ("What repeats most dependably",
         "Communication and motivation/personality/perception-related material occur in every "
         "modern FM paper when objectives and descriptives are considered together. "
         "Ethics/governance also spans all five. Finance repeatedly tests institution/regulator "
         "roles, instruments, payments, rules and policy applications. Exact forms change."),
        ("A realistic target equation",
         "Using the recent 50+50 structure: objective 40 + descriptive 35 = 75; "
         "objective 43 + descriptive 37 = 80. These are planning combinations, not "
         "predicted achievable marks. At objective 35, even descriptive 40 only reaches 75."),
        ("Negative marking and source limits",
         "Use correct-mark value - one-quarter wrong-mark value, not raw question accuracy "
         "when one-/two-mark items coexist. The 2025 source itself flags objective Q28-30 "
         "as possibly inexact in question/theme. Keep those as provisional examples, not exact "
         "wording evidence. Verify current rules against applicable RBI/SEBI releases."),
        ("Breadth rule",
         "Cover every explicit finance and management heading in the supplied syllabus. "
         "Prepare core subjects deeply, but keep a minimum concept/application layer for "
         "accounting, derivatives, alternate finance and less frequent management models."),
    ]),
    ("2. Financial system, institutions and regulation", [
        ("What to study",
         "Financial intermediation, RBI functions, banking structure and developments, NBFC/HFC "
         "differences, and SIDBI/EXIM/NABARD/NHB/NaBFID mandates. Know purpose, clients, "
         "funding/product and development role; distinguish regulator, operator and institution."),
        ("Objective versus descriptive depth",
         "Objectives ask recognition, regulator and rule/application. A descriptive answer must "
         "explain channels: mobilisation -> intermediation -> credit/risk allocation -> development, "
         "with institutional distinctions. Evidence: 2021 objective Q6/Q14-16, DQ4; "
         "2023 objective Q21; 2024 Q9-12; 2025 Q1-4 and DQ5."),
        ("Regulation and supervision",
         "Distinguish prudential/conduct rules, supervision, systemic oversight and consumer "
         "protection. Learn capital, liquidity, leverage, asset-quality and governance concepts, "
         "including the logic of Basel pillars. Evidence: 2021 DQ5; 2024 objective Q30; "
         "2025 DQ5. Do not memorise a Basel ratio without meaning and scope."),
        ("Global system and international banking",
         "Prepare crisis contagion, liquidity/funding, FX/capital-flow risk, cross-border banking "
         "and the transmission of global shocks into India. Evidence: 2022 DQ5. "
         "Know broad trends and current regulatory responses, not every foreign bank detail."),
        ("Stop line",
         "Skip detailed institution annual accounts, obscure circular clauses and deep "
         "international-banking legal mechanics. Retain major updated thresholds and exceptions "
         "when they are relevant to the syllabus/PYQ-style rules."),
    ]),
    ("3. Markets, risk, derivatives and alternate finance", [
        ("Market structure and instruments",
         "Study primary/secondary, money/bond/equity/forex, participants, issuance, trading, "
         "clearing and settlement; T-bills, CP/CD, repo, government bonds and basic equity/"
         "mutual-fund concepts. Compare maturity, issuer, risk, return and use. "
         "Evidence: 2022 objective Q8-11; 2023 Q30; 2025 Q3-6."),
        ("What objective depth looks like",
         "Recognise an instrument from a situation; apply a threshold/rule; identify the "
         "regulator/platform; distinguish debt from equity and settlement from issuance. "
         "ASBA (2021 Q7-8; 2024 Q5-8) and receivables discounting (2025 Q18-20) "
         "show the value of process maps rather than acronym lists."),
        ("Risk management",
         "Credit, market, interest-rate, liquidity, operational, cyber, model and systemic risk: "
         "definition -> exposure -> consequence -> control -> residual risk. Distinguish capital "
         "from liquidity and asset-price from funding risk. Use Basel and banking examples, "
         "not advanced statistical risk-model derivations."),
        ("Derivatives",
         "Compare forwards, futures, options and swaps; rights/obligations, exchange/OTC, "
         "margin/counterparty risk, hedger/speculator/arbitrageur. Work simple hedging/payoff "
         "direction cases. Evidence: 2024 DQ1 asks types, participants, significance AND risks. "
         "Do not replace this with just four definitions or study stochastic option pricing."),
        ("Bonds and investing",
         "Explain price-yield direction, duration intuition, default/subordination/call risk and "
         "ordinary versus AT1 features. Compare value/growth investing by valuation, expected "
         "earnings and risk; avoid stock tips. Evidence: 2024 DQ5/Q6. "
         "Keep applicability and instrument-specific conditions clear."),
        ("Alternate finance and PPP",
         "Cover venture/private capital, crowdfunding at a conceptual level, REITs/InvITs, "
         "infrastructure finance, PPP models and private versus social cost-benefit. "
         "Evidence: 2021 objective Q9-11; 2023 Q28; 2024 Q22; 2025 Q5-6. "
         "Explain risk allocation, externalities, incentives and viability, not just full forms."),
        ("A 75-80% depth check",
         "Can you draw the transaction flow, distinguish two similar products, solve a simple "
         "numeric/application item and write benefits/risks/safeguards on an unseen instrument "
         "using the underlying concepts? If not, rereading the chapter is not sufficient."),
    ]),
    ("4. Accounting, Budget and inflation: protect the breadth", [
        ("Accounting coverage",
         "Know accounting equation, asset/liability/equity, revenue/expense/profit, accrual versus "
         "cash, balance sheet/P&L/cash-flow links. Calculate and interpret debt-equity, debtor/"
         "creditor days, inventory turnover, ROA and ROE using the stated definitions/periods."),
        ("Exact observed forms",
         "2021 objective Q26 compares valuation with otherwise similar bank information; "
         "2023 Q22 calculates ROA; 2025 Q7-9 asks gross profit, debt and liabilities from data. "
         "Work small mixed problems and check units, numerator, denominator and averages. "
         "Do not dismiss accounting as too rare; do not expand into a professional-accountancy syllabus."),
        ("Budget and public finance",
         "Revenue/capital receipts and spending, deficit measures, debt, grants/transfers, "
         "non-tax revenue, financing and the current Budget's broad priorities. "
         "Evidence: 2021 objective Q21 and DQ1; 2023 objective Q29; 2025 Q23 and DQ4. "
         "Be able to classify an item and explain its economic effect."),
        ("Inflation",
         "CPI/WPI coverage and components, headline/core, demand-pull/cost-push, base effects, "
         "expectations, distributional costs and monetary/fiscal remedies. Explain why divergent "
         "CPI/WPI movements can occur. Evidence: 2025 objective Q17/Q24 and DQ4; "
         "Q28's inexact-source caveat applies. Skip advanced macro modelling."),
        ("Policy application",
         "Explain transmission and lags, not 'raise rates to reduce inflation' alone. Distinguish "
         "supply shocks from excess demand and discuss growth/inflation trade-offs. "
         "Read relevant Budget/Survey/MPC summaries, not every tax schedule."),
    ]),
    ("5. Digital finance, inclusion and governance", [
        ("Digital/IT and inclusion",
         "Understand payment-system roles and flows, bank/non-bank participants, CBDC/UPI/"
         "cards/account distinctions, digital lending, fintech, access/usage/quality and last-mile "
         "barriers. Examples: 2021 objective Q4-5/Q20; 2022 Q21; 2023 Q1-5 and DQ6; "
         "2024 Q28; 2025 objective Q18-22."),
        ("Descriptive digital pattern",
         "2022 DQ3 asks blockchain disruption; 2023 DQ3/Q4/Q6 asks Retail Direct, ONDC and "
         "credit-line UPI; 2025 DQ6 asks AI risks and ethics. Study purpose, mechanism, "
         "participants, benefits, limitations and safeguards. A product-launch note is not a "
         "complete descriptive answer."),
        ("AI depth without engineering overload",
         "Cover bias/fairness, explainability, model validation, data privacy, cybersecurity, "
         "third-party concentration, accountability and human oversight. Link each risk to "
         "a use case and control. No need to derive machine-learning algorithms for these prompts."),
        ("Corporate governance in banking",
         "Study board/committee roles, oversight versus execution, independence, conflicts, "
         "risk culture, audit, disclosure and stakeholder protection. Evidence: 2021 DQ3; "
         "2023 objective Q11-15/Q20. Keep current composition rules separate from the "
         "underlying governance principles."),
        ("Mixed connections",
         "A digital-lending case can test financial risk, consumer protection, ethics and "
         "governance simultaneously. A PPP case combines finance and incentives. "
         "A regulatory change can affect inclusion and operational risk. Prepare these links "
         "explicitly instead of maintaining isolated chapters."),
    ]),
    ("6. Management: full syllabus, theory and application", [
        ("Foundations and schools",
         "Management functions and roles; scientific, administrative, human-relations and "
         "systems approaches; nudge theory. Compare unit of analysis, assumptions, application "
         "and limitation. Evidence: 2023 DQ1 (Fayol); 2025 objective Q12-14. "
         "Skip thinker biographies and memorised labels without scenarios."),
        ("OB, personality, reinforcement and perception",
         "Individual/group/organisation levels, Big Five, determinants of personality, "
         "reinforcement versus punishment, attribution/perceptual errors. "
         "Evidence: 2021 Q1-3/Q22/Q24 and DQ6; 2022 Q1-3/Q26; "
         "2023 Q23 and DQ2. Practise the same behaviour under plausible competing labels."),
        ("Motivation: all explicit theories",
         "Maslow, ERG, McClelland and Herzberg (content); Adams equity and Vroom expectancy "
         "(process). Know central construct, assumptions, prediction, workplace example and "
         "limitation. Compare motivation/hygiene, equity/equality and expectancy/instrumentality/"
         "valence. Examples: 2022 Q15-17; 2023 Q7-8; 2024 Q21; 2025 Q27."),
        ("Leadership and emotional intelligence",
         "Trait, behavioural, contingency, charismatic, transactional and transformational; "
         "EI concept, dimensions and organisational use. Identify the mechanism, context fit "
         "and limitation, not just the theorist. Evidence: 2021 DQ2; 2023 Q9-10; "
         "2024 Q25 and DQ3. Use a comparison matrix plus a short case."),
        ("Relationships, conflict and change",
         "Transactional analysis and Johari Window; conflict sources/types/management styles; "
         "resistance, Lewin, OD, action research and positive model. "
         "Evidence: Johari 2021 Q24/2024 Q24; change 2022 DQ2/2025 DQ2. "
         "Practise diagnosing causes before proposing interventions."),
        ("Minimum coverage for less-visible headings",
         "EI, conflict, nudge, transactional analysis and OD alternatives remain in the official "
         "syllabus even if the sample underrepresents them. Prepare definition, dimensions, "
         "one scenario and one outline. Absence from five papers is not evidence of exclusion."),
        ("The theory card",
         "Theory | core proposition | variables/stages | a workplace case | nearest confusable "
         "theory | limitation. Retrieve the card closed-book, then classify a new case and explain "
         "why its nearest alternative is weaker. This is deeper than recalling a mnemonic."),
    ]),
    ("7. Ethics, governance and communication: applied depth", [
        ("Ethics breadth",
         "Utilitarianism, rights/duties, justice/fairness, care, virtue, teleological views, egoism "
         "and relativism. Apply to compliance, finance, HR and marketing. Cover organisational "
         "structure, board responsibilities, ethics programmes, code of ethics/conduct and "
         "governance mechanisms."),
        ("The observed pattern",
         "2021 DQ3: governance need/principles; 2022 DQ6: managerial ethical behaviour; "
         "2023 DQ5: implementing a code; 2024 DQ4: ethical influences; "
         "2025 DQ6: financial AI ethics. A memorised ethics definition will not cover implementation."),
        ("A usable ethics-case method",
         "Identify stakeholders, facts and conflict; compare duties/rights/outcomes/fairness; "
         "assess feasible alternatives; justify an action and safeguards. Include accountability, "
         "reporting/escalation and monitoring when relevant. Do not recite every theory regardless of fit."),
        ("Communication breadth",
         "Process and feedback; channels/networks; oral/written and verbal/non-verbal; "
         "upward/downward/lateral; barriers and IT. Explain noise and remedy at sender, "
         "message, channel and receiver. Distinguish a network's structure from direction."),
        ("Communication examples",
         "Objectives recur across all five years. Descriptive prompts include barriers/remedies "
         "(2022 Q1), channels/importance (2024 Q2), and non-verbal communication across "
         "leadership, culture and collaboration (2025 Q3). A single generic 'communication "
         "is important' answer will miss these different demands."),
        ("Change and ethics combined",
         "For a new AI/banking workflow, diagnose fear, incentives, capability and trust; plan "
         "communication, training, participation and feedback; add fair oversight and evaluation. "
         "Use a named model only when it genuinely organises the answer."),
    ]),
    ("8. How to study, practise and earn descriptive marks", [
        ("Best source stack",
         "Use one full-note source per topic from your Finance/Management folders. First solve "
         "a small diagnostic set, read the relevant concept, then use objective practice, "
         "answer-writing questions, short notes and infographics for different purposes. "
         "Use official RBI/SEBI material to update rules; notes' dates are not proof of currency."),
        ("Practice both knowledge modes",
         "For management: retrieve theory -> classify scenario -> compare alternatives -> "
         "write application/limitations. For finance: draw flow -> compare instruments -> "
         "solve small numeric/rule cases -> write purpose/benefits/risks/safeguards."),
        ("Match the answer to the demand",
         "For 2024 derivatives, cover types, participants, significance and risk. For a "
         "leadership comparison, use common dimensions and examples, not two disconnected "
         "mini-essays. For a named policy, give its actual mechanism before broad advantages."),
        ("Score calibration",
         "Use the same 90-minute planning budget as ESI: selection, two 15-mark and two "
         "10-mark answers, review. Under current-style instructions that is 50 descriptive "
         "marks, not six compulsory essays. Verify selection rules in the actual notice."),
        ("High-score safeguards",
         "Do not drop accounting/derivatives; do not assume management alone covers all "
         "objective questions; do not quote obsolete regulatory values. Avoid long theory "
         "lists, repeated points, empty 'awareness' solutions and polished but irrelevant introductions."),
        ("Readiness",
         "Keep net objective scores near your planning target on fresh 30-minute sets. "
         "Get timed descriptive work reviewed for demand coverage, conceptual correctness, "
         "application, evidence, balance and language. Reviewer marks are calibration only, "
         "not predicted RBI scores; assess repeated performance, not a single good paper."),
    ]),
]

ENGLISH = [
    ("1. What the evidence says: a writing paper, not Phase I English", [
        ("Sample and stable task mix",
         "All five supplied 2021-2025 English sections offer essay, precis and written "
         "comprehension, labelled 40/30/30 marks. The 2019 section offers the same three "
         "skills as supplementary evidence. Each essay offers choices; they are not all attempted."),
        ("Word-limit change in the supplied sample",
         "2021-2022 recollections specify about 300 essay words and 170 precis words; "
         "2023-2025 specify about 600-620 essay words and 180-200 precis words. "
         "Use the actual exam instruction. Do not train exclusively on the old shorter format "
         "or impose a one-third precis rule when an explicit limit is given."),
        ("75-80% score route",
         "A planning combination is essay 30/40 + precis 23/30 + RC 22/30 = 75; "
         "32 + 24 + 24 = 80. These are goals, not a published scoring rubric or a promise. "
         "A strong essay cannot fully compensate for unfinished precis/RC."),
        ("Important source mismatch",
         "2021 PDF pp71-72 prints an agorism passage but insurance-sector comprehension "
         "questions. Those subquestions cannot be reliably answered from that passage. "
         "Exclude this pair from evidence-based RC marking; do not invent missing material. "
         "The other 2021 tasks remain usable for practice."),
        ("The real depth requirement",
         "Express a defensible argument; compress a text faithfully; explain relationships "
         "from an unfamiliar passage in your own words. Content familiarity helps speed, "
         "but reading fidelity, structure and language determine the quality of the response."),
    ]),
    ("2. Essay breadth: prepare families, not predictions", [
        ("Technology, business and work",
         "Coding education, BPO, creativity (2021); e-rupee, employee motivation and multilingual "
         "business communication (2023); digital advertising and startup adaptation (2025). "
         "Prepare productivity, access, jobs/skills, competition, privacy, governance and ethics."),
        ("Climate, energy and development",
         "Renewable energy and grid integration (2022); climate economics (2023); climate "
         "migration (2024); emissions-intensity commitments (2025). Prepare mechanisms, "
         "distributional effects, finance, trade-offs and practical implementation."),
        ("Social/human capital and organisations",
         "Women entrepreneurs and medical tourism (2022); employee mental health and "
         "lifelong learning (2024); intergenerational education (2025). "
         "Prepare education, health, inclusion, gender, ageing and workplace capability."),
        ("Abstract and multidimensional prompts",
         "Prevention versus cure (2021), peace through understanding (2022), lifelong learning "
         "(2024) show that pure economics preparation is insufficient. Olympics impacts "
         "(2024) requires social, economic AND environmental dimensions. Learn argument "
         "construction for unfamiliar subjects, not a model essay for every headline."),
        ("A compact evidence bank",
         "For each family keep 3-4 mechanisms, 2 examples, 1 reliable fact when useful, "
         "2 counterarguments and workable responses. Reuse ESI/FM knowledge selectively. "
         "An English essay is not a dump of report names or scheme abbreviations."),
        ("Stop line",
         "Do not memorise full essays, ornamental quotations or hundreds of statistics. "
         "Do not predict the next topic from repetition. Keep breadth through varied "
         "prompts and fresh outlines, not more passive reading sources."),
    ]),
    ("3. Essay depth: argument, structure and editing", [
        ("Selection before commitment",
         "Choose the topic on which you can state a thesis, cover every requested dimension, "
         "give concrete examples and acknowledge a meaningful limitation. A familiar word "
         "in a title is not sufficient. Spend a short fixed time deciding, then commit."),
        ("Plan a coherent line of argument",
         "Define the issue and position in the opening; order body paragraphs causally or by "
         "the question's dimensions; include counterargument/conditions; conclude with a "
         "reasoned judgement. Each paragraph should advance the thesis, not merely add a heading."),
        ("Paragraph method",
         "Claim -> explanation/mechanism -> evidence/example -> link to the question. "
         "For climate migration, distinguish origin and destination impacts; for a technology "
         "prompt, distinguish capability from implementation conditions. This prevents generic filler."),
        ("Word allocation",
         "For a roughly 600-word essay, a starting plan is about 60-80 words introduction, "
         "420-460 body and 60-80 conclusion. Adapt to the exact limit and topic. "
         "A word target is a constraint, not a reason to repeat an argument."),
        ("Language",
         "Prefer accurate, direct sentences and controlled vocabulary. Vary sentence structure "
         "only when clear. Check subject-verb agreement, article/preposition use, pronoun "
         "reference, tense, parallelism and punctuation. Avoid unsupported absolutes and "
         "invented quotes/data."),
        ("Editing order",
         "First check demand coverage and logic; then paragraph transitions and repetition; "
         "then language and word limit. Polishing adjectives before fixing a missing "
         "subpart is low-return work."),
        ("Practice target",
         "Write varied timed essays, not just outlines. After review, rewrite the weakest "
         "paragraph and outline a different topic to test transfer. A reusable structure "
         "must still accommodate an unfamiliar prompt."),
    ]),
    ("4. Precis: faithful compression is a separate skill", [
        ("What recurs",
         "The subjects vary: sand extraction (2021), space race (2022), AI/gender (2023), "
         "AI leadership (2024), Amazon climate risk (2025). The stable demand is to retain "
         "the central argument and relationships under a tight word limit."),
        ("A repeatable method",
         "Read for thesis and structure; mark main propositions, causal links and qualifications; "
         "separate essential support from illustration; draft in your own words; count words; "
         "compare the draft against the source for omissions, distortion and additions."),
        ("Compress ideas, not random sentences",
         "Generalise a list only when the common category is accurate. Remove repeated "
         "examples and narrative detail before dropping a main claim. Preserve contrast, "
         "cause/effect, degree of certainty and the author's stance. Reordering is acceptable "
         "only when the argument remains faithful."),
        ("Examples of dangerous distortion",
         "Turning 'may increase risk' into 'will cause failure'; retaining only benefits from a "
         "balanced AI passage; dropping the distinction between suitable construction sand "
         "and abundant desert sand. These are comprehension errors, not stylistic preferences."),
        ("Title and expression",
         "Provide a concise neutral title when instructed. Keep the summary self-contained, "
         "coherent and free of personal opinion, invented evidence or meta-commentary. "
         "Do not write a critique or a bullet-list substitute unless instructed."),
        ("Review checklist",
         "Main thesis retained? All major stages covered? Key qualifications preserved? "
         "No outside facts/opinion? Natural prose? Accurate title? Within the stated limit? "
         "Use this for diagnosis; it is not an official mark conversion."),
        ("Best practice",
         "Practise 180-200 words on the recent supplied tasks, plus varied fresh passages. "
         "Compare coverage maps before comparing vocabulary. Rewriting a bad summary "
         "faithfully is more valuable than collecting model precis answers."),
    ]),
    ("5. Written comprehension: answer the question, not the topic", [
        ("The repeated operations",
         "Retrieve a reason; explain a process; compare alternatives; identify consequences; "
         "synthesise dispersed details; state the author's argument. Later papers offer five "
         "subquestions. Subject matter shifts, so practise unfamiliar technical/business prose."),
        ("Observed examples",
         "2022 asks why commodity-market regulation was separate and effects of merger; "
         "2023 asks inflation measurement and distribution between profits/workers; "
         "2024 asks CRM functions, deployment comparisons and challenges; "
         "2025 asks water needs, osmosis, advantages and future technology."),
        ("Evidence-map method",
         "For each question underline the command and scope, locate all supporting spans, "
         "note required points, then paraphrase without changing the technical meaning. "
         "Check that every sentence answers the question. Do not copy a large paragraph."),
        ("Depth and length",
         "Use the stated answer limit if present. Otherwise calibrate to marks and number "
         "of requested points; do not write an essay per subquestion. Multi-part questions "
         "need all parts, even if one is less familiar."),
        ("What not to do",
         "No outside facts unless requested, no personal policy recommendation in a retrieval "
         "question, no answer from the topic title alone and no guessed mechanism. "
         "Technical terms can remain when paraphrasing them would distort meaning."),
        ("Time trap",
         "Repeatedly rereading the whole passage instead of mapping a specific demand "
         "wastes time. Use local evidence for retrieval, but read wider for contrast or inference. "
         "Do not use the mismatched 2021 pair to judge your accuracy."),
    ]),
    ("6. Training, timing and honest score calibration", [
        ("A 90-minute starting plan",
         "For current-style 40/30/30 tasks, try essay 35 minutes, precis 25, RC 25 and "
         "5 minutes final checks. This includes reading/planning within each task; it is "
         "not an official optimal allocation. Practise another order if it improves completion "
         "without damaging essay/precis quality."),
        ("Typing is part of the task",
         "Use a keyboard with no autocorrect/spellcheck during timed practice. If four FM/ESI "
         "answers were written to the supplied 600/400 maxima, that is about 2,000 words "
         "before planning/review. For a 600-word English essay in 35 minutes with 8 minutes "
         "planning/checking, about 22 clean words/minute of composition is needed. "
         "Measure thoughtful composition, not copied-text typing speed."),
        ("A weekly minimum to adapt to baseline",
         "Two essays, two precis, two RC sets and one complete timed English paper is a "
         "useful training starting point; count full-paper tasks toward the totals. "
         "Review/rewrite sessions matter as much as volume. Reduce quantity if feedback "
         "and correction are being skipped."),
        ("Rubric for feedback - unofficial",
         "Essay: relevance/demand, argument, organisation, support, language and completion. "
         "Precis: fidelity, coverage, compression, coherence and instruction compliance. "
         "RC: correct required points, textual support, paraphrase and concision. "
         "Ask reviewers to identify concrete missing/distorted points, not just award a number."),
        ("Readiness standard",
         "Complete every task within instructions and time across several unseen papers. "
         "Seek independent review of at least two full scripts and compare reviewer "
         "disagreements. A self-awarded 80 is not evidence of an official 80. "
         "Track recurring error rates and task completion alongside indicative scores."),
        ("The largest avoidable losses",
         "Unfinished RC; precis that adds opinions; off-topic essay; missing a dimension; "
         "incorrect data used for decoration; ignoring a changed word limit; and no time "
         "left for basic editing. Eliminate these before chasing sophisticated vocabulary."),
    ]),
]


VISUAL_METHODS = {
    "ESI": [
        ("Build small maps, not one giant subject map",
         "Start with four branches: Growth and development; Indian economy; Globalisation; "
         "Social structure. Under each, list syllabus topics only. Create separate topic maps "
         "for poverty, employment, agriculture, migration, gender and monetary policy. "
         "Keep changing statistics in a separate evidence table."),
        ("Worked map: youth employment",
         "Centre: YOUTH EMPLOYMENT.\n"
         "Measurement -> participation, employment, unemployment.\n"
         "Causes -> labour demand, skills mismatch, participation barriers.\n"
         "Consequences -> income insecurity, underused demographic potential.\n"
         "Responses -> enterprise/jobs, skills/apprenticeships, participation support.\n"
         "Constraints -> implementation capacity, access and job quality."),
        ("Label every important connection",
         "Skills mismatch REDUCES employability; childcare availability CAN SUPPORT women's "
         "participation; enterprise growth CAN INCREASE labour demand. A line without a "
         "relationship label can hide weak understanding. Explain each arrow closed-book."),
        ("Evidence-table template",
         "Columns: Claim | Indicator/example | Source and reference period | Limitation.\n"
         "Row 1: Gender participation gap | Comparable labour data | Relevant PLFS release | "
         "Participation is not job quality.\n"
         "Row 2: Skills matter | Skills/employment evidence | Verified report | Training alone "
         "does not create labour demand.\n"
         "Row 3: Enterprise can help | Programme mechanism | Official programme source | "
         "Credit alone may be insufficient."),
        ("Convert the map into a descriptive answer",
         "For a youth-employment question: define the problem; select relevant causes; explain "
         "mechanisms; match causes to responses; add evidence and implementation constraints; "
         "conclude with priorities. The map stores knowledge, but the question determines "
         "the answer's structure. Do not reproduce every branch regardless of relevance."),
        ("Choose the right visual tool",
         "Use causal chains for inflation, migration or climate effects; comparisons for poverty "
         "measures or policy alternatives; scheme tables for beneficiaries/exclusions; "
         "and answer outlines for evaluation. Each topic needs only the tools that serve it."),
    ],
    "FM": [
        ("Management: theory comparison table",
         "Columns: Theory | Core idea | Recognition clue | Application | Common confusion.\n"
         "Herzberg | Hygiene and motivators have different roles | Conditions versus achievement | "
         "Diagnose dissatisfaction separately | Removing dissatisfaction need not create motivation.\n"
         "Vroom | Expectancy, instrumentality, valence | Effort -> performance -> valued outcome | "
         "Check capability, reward credibility and value | A valuable reward alone is insufficient.\n"
         "Adams | Perceived input-outcome fairness | Comparison with another employee | "
         "Investigate perceived inequity | Equity is not identical rewards."),
        ("Test the table through a mini-case",
         "Case: an employee values promotion but believes performance will not influence "
         "selection. Identify the relevant theory, explain the broken link and propose a "
         "remedy. Under Vroom, the performance-to-outcome link (instrumentality) is weak. "
         "Now change the case so the employee doubts their ability to perform: explain "
         "why the diagnosis changes. These are learning illustrations, not PYQ solutions."),
        ("Finance: draw the transaction",
         "TReDS example: MSME supplies goods/services -> buyer accepts invoice -> "
         "financiers bid to discount the receivable -> MSME receives early payment -> "
         "buyer pays at maturity. Add: purpose, participant at each step, conditions, risks "
         "and safeguards. Use the same process-map method for payments, bond issuance, "
         "monetary transmission and PPPs."),
        ("Instrument comparison template",
         "Columns: Instrument | Issuer/parties | Purpose | Return/payment | Main risks. "
         "Compare two confusable instruments on the same dimensions. Then cover the "
         "instrument name and identify it from the remaining fields."),
        ("Accounting practice table",
         "Columns: Ratio | Formula/convention | Meaning | Small calculation | Interpretation trap. "
         "Always solve a numeric example and explain the result. Check the stated definition, "
         "period and use of average balances. Formula recognition is not calculation competence."),
        ("Combine methods for depth",
         "Use a small topic map for structure, a table for distinctions, a flowchart for "
         "mechanism and a new case for application. For descriptive practice, select the "
         "relevant theory/mechanism, apply it and discuss limitations rather than copying the map."),
    ],
    "English": [
        ("Essay: question-specific argument map",
         "Centre: the exact question and requested dimensions.\n"
         "Branch 1: central position/thesis.\n"
         "Branch 2: argument -> explanation -> example.\n"
         "Branch 3: second argument -> explanation -> example.\n"
         "Branch 4: counterargument or limitation.\n"
         "Branch 5: judgement and way forward.\n"
         "Then write the essay. Outlines alone do not train sentences, transitions or completion."),
        ("Precis: passage-structure table",
         "Columns: Paragraph | Main proposition | Relationship | Essential?\n"
         "Example row 1: introduces the problem | Context | Retain briefly.\n"
         "Example row 2: explains why it happens | Cause | Retain.\n"
         "Example row 3: several illustrations | Examples | Compress.\n"
         "Example row 4: limits the claim | Qualification | Preserve.\n"
         "Draft from the main propositions, then check against the original. Do not change "
         "certainty, causation or the author's stance."),
        ("Comprehension: evidence table",
         "Columns: Question asks | Relevant passage points | Answer in my words. "
         "Map every part of the demand to textual evidence, then write a concise response. "
         "The table is a practice scaffold, not something to reproduce in the examination."),
        ("Personal language-error table",
         "Columns: My error | Correct form | Why | My new sentence. "
         "Record errors you actually make, then write a fresh sentence applying the correction. "
         "This is more useful than repeatedly collecting grammar rules already mastered."),
        ("Do not confuse organising with writing",
         "Mind maps help planning, but English improves through reading accurately, producing "
         "prose, receiving feedback and editing. Replace part of note-making time with a "
         "timed paragraph, precis or comprehension answer. Review ideas before vocabulary."),
    ],
}

VISUAL_RECALL = [
    ("Match the tool to the knowledge",
     "Mind map: topic structure. Flowchart: how something works. Comparison table: similar "
     "items. Fact table/cards: values, dates and exceptions. Mini-case: application. "
     "Question-specific outline: descriptive writing. Error log: recurring mistakes."),
    ("Blank-page recall: the essential step",
     "Close the source. Rebuild the map/table from memory. Explain the connections aloud. "
     "Compare with the source and correct missing/wrong elements. Attempt a fresh question. "
     "Recognising a finished map is not the same as knowing the topic."),
    ("Spaced retrieval",
     "A practical starting schedule is next day -> one week -> two weeks -> one month, "
     "adjusted to recall. Hide table columns, reverse the prompt, vary the case and retrieve "
     "the relationship as well as the label. Update dated facts before reinforcing them."),
    ("A manageable 60-minute session",
     "20 minutes: understand from existing notes. 10: make one small map/comparison table. "
     "10: reconstruct closed-book. 15: apply through MCQs, a case or an answer outline. "
     "5: record mistakes and the next review. For English, replace part of reading/organising "
     "with actual writing. Adapt the timings; do not make formatting the main activity."),
    ("The stopping rule",
     "Every visual note must produce recalled facts, solved questions, explained cases "
     "or a written answer. If formatting takes more effort than testing, simplify. "
     "The goal is retrievable knowledge, not an attractive notebook."),
]

COMMON = [
    ("A 12-week integrated preparation path", [
        ("Weeks 1-2: diagnose and establish breadth",
         "Take fresh objective ESI/FM diagnostics and write one full English paper. Map every "
         "syllabus heading green/amber/red by closed-book performance, not reading completed. "
         "Establish core economics, financial-system basics and management theory cards. "
         "Start writing immediately, not after finishing all notes."),
        ("Weeks 3-5: deepen and connect",
         "Work through ESI scheme/report cases, FM instruments/accounting/risk and applied "
         "management. Write timed answers on multiple syllabus areas; practise precis and "
         "RC weekly. Add current developments to existing static notes instead of building "
         "a second unrelated notebook."),
        ("Weeks 6-8: objective-to-descriptive transfer",
         "Use mixed objective sets and choose answers from six-question descriptive menus. "
         "Test both mark bands and complete all English tasks. Repair stale facts, confused "
         "rules, weak mechanisms and incomplete subparts. Keep one current-affairs source."),
        ("Weeks 9-10: full-paper constraints",
         "Run fresh timed papers with a keyboard and actual-style selection rules. Review "
         "mark-weighted objective net scores and externally reviewed writing separately. "
         "Do not hide one subject's weakness behind the aggregate."),
        ("Weeks 11-12: revision and verified updates",
         "Prioritise retrieval, comparison sheets, short error logs and repeated timed "
         "completion. Update major reports/policies from applicable official releases. "
         "Limit new sources and stop expanding low-return detail."),
        ("Weekly outputs and readiness gate",
         "Once foundations are established, work toward one fresh timed objective section "
         "and one full descriptive section each for ESI and FM, plus one full English paper "
         "per week. Review and rewrite before adding volume. Seek repeated objective "
         "performance around 40-43/50 net and independently reviewed complete answers "
         "around your planning targets; do not turn an unofficial review into a score guarantee. "
         "Track each subject separately across at least three fresh papers."),
        ("Protect Phase I work",
         "If Phase I is only two months away, this is a parallel Phase II track, not a direction "
         "to abandon Phase I aptitude/GA. Start with one feasible Phase II content block "
         "and one short writing/recall block daily; increase after Phase I. Adapt time to "
         "your baseline and available hours."),
    ]),
    ("Using your material without drowning in it", [
        ("Assign each resource one job",
         "Full notes explain; objective questions test discrimination; descriptive questions "
         "test organisation/application; short notes support retrieval; infographics refresh "
         "a map. Do not read all five versions cover-to-cover or make another full notebook."),
        ("Reverse-learning loop",
         "Fresh question -> classify the gap -> targeted full-note repair -> short closed-book "
         "explanation -> a new application question -> spaced retest. Distinguish knowledge "
         "missing, rule confusion, stale value, weak analysis, poor selection and time failure."),
        ("One compact topic packet",
         "Keep a concept map; one comparison table; a few dated evidence anchors; "
         "objective exceptions/rules; two descriptive skeletons; and your error list. "
         "One or two pages is a revision goal, not a restriction that forces important "
         "syllabus detail to disappear. Detailed notes remain the reference."),
        ("Currency and verification",
         "Your Reports_NationalAndInternational, SchemesAndGovernmentPortals and "
         "CurrentAffairs-Monthly folders are useful starting material. File names/editions "
         "are not certification of current accuracy. Check official scope, release/reference "
         "date and policy effective date before using numbers in an exam."),
        ("English resource gap",
         "No dedicated English folder appears under SubjectNotesForPhase2. Use the supplied "
         "usable English tasks and fresh passages for production practice; ESI/FM notes "
         "supply content, not a substitute for writing/precis feedback."),
    ]),
]


def audit_rows():
    rows = []
    for subject, by_year in DESCRIPTIVE.items():
        for year, prompts in by_year.items():
            if len(prompts) != 6:
                raise ValueError(f"{subject} {year}: expected six offered prompts")
            for index, (family, summary) in enumerate(prompts, 1):
                rows.append({
                    "subject": subject, "year": year, "original_question": index,
                    "section": "Descriptive", "offered_marks": 15 if index <= 3 else 10,
                    "family": family, "paraphrased_demand": summary,
                    "source": f"PYP\\{year} (Phase 1-2).pdf",
                    "section_pdf_page_start": PAGES[year][subject][0],
                    "section_pdf_page_end": PAGES[year][subject][1],
                })
    if len(rows) != 60:
        raise ValueError("Expected 60 offered ESI/FM descriptive prompts")
    return rows


def source_links(subject):
    links = [
        ("Official supplied 2025 Phase II syllabus",
         ROOT / "PYP" / "Latest-RBI-Grade-B-Syllabus-2025-Official-PDF.pdf"),
        ("Your ESI notes", ROOT / "SubjectNotesForPhase2" / "ESI"),
        ("Your Finance notes", ROOT / "SubjectNotesForPhase2" / "Finance"),
        ("Your Management notes", ROOT / "SubjectNotesForPhase2" / "Management"),
        ("Reports supplied by you", ROOT / "SubjectNotesForPhase2" / "Reports_NationalAndInternational"),
        ("Scheme/portal notes and practice", ROOT / "SubjectNotesForPhase2" / "SchemesAndGovernmentPortals"),
        ("Monthly current-affairs material", ROOT / "SubjectNotesForPhase2" / "CurrentAffairs-Monthly"),
    ]
    for year in YEARS:
        a, b = PAGES[year][subject]
        links.append((f"{year} {subject}: original PDF pp{a}-{b}",
                      ROOT / "PYP" / f"{year} (Phase 1-2).pdf"))
    for _, path in links:
        if not path.exists():
            raise FileNotFoundError(path)
    return links


def sections(subject):
    data = {"ESI": ESI, "FM": FM, "English": ENGLISH}[subject]
    evidence = []
    if subject in DESCRIPTIVE:
        for year, prompts in DESCRIPTIVE[subject].items():
            text = "; ".join(
                f"Q{i} ({15 if i <= 3 else 10}m): {summary}"
                for i, (_, summary) in enumerate(prompts, 1)
            )
            a, b = PAGES[year][subject]
            evidence.append((f"{year} | original section PDF pp{a}-{b}", text + "."))
        evidence.append(("How to interpret this audit",
                         "These are paraphrased offered prompts, not model answers or "
                         "proof that the same topic will return. Recent papers list three "
                         "15-mark and three 10-mark options; use the actual selection "
                         "instructions. Objective evidence references above are separate "
                         "from descriptive Q numbers. DQ means descriptive question."))
    else:
        for year, record in ENGLISH_AUDIT.items():
            a, b = PAGES[year]["English"]
            evidence.append((
                f"{year} | original PDF pp{a}-{b}",
                f"Essay choices: {record['essay']}. Precis: {record['precis']}. "
                f"RC: {record['rc']}. Limits: {record['limits']}.",
            ))
        evidence.append(("2019 supplementary evidence",
                         "Original PDF pp68-70: higher education, youth stress, NBFC recovery, "
                         "voting/democracy and 5G essay choices; inflation precis; economy/"
                         "reforms comprehension. The older shorter format is not a current "
                         "word-limit template. Do not treat compilation year as verification "
                         "of every passage's contemporaneity."))
    return data + [
        ("Studying with mind maps, tables and worked examples", VISUAL_METHODS[subject]),
        ("Making visual notes stick: recall and practice", VISUAL_RECALL),
        ("Source-year audit: what was actually offered", evidence),
    ] + COMMON + [
        ("Evidence limits and official source stack", [
            ("Authority",
             "The official supplied syllabus is a 2025 Phase II excerpt. Exam timings, marks "
             "and choice structure used for planning are corroborated by the supplied "
             "guidebook pp26-27 and paper labels, not a supplied complete 2027 notification. "
             "Confirm final structure and instructions from RBI before the exam."),
            ("What the sample cannot establish",
             "No candidate scripts, examiner rubrics, actual awarded descriptive marks or "
             "question-level empirical solve times were supplied. Therefore this guide cannot "
             "rank topics by proven scoring ease, promise 75-80, or infer exact future marks. "
             "Five modern papers support patterns, not a narrow guaranteed list."),
            ("Use historical questions correctly",
             "Learn the concept/fact template, not stale figures. The guide paraphrases "
             "demands rather than endorsing every recollected premise. Automated old "
             "topic tags were not used as verified frequency counts. Offered prompt counts "
             "are not distinct concepts, candidate attempts or mark shares."),
            ("Official updates",
             "RBI: https://www.rbi.org.in/ ; SEBI: https://www.sebi.gov.in/ ; "
             "Budget/Survey: https://www.indiabudget.gov.in/ ; MoSPI: https://mospi.gov.in/ ; "
             "PIB: https://pib.gov.in/ . Use the relevant ministry/report issuer for "
             "scheme eligibility and report-specific findings."),
            ("How to use the companion HTML",
             "The HTML has clickable source and notes-folder links plus the same full "
             "analysis. PDFs provide bookmarked printable copies. The CSV exposes all "
             "60 ESI/FM descriptive prompts and the JSON preserves the English task audit."),
        ]),
    ]


def write_pdf(subject, content):
    book = Book(subject, phase="Phase II")
    title = {"ESI": "Economic and Social Issues", "FM": "Finance and Management",
             "English": "English Writing Skills"}[subject]
    book.new_page()
    book.text(f"{title}: deep study analysis", 20, True)
    book.text("Subject-wise target: 75-80/100 | depth AND syllabus-wide breadth", 12, True)
    book.text(
        "Prepare to retrieve, distinguish, apply and explain - not just finish reading. "
        "This is an evidence-led study guide based on your supplied papers and syllabus, "
        "not an official marking scheme or score guarantee. All examples use original "
        "source question numbers; DQ denotes descriptive. No model answers are included.", 10
    )
    book.text("Contents (PDF bookmarks provide navigation)", 13, True)
    for heading, _ in content:
        book.text(heading, 10)
    for heading, blocks in content:
        book.new_page()
        book.bookmarks.append([1, heading, len(book.document)])
        book.text(heading, 17, True)
        for label, text in blocks:
            if book.y + 85 > BOTTOM:
                book.new_page()
            book.text(label, 11, True)
            book.text(text, 10)
    book.document.set_toc(book.bookmarks)
    book.document.set_metadata({
        "title": f"RBI Grade B Phase II - {title} - 75-80% Study Analysis",
        "subject": "Historical patterns, official syllabus breadth, depth and practice",
        "creator": "Local supplied-paper analysis",
    })
    path = OUTPUT / f"phase2_{subject.lower()}_analysis.pdf"
    book.document.save(path, deflate=True, garbage=4)
    book.document.close()
    with pymupdf.open(path) as saved:
        if len(saved.get_toc()) != len(content):
            raise ValueError(f"{subject}: missing bookmarks")
        text = " ".join(page.get_text() for page in saved)
        for phrase in ["75-80", "2021", "2025", "Evidence limits"]:
            if phrase not in text:
                raise ValueError(f"{subject}: missing {phrase}")
        for page in saved:
            for block in page.get_text("dict")["blocks"]:
                if block["type"] == 0 and block["bbox"][3] > 828:
                    raise ValueError(f"{subject}: text exceeds print area, p{page.number + 1}")
        print(f"{path.name}: {len(saved)} pages, {len(content)} bookmarked sections")
    return path


def build(html_only=False):
    evidence_extension = render_evidence_extension(OUTPUT)
    chapter_roadmap = render_chapter_roadmap(OUTPUT)
    topper_findings = render_topper_findings(OUTPUT)
    rows = audit_rows()
    with (OUTPUT / "phase2_descriptive_pattern_audit.csv").open(
            "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUTPUT / "phase2_english_task_audit.json").write_text(
        json.dumps(ENGLISH_AUDIT, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    esc = html.escape
    fragments = []
    nav = ['<a href="#chapter-roadmap">Specific topics &amp; AI prompts</a>',
           '<a href="#weightage">Marks &amp; distribution</a>',
           '<a href="#detailed-what">Reports, schemes &amp; policies</a>',
           '<a href="#topper-insights">Topper tips &amp; traps</a>']
    for subject in ("ESI", "FM", "English"):
        content = sections(subject)
        pdf = OUTPUT / f"phase2_{subject.lower()}_analysis.pdf" if html_only else write_pdf(subject, content)
        nav.append(f'<a href="#{subject}">{subject}</a>')
        fragments.append(f'<section id="{subject}"><h1>{subject}: 75-80% preparation</h1>'
                         '<p class="task-jump"><b>Want one specific topic to give an AI agent?</b> '
                         + ({
                             "ESI": '<a href="#chapters-ESI">Open ESI topics and copyable prompts</a>.',
                             "FM": '<a href="#chapters-Finance">Finance topics and prompts</a> | '
                                   '<a href="#chapters-Management">Management topics and prompts</a>.',
                             "English": '<a href="#chapters-English">English writing/comprehension tasks and prompts</a>.',
                         }[subject]) +
                         ' Each topic states the exact concepts, calculations or exercises to cover, '
                         'with linked chapter notes.</p>'
                         f'<a href="{pdf.name}">Original printable subject analysis PDF</a>'
                         '<p>The new detailed inventories and distribution are in this HTML; '
                         'the linked original PDF does not include that extension. '
                         'Use browser Print to PDF to save the complete updated report.</p>')
        fragments.append('<details><summary>Source papers and your existing study material</summary><ul>')
        for label, path in source_links(subject):
            fragments.append(f'<li><a href="{esc(path.as_uri(), quote=True)}">{esc(label)}</a></li>')
        fragments.append('</ul></details>')
        for heading, blocks in content:
            fragments.append(f'<article><h2>{esc(heading)}</h2>')
            for label, text in blocks:
                fragments.append(f'<h3>{esc(label)}</h3><p>{esc(text)}</p>')
            fragments.append('</article>')
        fragments.append('</section>')
    assets = Path(__file__).parent
    styles = (assets / "phase2_report.css").read_text(encoding="utf-8")
    script = (assets / "phase2_report.js").read_text(encoding="utf-8")
    page = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Phase II: subject-wise 75-80% study analysis</title>'
        '<style>' + styles + '</style><body>'
        '<a class="skip-link" href="#main-content">Skip to study content</a>'
        '<header class="app-header"><a class="brand" href="#report-top">RBI / Study atlas'
        '<small>PHASE II PREPARATION</small></a>'
        '<div class="toolbar" role="group" aria-label="Reading controls">'
        '<button class="menu-button" id="open-navigation" aria-controls="report-sidebar" aria-expanded="false">Chapters</button>'
        '<button id="smaller-text" aria-label="Decrease reading text size">A-</button>'
        '<button id="larger-text" aria-label="Increase reading text size">A+</button>'
        '<button id="focus-reading" class="focus-button" aria-pressed="false">Focus reading</button>'
        '<button id="print-report">Print / PDF</button>'
        '<span id="text-size-status" class="skip-link" role="status" aria-live="polite"></span>'
        '</div></header>'
        '<aside class="sidebar" id="report-sidebar" aria-label="Study navigation">'
        '<button class="drawer-close" id="close-navigation">Close navigation</button>'
        '<nav class="quick-links" aria-label="Report sections">' + ''.join(nav) + '</nav>'
        '<h2>Find your next topic</h2>'
        '<label class="search-label" for="chapter-search">Search chapters &amp; content</label>'
        '<input id="chapter-search" type="search" placeholder="Try Basel, poverty, WDR..." aria-controls="chapter-results">'
        '<label class="search-label" for="subject-filter">Subject</label>'
        '<select id="subject-filter"><option value="">All subjects</option><option>ESI</option>'
        '<option>FM</option><option>English</option></select>'
        '<button id="clear-search">Clear search</button>'
        '<p class="search-status" id="search-status" role="status" aria-live="polite"></p>'
        '<nav id="chapter-results" aria-label="Searchable study sections"></nav></aside>'
        '<main id="main-content" class="reader" tabindex="-1">'
        '<p id="reading-location" class="reading-location"></p>'
        '<div class="hero" id="report-top"><span class="eyebrow">Evidence-led / offline / 2021-2025 papers</span>'
        '<h1>Your Phase II study atlas</h1>'
        '<p>Know what to study, why it matters and where your notes are. '
        '93 chapter roadmaps with specific topic tasks and complete copyable AI prompts. '
        'ESI, Finance, Management and English. Target: 75-80% per subject.</p>'
        '<div class="hero-links"><a href="#chapters-ESI">ESI chapters</a>'
        '<a href="#chapters-Finance">Finance chapters</a>'
        '<a href="#chapters-Management">Management chapters</a>'
        '<a href="#chapters-English">English chapters</a>'
        '<a href="#topper-insights">Topper tips &amp; traps</a></div></div>'
        '<noscript><p class="no-js">Interactive search needs JavaScript. All study content and '
        'chapter links remain available below.</p></noscript>'
        '<p>Based on supplied 2021-2025 papers and the official supplied 2025 syllabus. '
        'Historical question patterns are not future guarantees. Original question references '
        'and source limitations are retained.</p>'
        '<p><a href="phase2_descriptive_pattern_audit.csv">60-prompt descriptive audit</a> | '
        '<a href="phase2_english_task_audit.json">English task audit</a></p>'
        + chapter_roadmap + topper_findings + evidence_extension + ''.join(fragments)
        + '<a class="back-top" href="#report-top">Back to overview</a></main>'
        '<script>' + script + '</script></body></html>'
    )
    (OUTPUT / "phase2_deep_analysis.html").write_text(page, encoding="utf-8")
    print("Saved companion HTML and audits.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html-only", action="store_true", help="Update HTML and audits without rebuilding original subject PDFs")
    build(html_only=parser.parse_args().html_only)
