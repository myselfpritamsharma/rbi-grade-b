"""Numbered static/current study targets and checked local notes for every supplied chapter."""

import html
import json
import re
from pathlib import Path

from phase2_topic_tasks import chapter_key, load_tasks, make_prompt

# Folder | explained Study Studio topic IDs | static targets | current/evidence targets
# Semicolons separate numbered targets; current targets are preparation recommendations,
# not claims that each item appeared in a historical question.
ESI = """
ESI Dictionary-0|esi-glossary|GDP/GVA and stock/flow vocabulary;Fiscal/monetary, real/nominal and growth/development distinctions;Banking, trade, welfare and demographic terms in application|Extract unfamiliar terms from current RBI/Budget/report reading;Record changed institutional or product definitions with effective dates
National Income Accounting-1|esi-national-income|GDP/GVA bridges and valuation;Nominal/real GDP, deflator and base year;Per-capita income, expenditure components and measurement limits;Growth versus level and percentage-point versus percent change|Latest national-account estimates and revisions, labelled by period;Economic Survey growth drivers and sector shares;Compare forecasts from IMF, World Bank, OECD and RBI without mixing vintages
Economic Growth and Development-2|esi-growth-development|Growth versus development and welfare;Capital formation, productivity and structural transformation;Inequality, inclusion and sustainability trade-offs;Mechanisms linking investment, jobs and living standards|Economic Survey growth constraints and priorities;WDR middle-income transition and investment/infusion/innovation;Latest growth projections and reasons for revisions
School Of Economic Thoughts-3|esi-economic-thought|Classical, Keynesian and major policy perspectives;Demand versus supply constraints;Market failure, state intervention and incentive effects;Use assumptions to explain differing policy prescriptions|Interpret fiscal/monetary responses to contemporary shocks;Debates on inflation, employment and industrial policy as applications, not a theorist-news memorisation list
Human Development-4|esi-human-development|Capabilities versus income;Health/education/productivity feedback;Index dimensions, normalisation and rank versus score;Human capital versus human development|World Bank Human Capital Index/Project;Latest available UNDP human-development indicators and methodology;Education/health findings with disaggregated inequality
Sustainable Development-5|esi-sustainable-development|SDGs, externalities and intergenerational equity;Mitigation/adaptation, physical/transition risks;Intensity versus absolute emissions;Circular economy and just transition|Mission LiFE and PM-PRANAM;FAO FRA, Sustainable Development Report and relevant SDG assessments;RBI climate-focused Currency and Finance report;Green Credit Programme, environmental audit rules and climate commitments
Nature of Indian Economy-6|esi-economy-nature|Sector structure and dualism;Informality, productivity and demographic conditions;Rural/urban and regional inequalities;Public/private roles and inclusive transformation|Economic Survey sector shares, jobs and productivity;Current MSME/agriculture/services constraints;Use date-consistent indicators instead of an undated India fact list
Nature of Indian Economy before Independence-7|esi-colonial-economy|Colonial agriculture, industry and trade structure;Deindustrialisation, land relations and infrastructure incentives;Poverty, human capital and institutional constraints|Use historical foundations to explain present structural legacies;No separate recurring monthly-current list established: use only relevant contemporary comparisons
Nature of Indian Economy 1947-1991 Macro-economy-8|esi-planned-economy-sectors|Planning, mixed economy and public sector;Savings/investment and growth constraints;Licence controls and macro imbalances;Background to the 1991 crisis|Compare historical constraints with current reform debates;Do not memorise every annual target as current affairs
Nature of Indian Economy 1947-1991 Agriculture-9|esi-planned-economy-sectors,esi-agriculture|Land reform, irrigation and Green Revolution;Food security, procurement and input support;Regional/crop disparities and productivity;Institutional credit and rural development|Compare legacy input-support design with current sustainability reforms;Link contemporary food-security and fertiliser policy only where it explains continuity/change
Nature of Indian Economy 1947-1991 Industry-10|esi-planned-economy-sectors,esi-industry|Industrial-policy regimes and licensing;Public sector, small-scale reservation and protection;Competition, scale and productivity constraints|Compare current industrial corridors/startup/MSME reforms with historical controls;Historical chronology is a foundation, not a request for monthly scheme trivia
Nature of Indian Economy 1947-1991 Services-11|esi-planned-economy-sectors,esi-services|Bank nationalisation and service expansion;Transport/communications and social infrastructure;Regulation and productivity limits|Compare historical access objectives with current digital-service delivery;Use present services data as a comparison, not as evidence of historical outcomes
Nature of Indian Economy 1947-1991 External Sector-12|esi-planned-economy-sectors,esi-external-sector|Import substitution and trade protection;Exchange controls, BoP constraints and external borrowing;1991 external vulnerability|Compare contemporary reserves/current-account risks with the historical crisis;Distinguish current capital openness from the pre-reform regime
Economic Reforms-13|esi-reforms|Stabilisation versus structural reform;Liberalisation, privatisation and globalisation;Industrial, trade, financial and fiscal reforms;Distributional effects and sequencing|Current disinvestment, industrial/labour-policy changes and implementation;Economic Survey reform proposals;Pandemic/crisis responses linked to reform constraints
Nature of Indian Economy Post 1991 Macro-economy-14|esi-post1991-macro|Growth phases, investment and saving;Demand composition, productivity and macro stability;Reform-outcome versus correlation|Economic Survey growth/inflation/jobs outlook;Budget priorities and policy trade-offs;Latest dated GDP, investment and fiscal evidence
Nature of Inidan Economy Post 1991 Agriculture-15|esi-agriculture|Farm productivity, holdings and cropping;Markets, price risk, procurement and food security;Irrigation, inputs, credit and value chains|PM-KISAN, PM Dhan-Dhaanya, AIF and PMMSY;Operation Greens, PM-PRANAM and farmer portals;Survey farm growth and market trends;Eligibility, exclusions, funding and last-mile delivery cases
Nature of Indian Economy Post 1991 Industry-16|esi-industry|Industrial productivity, scale and competitiveness;MSME/startup definitions and constraints;Clusters, corridors, logistics and formalisation|Udyam/Udyam Assist and Startup India rules;Industrial-corridor developments and Budget enterprise measures;MUDRA, Stand-Up India, SVANidhi and relevant current manufacturing initiatives
Nature of Indian Economy Post 1991 Services-17|esi-services|Services output versus employment;IT/BPO, tourism, logistics and financial services;Tradability, skills and digital delivery|Survey services exports/jobs trends;Digital India, medical-tourism and platform developments;AI and service-productivity risks as applied examples
Nature of Indian Economy Post 1991 External Sector-18|esi-external-sector|BoP/current versus capital account;Exchange-rate transmission and convertibility;FDI/FPI, trade creation/diversion and global value chains|India-Australia ECTA and relevant new agreements;Foreign Trade Policy/deemed-export rules;WTO/TRIPS developments and globalisation after crises;Latest trade/capital-flow data and dated regulatory changes
Public Expenditure and Receipts-19|esi-public-finance|Revenue/capital receipts and spending;Tax/non-tax and debt/non-debt flows;Public goods, redistribution and opportunity cost|Union Budget expenditure/receipt priorities;Scheme allocation versus release versus utilisation;Digital initiatives, subsidies and disinvestment receipts
Public Debt-20|esi-public-debt|Debt stock versus deficit flow;Interest-growth-primary-balance dynamics;Maturity/currency/refinancing risk;Crowding out and intergenerational effects|Budget debt/interest indicators;RBI government-borrowing and fiscal-risk commentary;Dated debt comparisons with consistent coverage
Fiscal Policy-21|esi-fiscal-policy|Fiscal/revenue/primary deficits;Multipliers, automatic stabilisers and discretion;Consolidation versus development spending;Monetary-fiscal coordination|Current Budget fiscal path and FRBM-related changes;Growth/inflation policy mix;Tax/expenditure measures and distributional consequences
Federal Finance-22|esi-federal-finance|Vertical versus horizontal imbalance;Tax devolution versus grants;Finance Commission criteria and fiscal transfers;Local-government finance|Applicable Finance Commission recommendations and transition;Union/State fiscal transfers and grants;GST Council developments and state fiscal capacity
Poverty-23|esi-poverty|Monetary versus multidimensional poverty;Incidence, intensity and vulnerability;Targeting, inclusion/exclusion errors;Safety nets versus public-service quality|ONORC/NFSA, PM CARES for Children and welfare-delivery changes;Latest comparable poverty evidence and methodology;WDR welfare reference requires edition authentication;Prepare three verified poverty/employment programme examples
Unemployment-24|employment-measurement|LFPR, WPR and unemployment;Reference periods, denominators and comparability;Youth/female employment, informality and underemployment;Skills and labour demand|Latest PLFS indicators and Survey job estimates;NCS, skill programmes and e-Shram;Labour-code implementation and social security;Tier-2/3 entrepreneurship and youth employment examples
Population Growth and Demography-25|esi-demography|Fertility/mortality and demographic transition;Dependency ratio and demographic dividend;Ageing, migration and regional variation;Population versus participation effects|Latest demographic estimates with Census/survey/projection distinction;PM-SYM, PM-KMY, APY/NPS and ageing support;Care economy and labour-supply evidence
Health-26|esi-health|Public health versus clinical care;Risk pooling, insurance and financial protection;Access, affordability, quality and prevention;Health-productivity-poverty feedback|PM-JAY, Janaushadhi and public-health apps;Disease/maternal-health service delivery;Latest comparable health indicators and health spending;Eligibility and benefit cases, not only scheme launch facts
Education-27|esi-education|Access versus learning and attainment;Human-capital externalities;Inequality, digital divide and skill mismatch|STARS, PM eVIDYA, PMKK and SHRESHTA;Current learning/education evidence and funding;Digital delivery accessibility and implementation;Scholarship eligibility and named programme identity
Gender Issues-28|esi-gender-issues|Agency, resources and gender norms;Labour participation, care work and violence;Equality/equity and intersectionality|UNDP gender strategy/GSNI, WEF Gender Gap and Gender Snapshot;Beijing+30 action agenda and relevant alliance;Women-led rural development and enterprise measures;Swadhar/One Stop Centre, savings and inclusion schemes
Positive Discrimination-29|esi-positive-discrimination|Formal versus substantive equality;Caste/disadvantage and representation;Affirmative-action rationale, design and limitations;PVTG identification criteria|PM-AJAY, PVTG development mission and SHRESHTA;Social-justice programmes and beneficiary cases;Current inclusion evidence and implementation safeguards
Internation Economic Institutions-30|esi-international-institutions|IMF/World Bank/WTO mandates;Governance, finance and instruments;WTO origins/decision-making;Institution versus report versus project|WEO, WDR, OECD Outlook and Human Capital publications;Current heads/membership only as dated facts;Trade/IP developments and relevant international policy cooperation
Roles of Banks and RBI in Development Process-31|esi-banks-rbi|Bank/NBFC distinction and development role;Money/credit transmission and liquidity;Policy framework, corridor and instruments;Inclusion and financial stability|RBI policy statements and liquidity changes;FSR, inclusion measures and bank/NBFC developments;AI in banking, payments and CBDC;Current rule versus conceptual mechanism
Rural Credit and Microfinance-32|esi-rural-credit|Formal/informal credit and market failure;NABARD/RRB/cooperative roles;SHG/microfinance mechanisms and borrower risks;Credit access versus productive use|MUDRA, Stand-Up India, farm credit and cooperative initiatives;Current microfinance/customer-protection changes;Scheme eligibility and rural enterprise cases
Inflation-33|esi-inflation|CPI/WPI/deflator and index interpretation;Demand-pull/cost-push and expectations;Food/supply shocks and real income;Policy trade-offs and transmission|Latest inflation prints with base/month/year;RBI forecasts, stance and policy measures;Survey price risks and food/energy developments;Distinguish forecast, target and actual
Planning Period in India (5 Year Plans)-34|esi-planning|Planning objectives, instruments and allocation;Broad plan-era strategy shifts;Planning Commission/NITI roles;Targets versus outcomes|Current district/convergence planning and NITI-related monitoring;Aspirational Districts as a contemporary application;No need to treat all old plan outlays as current facts
Multiculturism-35|esi-multiculturalism|Pluralism, diversity and common citizenship;Assimilation/integration and recognition;Minority rights, cohesion and democratic participation;Opportunities and tensions|Current examples of inclusion, migration and language access;Use verified policy cases, not partisan generalisations;No fixed report list is established by the descriptive demand
Urbanisation and Migration-36|esi-urbanisation-migration|Push/pull factors, agglomeration and congestion;Housing, services, informality and municipal capacity;Origin/destination effects and migrant rights|WDR migration recommendations;AMRUT, PMAY-U 2.0, Angikaar and Smart Cities;ONORC migrant portability and a verified city case;Climate migration and inclusive urban outcomes
Indian Taxation System-37|esi-taxation|Direct/indirect taxes and incidence;GST input-tax credit and destination principle;Buoyancy/elasticity, equity and efficiency;Tax expenditure and compliance|Current Budget tax changes and GST Council decisions;Revenue evidence and rate/threshold effective dates;Link tax design with consumption, investment and state finance
"""

FINANCE = """
Finance Dictionary-0||Instrument, institution and market vocabulary;Risk/return, liquidity/solvency and debt/equity distinctions;Read units, tenors and denominators|New terms from RBI/SEBI circulars;Maintain dated definitions for new products rather than memorising abbreviations alone
Regulatory Bodies-1|oct26-supervision-stability-cyber|RBI/SEBI/IRDAI/PFRDA mandates;Regulator versus operator, depository and clearer;Prudential versus conduct supervision|New circulars by authority/applicability/effective date;SEBI investor protection and RBI supervisory changes;Current institutional powers verified against primary rules
Indian Banking System-2|esi-banks-rbi,oct26-ownership-and-bank-status|Bank balance sheet and functions;Commercial/cooperative/RRB/SFB/payments-bank distinctions;Deposits, credit, ownership and governance|Banking reforms and ownership/amalgamation changes;SFB inclusion measures and current licensing conditions;Latest RBI banking-sector evidence
Non Banking System-3|oct26-nbfc-and-upi|NBFC categories and bank differences;Business models and funding risks;Prudential regulation and customer protection|Current NBFC classification/capital/NPA directions;FSR sector risks and interconnectedness;Dated deposit-taking and conduct rules
Indian Financial System-4|esi-banks-rbi,oct26-banking-inclusion-reform|Institutions, markets, instruments and services;DFIs and financial intermediation;Savings-investment and inclusion channels|NaBFID and development-finance initiatives;Financial-system reform and stability reports;Institution-specific mandate/regulator changes
Financial Markets-5|oct26-bond-market-infrastructure,oct26-closing-auction-and-ipo|Money/capital, primary/secondary and exchange/OTC markets;Price discovery, liquidity and settlement;CP/CD/T-bill/G-sec/equity basics|ASBA/UPI public-issue rules;NDS-OM and bond-platform access;Settlement/corporate-action changes;MWPL/derivatives surveillance updates
Risk Management In Banking-6|oct26-capital-and-leverage,oct26-supervision-stability-cyber|Credit/market/liquidity/operational risks;Basel pillars, capital quality and RWA;Buffers, leverage and stress testing;Outsourcing/cyber/vendor risk|Current capital/leverage/counterparty rules;FSR and supervisory priorities;Outsourcing, cyber and model-risk changes
Financial Inclusion-7|oct26-banking-inclusion-reform|Access, usage and quality;Account/insurance/pension/credit distinctions;Digital divide and consumer protection|PMJDY, PMJJBY, PMSBY and APY rules;PIDF, JAM, SFB and lead-bank measures;Latest inclusion indicators;Eligibility/benefit/premium/renewal cases
Alternative Source of Finance-8|oct26-portfolio-management,oct26-debt-instruments-and-risk|Factoring/forfaiting, securitisation and pooled finance;REIT/InvIT structure and cash flows;Risk, recourse and liquidity|InvIT allocation/distribution changes;SM REIT/SIF/PMS/AIF frameworks and thresholds;New alternative-finance rules dated by product
Corporate Governance in Banking-9|oct26-supervision-stability-cyber|Agency/stakeholder issues and board accountability;Independent/non-executive directors;Audit/risk committees and conflicts|RBI board/committee composition, quorum and tenure rules;Governance enforcement and disclosure changes;Keep Companies Act and bank-specific rules separate
Money and Inflation-10|esi-inflation,oct26-monetary-policy,oct26-crr-liquidity|Money creation and monetary aggregates;CPI/WPI and demand/cost shocks;Policy corridor, reserve requirements and transmission|RBI policy decisions, liquidity operations and forecasts;Latest price data and revisions;Dated WMA limits and fiscal/monetary mix
FinTech-11|programmable-digital-rupee,oct26-investor-protection-and-ai,oct26-nbfc-and-upi|Payments architecture and settlement;CBDC versus UPI/deposit/crypto;Blockchain applications and limits;AI data/model/cyber/ethics risks|UPI Circle and pre-sanctioned credit lines;RBI sandbox/PIDF/CBDC developments;ONDC/TReDS and relevant digital rules;Consent, limits and effective dates
Global Financial Markets and International Banking-12|oct26-forex-risk-and-swaps|FX spot/forward/swap and international capital flows;Exchange/country/counterparty risks;Cross-border intermediation|Global financial conditions and spillovers;Bilateral swaps/cross-border payments;Relevant international prudential developments and dated LRS rules
FDI FPI Disinvestment-13|esi-external-sector,oct26-ownership-and-bank-status|FDI/FPI distinction and control;Sectoral caps versus individual holdings;Strategic/non-strategic disinvestment;Flow versus stock|Current bank ownership caps and FPI limits;Budget disinvestment measures;Policy changes by route/sector/effective date
GST-14|oct26-gst|Destination-based tax and federal design;ITC, input/output liability and refunds;Exempt/zero-rated distinctions|GST Council decisions and notified implementation;Rate/compliance/refund changes;Fiscal federalism and business effects, with current status
Basics of Accounting-15||Accounting equation, debit/credit and accrual;Assets/liabilities/equity/income/expense;Capital versus revenue treatment;Statements and basic adjustments|Use current annual-report extracts only as practice inputs;Relevant accounting/disclosure changes if they alter the syllabus concept;No separate recurring news list established
Impact Of Global Financial Crisis-16||Crisis origins, leverage and securitisation;Liquidity/solvency and contagion;India's exposure and monetary/fiscal response|Compare the 2008 response with current stability frameworks;FSR vulnerabilities and buffer-building;Historical measures remain historical evidence
Preparation of Company Final Accounts-17||Trading/P&L/balance-sheet links;Closing stock, depreciation and provisions;Accrual/prepayment adjustments;Classification and statement consistency|Apply to recent public financial statements without importing irrelevant audit detail;Track a rule change only if it affects the studied presentation
Cash Flow Statement-18||Operating/investing/financing flows;Cash versus profit;Indirect-method adjustments;Working-capital changes|Use a recent statement for ratio/quality-of-earnings interpretation;No fixed monthly-current requirement shown by the sample
Ratio Analysis-19||ROA/ROE/EPS/P-E and book/market value;Liquidity, leverage, turnover and profitability;Numerator/denominator and average-versus-closing values;Linked accounting numerical cases|Apply ratios to dated bank/company figures;Do not compare different accounting bases;Use market-price changes as inputs, not news to memorise
Indian Taxation System and Public Expenditure-20|esi-taxation,esi-public-finance|Tax incidence, direct/indirect tax and GST basics;Receipts/expenditure and deficit classification;Public spending and distribution|Budget tax/expenditure measures and revenue data;GST implementation updates;Tax thresholds and legal effective dates
FRBM Act and Finance Commission-21|esi-fiscal-policy,esi-federal-finance|Deficits, debt and fiscal rules;Fiscal federalism and devolution/grants;Commission role and recommendation periods|Current Budget consolidation path;Applicable Finance Commission recommendations;Fiscal-rule amendments/escape provisions verified from notified material
Trading and Investment-22|oct26-portfolio-management,oct26-debt-instruments-and-risk|Value/growth investing and valuation;Bond price/yield, duration and credit risk;Derivative payoffs and hedging;Portfolio diversification and investor suitability|AT1 and debt-product disclosures;SIF/REIT/InvIT/PMS changes;Investor-protection and advertising rules;Current settlement/product limits
RBI Act 1934-23|esi-banks-rbi,oct26-monetary-policy|RBI mandate and major statutory functions;Currency, reserves, government banking and monetary framework;Act versus other banking/payment laws|Notified amendments and monetary-framework developments;Do not attribute every RBI power to one Act;Read legal applicability alongside current circulars
"""

MANAGEMENT = """
Intoduction to Management-1||Efficiency/effectiveness and organisational goals;Managerial levels and skills;Management versus administration/leadership|Apply to a current organisational case;No fixed monthly-news list: learn diagnosis and managerial action
Evolution of Management Thought-2||Taylor, Fayol, Weber and human relations;Systems and contingency approaches;Core assumptions, contribution and limitations|Use automation/remote-work cases to test the theories;Verify recalled thinker attributions rather than treating ambiguous options as facts
Management Functions and Manegerial Role-3||Planning, organising, staffing, directing and controlling;Managerial roles and skills;Coordination and performance feedback|Apply functions to digital transformation and bank risk controls;Use current cases as illustrations, not as a separate trivia syllabus
Organisation and Organisation Structure-4||Functional/divisional/matrix structures;Centralisation, formalisation and span;Line/staff, delegation and coordination|Digital/remote/hybrid organisational design examples;Governance and risk-accountability implications of restructuring
Introduction to Organisation-5||Individual/group/organisation behaviour;Formal/informal organisation;Culture, climate, diversity and inclusion|World Management Survey-style passage applications;Workplace inclusion and technology-change cases;Do not memorise every survey statistic without an actual question demand
Personality-6||Big Five/OCEAN traits;Personality versus mood/attitude;Behavioural indicators and work applications;Limits of prediction/stereotyping|Use workplace cases rather than a monthly fact list;Relevant AI-based hiring bias examples with ethical caveats
Perception-7||Perception process and attribution;Stereotype/halo/selective perception;Bias in appraisal and decisions|Apply to recruitment, credit judgement and digital misinformation;Distinguish a current example from the stable psychological concept
Motivation-8|motivation-theories|Maslow, ERG, McClelland and Herzberg;X/Y, expectancy, equity and goal-setting;Intrinsic/extrinsic incentives;Reinforcement versus punishment|Modern employee motivation, flexible work and reskilling cases;No mandatory scheme/report list established;Link incentives to organisational growth and ethical limits
Leadership-9||Transactional/transformational and Lewin styles;Trait versus behavioural theories;Managerial Grid and contingency/path-goal models;Fit between leader, followers and situation|Change/digital/ethical leadership examples;Employee wellbeing and inclusion;Avoid personality biographies in place of theory comparison
Authority and Power-10||Authority versus power;Legitimate/reward/coercive/expert/referent bases;Delegation, responsibility and accountability|Ethical use of influence in contemporary organisational cases;Governance controls against concentration of authority
Communication-11||Process, encoding/decoding/noise/feedback;Directions, channels and networks;Semantic/personal/organisational barriers;Nonverbal signals and listening|Multilingual/digital/hybrid communication;Translation tools and language initiatives as optional examples;Data privacy, accessibility and consistent nonverbal leadership
Emotional Intelligence-11||Self-awareness/regulation, empathy and social skills;Emotional labour/dissonance;EI versus personality/cognitive ability|Workplace conflict, stress and leadership cases;AI/remote-work interaction as application, not a list of new emotional-intelligence reports
Analysis of Interpersonal Relationship-12||Johari Window;Feedback/disclosure and self-awareness;Interpersonal trust and relationship patterns;Apply any additional syllabus model from supplied notes|Use feedback/coaching cases;Digital communication and culturally diverse teams;No separate recurring current-affairs list established
Decision Making and MBO-13||Rational/bounded-rational decisions;Bias, uncertainty and group decisions;MBO goal setting, alignment and review|Data/AI-supported decisions, accountability and model limits;Current management cases for goal design and measurable outcomes
Morale and Incentive-14||Morale, commitment and satisfaction;Financial/non-financial incentives;Turnover/absenteeism and group climate|Contemporary retention/wellbeing cases;Compare short-term performance incentives with long-term ethical behaviour
Organisational Conflict-15||Sources and levels of conflict;Functional/dysfunctional effects;Negotiation, resolution and escalation|Merger, hybrid-work and diversity cases;Use stakeholder interests and remedies, not generic conflict slogans
Stress and Learning-16||Work stressors and coping/support;Learning mechanisms and reinforcement;Behaviour change and transfer of learning|Employee mental health and technology overload;Organisational prevention/support/privacy measures;Use non-diagnostic workplace language
Organisational Changes and Group-17||Lewin stages and resistance;Group dynamics, norms and team development;Change diagnosis, participation and reinforcement|Merger/digital transformation and training cases;Systematic change implementation and outcome checks;No fixed monthly report requirement
Human Resouce Development-18||Capability development and workforce planning;Career development and talent retention;HRD versus routine HR administration|Reskilling, digital skills and inclusive career opportunities;Use public or hypothetical employer cases without treating trends as universal
Job Analysis, Job Design and Job Evaluation-19||Job description/specification;Enlargement/enrichment/rotation;Job characteristics and evaluation;Job value versus individual performance|Automation and redesign of work;Fairness, safety and accessibility in current job-design cases
Training and Development-20||Needs analysis and training design;Methods, transfer and evaluation;Training versus development;Resistance and managerial support|AI/digital/cyber training and reskilling;Evaluate whether learning changes behaviour/outcomes rather than only attendance
Organisational Development-21||Diagnosis, planned interventions and feedback;Culture/team/process interventions;Participation and sustained change|Current transformation and inclusion cases;Separate OD from a one-off training event or organisational restructuring
Performance Appraisal-22||Objectives and appraisal methods;Bias/error and feedback;Development versus reward decisions;Fairness and measurable criteria|Digital/AI monitoring, privacy and explainability;Hybrid-team evaluation and incentive gaming;Current cases as applications, not a statistics list
Nudge Theory-23||Choice architecture, defaults and salience;Nudge versus mandate/incentive;Behavioural bias and ethical boundaries|Financial inclusion, saving and public-service uptake examples;Evaluate transparency, consent and unintended distributional effects
Ethics-24||Consequentialism, duty, virtue, justice, rights/care;Relativism/absolutism and moral disengagement;Code, culture, whistleblowing and conflicts;Stakeholder-based case analysis|AI/banking ethics, data use, bias and incentives;Verified regulatory conduct examples;Connect current harms to controls and accountability
Corporate Governance In Banking-25||Agency/stakeholder/stewardship;Board accountability, independence and conflicts;CSR versus ethics versus governance;Audit/risk oversight|RBI bank-board/committee directions and amendments;Companies Act CSR thresholds/committee rules;Dated applicability and authority, not recalled misattribution
"""

ENGLISH = [
    ("Essay writing: content and argument", "Read a command and formulate a thesis;Causal/comparative paragraph structure;Counterargument, examples and reasoned conclusion;Grammar, coherence and word-limit editing",
     "Climate/energy and development;Digital finance/business/startup changes;Women entrepreneurship, health and education;Workplace wellbeing and learning",
     "Select one of four topics and cover every named dimension; use the twenty historical topic cards below."),
    ("Essay family preparation", "Build transferable mechanisms, not memorised essays;Separate fact, interpretation and value judgement;Learn balanced evaluation and implementation conditions",
     "Maintain five family sheets from the detailed inventory;Use two verified examples per family;Update dated evidence without predicting the next essay",
     "Create a fresh outline from each of the five families; cross-link ESI/FM knowledge only where relevant."),
    ("Precis writing", "Identify thesis and major propositions;Preserve causal/contrast links and qualifications;Paraphrase and compress faithfully;Count words and check omissions/distortions",
     "No external facts required to answer the given passage;Practise unfamiliar science/economy/technology passages;Use current reading to improve comprehension, never to add outside opinion",
     "Practise all five supplied passage themes; follow the explicit word limit rather than a mechanical one-third rule."),
    ("Reading comprehension", "Retrieve, explain, compare and infer;Preserve technical processes and author stance;Answer the exact command in own words;Distinguish passage evidence from outside knowledge",
     "No fixed current-affairs memorisation list;Practise business, economic and scientific texts;Keep the 2021 mismatched passage/questions out of scored assessment",
     "Use the four coherent supplied RC tasks plus fresh passages; explain a process and a causal inference without distortion."),
    ("Language, editing and timed execution", "Agreement, tense, articles, prepositions and pronoun reference;Parallelism, punctuation and concise syntax;Transitions, paragraph unity and word choice;Typing, time allocation and final checks",
     "No separate monthly-current list;Maintain an error log from your own drafts;Revise examples/facts only where an essay uses them",
     "Complete timed essay/precis/RC work, diagnose omissions before vocabulary, then rewrite the weakest paragraph."),
]


def parse(raw):
    rows = []
    for line in raw.strip().splitlines():
        fields = line.split("|")
        if len(fields) != 4:
            raise ValueError(f"Expected four roadmap fields: {line}")
        folder, topics, static, current = fields
        rows.append(dict(folder=folder, topics=topics.split(",") if topics else [],
                         static=static.split(";"), current=current.split(";")))
    return rows


def numbered(items):
    return "<ol>" + "".join(f"<li>{html.escape(x)}</li>" for x in items) + "</ol>"


def task_list(tasks, chapter_id, subject, title):
    esc = html.escape
    content = ["<ol class='study-task-list'>"]
    for task in tasks:
        task_id = task["id"]
        prompt = task["prompt"]
        label = {"S": "Static explanation", "C": "Current source verification", "A": "Applied practice"}[task["kind"]]
        content.append(
            f"<li class='study-task' id='{task_id}' data-task-kind='{task['kind']}'>"
            f"<span class='task-kind'>{label}</span>"
            f"<h5>{esc(task['title'])}</h5><p>{esc(task['demand'])}</p>"
            f"<p class='task-context'>{esc(subject)} / {esc(title)} / "
            f"<a href='#{chapter_id}'>Chapter notes and context</a></p>"
            f"<details class='ai-prompt'><summary>Ready-to-use AI prompt: {esc(task['title'])}</summary>"
            f"<label for='{task_id}-prompt'>Complete prompt (read-only; attach your notes if needed)</label>"
            f"<textarea id='{task_id}-prompt' class='prompt-text' readonly rows='9' spellcheck='false'>"
            f"{esc(prompt)}</textarea>"
            "<div class='prompt-actions'>"
            f"<button type='button' data-copy-prompt='{task_id}-prompt' aria-describedby='{task_id}-status'>Copy AI prompt</button>"
            f"<button type='button' data-select-prompt='{task_id}-prompt'>Select prompt manually</button>"
            f"<a href='#{task_id}'>Link to this topic</a></div>"
            f"<p id='{task_id}-status' class='prompt-status' role='status' aria-live='polite'></p>"
            "</details></li>"
        )
    content.append("</ol>")
    return "".join(content)


def render_chapter_roadmap(output):
    root = output.parent
    library = json.loads((root / "study_library" / "library.json").read_text(encoding="utf-8"))
    topics = {t["id"]: t for t in library["topics"]}
    all_rows = []
    task_groups = load_tasks()
    used_groups = set()
    esc = html.escape
    parts = ["""<section id="chapter-roadmap" class="evidence-extension">
<h1>Numbered chapter-wise study roadmap</h1>
<p>Each numbered topic below is a <b>specific, independently answerable study task</b>.
Read its exact subquestions, open <b>Ready-to-use AI prompt</b>, then copy it into your AI
agent. The prompt includes the subject, chapter, requested output, practice-answer requirements
and source/date safeguards. You do not need to copy the entire chapter. Attach the linked
notes when you want the agent to use those files; a different agent cannot automatically
access files on this computer.</p>
<p>Static explanations, current source-verification tasks and applied practice are labelled
separately. Current-topic prompts ask the agent to verify status; their presence here does not
authenticate a latest figure or imply every subject requires monthly news. Task selection is a
preparation recommendation, not a claim that every task appeared in a PYQ.</p>
<p>Print/PDF retains all numbered study tasks. The expandable prompt text and copy controls
are HTML-only, avoiding hundreds of repetitions of the same output instructions in print.</p>
<p><b>Notes labels:</b> Explained notes = authored Study Studio teaching prose;
revision packet = maps/tables/cards without a complete teaching chapter;
supplied PDF = your source notes, not a claim that all its contents have been freshly reviewed.
Finance's October examples are not a complete static FM course and their dated claims still
need verification. Where no explained chapter exists, that gap is explicit.</p>
<p><a href="#chapters-ESI">ESI chapters</a> |
<a href="#chapters-Finance">Finance chapters</a> |
<a href="#chapters-Management">Management chapters</a> |
<a href="#chapters-English">English chapters</a></p>"""]
    parts.append("<p><b>Four current-affairs collections to cross-check on updates:</b> ")
    collections = ["CurrentAffairs-Monthly", "Reports_NationalAndInternational", "SchemesAndGovernmentPortals", "StaticGK"]
    links = []
    for collection in collections:
        path = root / "SubjectNotesForPhase2" / collection
        if not path.is_dir():
            raise ValueError(f"Missing evidence collection: {path}")
        links.append(f"<a href='{esc(path.as_uri(), quote=True)}'>{esc(collection)}</a>")
    parts.append(" | ".join(links) + ". Links are optional reading routes; the targets are specified chapter by chapter below.</p>")
    for subject, raw in [("ESI", ESI), ("Finance", FINANCE), ("Management", MANAGEMENT)]:
        rows = parse(raw)
        directory = root / "SubjectNotesForPhase2" / subject
        actual = {p.name for p in directory.iterdir() if p.is_dir()}
        configured = {r["folder"] for r in rows}
        if actual != configured or len(configured) != len(rows):
            raise ValueError(f"{subject} chapter coverage: missing={actual-configured}, extra={configured-actual}")
        rows.sort(key=lambda r: (int(r["folder"].rsplit("-", 1)[-1]), r["folder"]))
        parts.append(f"<article id='chapters-{subject}'><h2>{subject}: {len(rows)} supplied chapters</h2>")
        parts.append("<ol class='chapter-index'>" + "".join(
            f"<li><a href='#chapter-{subject}-{i}'>{esc(re.sub(r'-\\d+$', '', row['folder']))}</a></li>"
            for i, row in enumerate(rows, 1)) + "</ol>")
        for i, row in enumerate(rows, 1):
            folder = directory / row["folder"]
            pdfs = sorted(folder.glob("*.pdf"))
            if not pdfs:
                raise ValueError(f"No supplied notes PDFs: {folder}")
            primary = [p for p in pdfs if "notes" in p.name.lower() and "short" not in p.name.lower()]
            if not primary:
                primary = [p for p in pdfs if "practice" not in p.name.lower() and "question" not in p.name.lower()]
            if not primary:
                raise ValueError(f"No readable source note candidate: {folder}")
            # Keep all full-note parts; select at most two non-note candidates only when no notes are labelled.
            if not any("notes" in p.name.lower() for p in primary):
                primary = primary[:2]
            row["subject"] = subject
            row["chapter_number"] = i
            row["source_notes"] = [str(p.relative_to(root)) for p in primary]
            title = re.sub(r"-\d+$", "", row["folder"])
            key = (subject, chapter_key(subject, row["folder"]))
            if key not in task_groups:
                raise ValueError(f"No specific topic tasks: {key}")
            used_groups.add(key)
            chapter_id = f"chapter-{subject}-{i}"
            row["coverage_static"] = row["static"]
            row["coverage_current"] = row["current"]
            row["tasks"] = []
            for number, task in enumerate(task_groups[key], 1):
                row["tasks"].append(task | {"id": f"{chapter_id}-topic-{number}",
                                            "prompt": make_prompt(subject, title, task)})
            static_tasks = [t for t in row["tasks"] if t["kind"] == "S"]
            other_tasks = [t for t in row["tasks"] if t["kind"] != "S"]
            row["static"] = [t["demand"] for t in static_tasks]
            row["current"] = [t["demand"] for t in other_tasks]
            parts.append(f"<div class='inventory-card chapter-card' id='chapter-{subject}-{i}' "
                         f"data-subject='{subject}'><h3>{subject} {i}. {esc(title)}</h3>"
                         "<h4>1. Static topics: precise explanation and calculation tasks</h4>" +
                         task_list(static_tasks, chapter_id, subject, title) +
                         "<h4>2. Current verification and chapter-specific application</h4>" +
                         task_list(other_tasks, chapter_id, subject, title))
            parts.append("<h4>3. Coverage reminders and historical evidence</h4>"
                         f"<p>Use the <a href='#what-{'ESI' if subject == 'ESI' else 'FM'}'>named-item evidence inventory</a> "
                         "to check historical questions. A chapter's presence here ensures breadth; it does not imply a separately observed question or guaranteed marks.</p>"
                         "<details class='coverage-reminders'><summary>Additional connections to keep in view</summary>"
                         "<p>These are broader coverage reminders, not substitutes for the specific tasks above.</p>"
                         + numbered(row["coverage_static"] + row["coverage_current"]) +
                         "</details><h4>4. Linked notes</h4><ul>")
            explained = False
            for topic_id in row["topics"]:
                if topic_id not in topics:
                    raise ValueError(f"Unknown notes topic: {topic_id}")
                topic = topics[topic_id]
                has_prose = bool(topic.get("teaching_notes"))
                explained |= has_prose
                label = "Explained notes" if has_prose else "Revision packet (not full explained prose)"
                href = "../study_library/index.html#topic=" + topic_id
                parts.append(f"<li><a class='studio-note-link' href='{esc(href, quote=True)}'>{label}: {esc(topic['title'])}</a></li>")
            if not explained:
                parts.append("<li><b>Explained-note gap:</b> no dedicated complete authored chapter is linked here; use the supplied full notes below. A revision packet or related October chapter is not full syllabus coverage.</li>")
            for pdf in primary:
                parts.append(f"<li><a class='supplied-note-link' href='{esc(pdf.as_uri(), quote=True)}'>Supplied PDF: {esc(pdf.name)}</a></li>")
            parts.append(f"<li><a href='{esc(folder.as_uri(), quote=True)}'>All chapter material, including practice/infographics</a></li></ul></div>")
            all_rows.append(row)
        parts.append("</article>")
    parts.append("<article id='chapters-English'><h2>English: five preparation chapters</h2>")
    for i, (name, static, current, task) in enumerate(ENGLISH, 1):
        key = ("English", str(i))
        if key not in task_groups:
            raise ValueError(f"No specific English tasks: {key}")
        used_groups.add(key)
        chapter_id = f"chapter-English-{i}"
        tasks = [t | {"id": f"{chapter_id}-topic-{number}", "prompt": make_prompt("English", name, t)}
                 for number, t in enumerate(task_groups[key], 1)]
        static_tasks = [t for t in tasks if t["kind"] == "S"]
        other_tasks = [t for t in tasks if t["kind"] != "S"]
        parts.append(f"<div class='inventory-card chapter-card' id='chapter-English-{i}' data-subject='English'>"
                     f"<h3>English {i}. {esc(name)}</h3><h4>1. Specific writing and comprehension tasks</h4>" +
                     task_list(static_tasks, chapter_id, "English", name) +
                     "<h4>2. Applied exercises and source-checked evidence</h4>" +
                     task_list(other_tasks, chapter_id, "English", name) +
                     f"<h4>3. Chapter readiness check</h4><p>{esc(task)}</p>"
                     "<h4>4. Linked notes</h4><ul><li><a href='#English'>English explained guidance in the original analysis</a></li>"
                     "<li><a href='#what-English'>Detailed topic-by-topic and task-by-task notes</a></li>"
                     "<li><a href='phase2_english_analysis.pdf'>Existing English analysis PDF</a></li></ul>"
                     "<p>No separate supplied English source-notes folder is present. The links above point to authored analysis/guidance, not an invented complete English textbook.</p></div>")
        all_rows.append(dict(subject="English", chapter_number=i, title=name,
                             static=[t["demand"] for t in static_tasks],
                             current=[t["demand"] for t in other_tasks], tasks=tasks,
                             coverage_static=static.split(";"), coverage_current=current.split(";"),
                             task=task))
    parts.append("</article></section>")
    if used_groups != set(task_groups):
        raise ValueError(f"Unused specific topic groups: {set(task_groups) - used_groups}")
    (output / "phase2_chapter_study_roadmap.json").write_text(json.dumps(all_rows, indent=2), encoding="utf-8")
    total_tasks = sum(len(row["tasks"]) for row in all_rows)
    print(f"Specific study tasks: {total_tasks}; complete AI prompts: {total_tasks}")
    print("Chapter roadmap:", dict((s, sum(r["subject"] == s for r in all_rows))
                                   for s in ("ESI", "Finance", "Management", "English")))
    return "".join(parts)
