"""Detailed, paraphrased study-demand inventories for the Phase II HTML report.

Regenerate with: python PYP\\analysis\\build_phase2_analysis.py --html-only
Historical references identify demands, not verified answer keys or future forecasts.
"""

import csv
import html
import json
from collections import Counter


# Group | named item | year:O/D question references | observed demand | study scope | retrieval/application task
ESI = """
Reports|OECD Economic Outlook, March 2021 interim update|2021:O1-3|Identify report/publisher; pandemic support finding; India's growth projection.|Record edition/date, publisher, forecast year, revision direction and policy rationale. Separate projected growth from realised growth and identify the denominator/reference period.|Make a report card with one projection, one finding and its economic explanation; update the edition rather than memorising the old forecast.
Reports|Economic Survey 2020-21, 2023-24 and 2024-25|2021:O19;2024:O9-12;2025:O14|Recovery explanation; Survey identification; agricultural production/growth; non-farm job requirement; MSME contribution and formalisation.|Study sectoral trends, growth drivers, employment estimates, agriculture, MSMEs and risks. Preserve financial year, averaging period, units, estimate/forecast status and source table.|Explain how a strong GDP number can coexist with employment problems; build a year-labelled sector indicator table.
Reports|World Bank Human Capital Index / Human Capital Project|2022:O15-17|India rank/score; index dimensions; project membership count.|Know publisher, index versus project, survival/health/education dimensions, interpretation of score, country coverage and edition-specific rank. Rank, score and project membership are different facts.|Explain why improved income alone does not guarantee better human-capital outcomes.
Reports|IMF World Economic Outlook (WEO)|2023:O9-11;2024:O13|Report identification, advanced-economy/global growth forecasts and publication/database cycle.|Know IMF versus World Bank/OECD publications; release/update dates; country/group forecast; year and revision; inflation/growth risks. Distinguish forecast vintage from forecast horizon.|Compare two vintages without mixing years or presenting a forecast as an actual outcome.
Reports|RBI Financial Stability Report, December 2021|2022:D3|Discuss financial resilience, pandemic challenges and reforms with a specific FSR reference.|Study bank/NBFC asset quality, profitability, capital/liquidity buffers, stress tests, macro-financial risks and interconnectedness. Separate baseline projections from stress scenarios and system aggregates from individual institutions.|Explain shock -> exposure -> transmission -> buffer -> policy response; use current FSR evidence in a separate dated column.
Reports|UNDP Gender Equality Strategy 2022-25 and Gender Social Norms Index|2023:D1|Use a strategy/index to discuss gender sensitisation and social norms.|Separate the strategy's actions from an index's measurement. Study norms, discriminatory attitudes, agency, institutions, education, work and political participation; connect each to a feasible intervention.|Write a 15-mark outline: diagnosis, mechanisms, sensitisation measures, implementation limits and evidence.
Reports|World Development Report 2023: migration|2023:D2|Explain migration policy and report recommendations.|Know publisher, edition/theme, migrants versus refugees, origin/destination effects, skills matching, rights, remittances and policy coordination. Read the report's actual framework before quoting it.|Construct an origin-country versus destination-country effects table and a balanced policy answer.
Reports|RBI Report on Currency and Finance: climate-focused report|2023:D3|Climate's macroeconomic effects and global cooperation.|Study physical/transition risks, output/productivity, food inflation, fiscal pressures, financial stability and adaptation/mitigation finance. The demand names the report; verify exact edition/title from the report before citing data.|Draw climate shock -> output/prices/public finances/bank risk; add three accurately explained cooperation mechanisms.
Reports|WEF Global Gender Gap Report and Alliance for Global Good: Gender Equity and Equality|2024:O1-4|Alliance venue/partners; reason for ranking change; report publisher.|Separate report indicators from alliance membership. Study four gender-gap dimensions, rank versus score, edition changes and initiative partners. A launch venue is not an index component.|Make two cards: measurement/report and action/alliance; do not merge their facts.
Reports|World Development Report 2024: middle-income transition|2024:O5-8|Director, development strategy, transitions to high income and India-specific findings.|Study middle-income trap, investment/infusion/innovation, firm dynamism, women's participation, income classification and comparative productivity. Separate useful policy mechanisms from incidental edition metadata.|Explain why investment alone may cease to be sufficient; make a strategy-stage comparison.
Reports|WEF Global Risks Report|2024:O16|Identify long-term global risks.|Record publisher, survey basis, short versus long horizon, risk categories and changing rankings. Do not mix perceived risk rankings with measured probability or realised damage.|Compare economic, environmental, technological and geopolitical risks over the stated horizons.
Reports|SDG midline assessment published in a journal|2024:O17-18|Number of lagging indicators and publication carrying the assessment.|The supplied demand concerns a journal study, not automatically a UN SDG report. Verify title/authors/publication, indicator set, district coverage, deadline and assessment method before quoting figures.|Create a study-specific card; distinguish this assessment from the Sustainable Development Report and national SDG indices.
Reports|World Development Report: welfare-quality reference|2025:D1|Discuss quality of welfare with a WDR reference.|The reconstructed wording does not reliably establish an edition or precise chapter. Study service quality, delivery capacity, targeting, adequacy, accountability and outcome measurement; authenticate the cited report before attributing recommendations.|Outline welfare access -> quality -> outcomes, and mark the report-edition field unresolved rather than inventing it.
Reports|UN Women/UNDESA Gender Snapshot 2025 and Beijing+30 Action Agenda|2025:D2|Discuss six priority pillars in the context of gender equality and the 2030 deadline.|Keep the monitoring report, Beijing Declaration anniversary and action agenda distinct. Verify the six official pillars; attach barriers, implementation steps and measurable outcomes to each.|Build six pillar/action/indicator rows from the actual publication, then practise an integrated 15-mark answer.
Reports|Sustainable Development Report: environment-poverty-growth linkage|2025:D3|Use the report/ranking context to discuss sustainable development.|Study SDG progress, rank versus score, environmental constraints, poverty traps, distributional costs and policy complementarities. Treat the recalled rank as a historical question cue, not a current verified statistic.|Explain both a conflict and a synergy among growth, poverty reduction and environmental protection.
Reports|FAO Global Forest Resources Assessment 2025|2025:O19,O22|Report features, forest categories, extent and geographic concentration.|Know publisher, national-data basis, definitions of forest/planted/naturally regenerating categories, area versus percentage, biome/domain and assessment year. Avoid equating tree cover with forest under every definition.|Make a definition/data/method card and explain why forest area and forest quality can move differently.
Schemes: urban/basic welfare|AMRUT, JNNURM and related urban-renewal distinctions|2021:O6-10|SAAP, objectives, cost sharing, scheme succession and extension.|Know ministry, service focus, city coverage, state action plans, funding pattern, reform incentives and phase/version. Distinguish drinking water/sewerage/green spaces from heritage conservation, housing and smart-city objectives.|Compare AMRUT with housing and Smart Cities; solve objective-matching and funding cases.
Schemes: agriculture|PM-KISAN and its mobile application|2021:O11-13;2023:O28;2024:O29|Disbursement, annual benefit, exclusions, face-authentication app functions and beneficiary cases.|Study farmer-family/landholder definition, exclusions, benefit/installments, DBT, land/Aadhaar/bank/e-KYC checks and grievance process. Keep historical small/marginal wording separate from applicable revised eligibility.|Decide eligibility for a government employee, private worker and taxpaying professional; explain each exclusion.
Schemes: education|STARS: Strengthening Teaching-Learning and Results for States|2021:O21|Financing institution and funding amount.|Know project purpose, school-education outcomes, implementing ministry/states, external lender, financing instrument and results-based features. Date funding figures and distinguish commitment from utilisation.|Write an inputs -> teaching/assessment -> learning outcomes chain, with a dated financing card.
Schemes: food security|One Nation One Ration Card, NFSA and Food Security Allowance Rules|2021:O22;2022:O1-4|Portability, technology, legal framework, allowance rules, state coverage and award.|Study entitlement versus portability, beneficiary identification, Aadhaar/e-PoS, inter/intra-state use, grievance/allowance provisions and migrant access. Separate underlying Act from implementing rules.|Explain how portability helps migrants and why authentication failure still creates exclusion risk.
Schemes: financial savings|Sovereign Gold Bonds (SGB)|2021:O24;2022:O21;2023:O24;2024:O30|Investor eligibility, discount, collateral, interest, tenure, limits and premature redemption cases.|Study issuing authority, eligible persons/entities, annual purchase limits, issue versus secondary purchase, coupon, market-price risk and redemption windows. Do not assume fresh issuance continues merely because old bonds exist.|Make SGB versus physical gold versus gold fund comparison; apply the correct historical rule to an investment case.
Schemes: agriculture portals|Kisan Suvidha|2021:O25|Identify a farmer-information application from services.|Know owner, weather/market/advisory services, intended user and distinction from PM-KISAN's benefit-management app.|Match a farmer's information need to the correct portal, not simply the word Kisan.
Schemes: health portals|e-Sanjeevani, NIKSHAY, Kilkari and ANMOL|2021:O26|Recognise public-health applications and their purpose.|Map each application to service, target user, administering health system and delivery channel: teleconsultation, disease management, maternal messaging or frontline-worker support. Verify current scope before adding details.|Make application -> user -> service -> ministry cards; distinguish citizen-facing and health-worker-facing tools.
Schemes: enterprise/property|PM SVANidhi, SVAMITVA and EPF-support matching|2021:O28|Match working capital, property mapping and employment-contribution support to schemes.|Study beneficiary, instrument and delivery mechanism separately. Vendor credit is not land-title mapping; pandemic employment support is not a permanent entitlement by default.|Use a three-column beneficiary/problem/instrument table; verify which named historical EPF-support provision the recalled item intends.
Schemes: food processing|Operation Greens and PM Kisan SAMPADA distinctions|2021:O29|Objectives, coverage and relation to food-processing support.|Know value-chain stabilisation, perishables, processing/storage/logistics, implementing ministry and changes in commodity coverage. Do not infer the correct nesting of programmes from answer options.|Explain price volatility -> supply-chain intervention -> farmer/consumer effects.
Schemes: social justice|SMILE and Garima Greh, including PM-DAKSH linkage|2022:O5-7|Shelter name, components, education/livelihood provision and allocation.|Know distinct target groups, umbrella/sub-scheme relationship, shelter and rehabilitation, skilling, scholarships, implementing ministry and dated funding horizon.|Build beneficiary -> service -> delivery agency matrix; distinguish umbrella scheme from a component.
Schemes: caste inclusion|PM Adarsh Gram Yojana / PM-AJAY|2022:O18-20|Pilot states, monitorable indicators and implementation award.|Study SC-majority village eligibility, convergence/gap filling, indicator domains, merger/renaming, implementing ministry and dated pilot/award metadata.|Explain why infrastructure saturation and social inclusion require different outcome indicators.
Schemes: pensions|PM Kisan Maandhan Yojana|2022:O22;2024:O23|Age, landholding and other-pension exclusions in eligibility cases.|Study contributory pension, joining/exit age, small/marginal farmer criteria, contribution matching, exclusions and distinction from PM-KISAN income support.|Apply age, landholding and existing-pension tests separately; show why PM-KISAN and PM-KMY are not interchangeable.
Schemes: mixed beneficiary matching|Rashtriya Gokul Mission, Stand-Up India and One Stop Centre|2022:O23|Match livestock improvement, entrepreneurship and support for women.|Know each scheme's beneficiary/problem/instrument. Do not treat every woman or every entrepreneur as eligible for all women-focused programmes.|Create three sharply different case cards, including one ineligible or wrongly matched case per programme.
Schemes: land acquisition portal|Bhoomi Rashi|2022:O24|Compensation transfer, PFMS integration and implementing-agency use.|Study land-acquisition workflow, responsible ministry/agency, compensation delivery, transparency and digital integration.|Contrast acquisition compensation with property-survey/title mapping under SVAMITVA.
Schemes: cooperatives|Sahakar Mitra|2022:O25|Identify a cooperative-sector internship programme.|Know sponsoring institution, target trainees, internship versus enterprise-finance support, learning objectives and current eligibility.|Compare Sahakar Mitra with cooperative credit/startup programmes without assuming similar names mean similar benefits.
Schemes: fisheries|PM Matsya Sampada Yojana|2022:O26|Production, income, infrastructure and beneficiary objectives.|Study fisheries value chain, production/productivity, post-harvest losses, formalisation, beneficiary categories, central/centrally sponsored components and applicable funding pattern.|Map hatchery -> production -> cold chain -> market; identify which intervention solves which bottleneck.
Schemes: pensions|PM Vaya Vandana Yojana|2022:O27|Tenure, investment limit and pension frequency.|Study insurer/administrator, purchase versus pension amount, term, payment options, joining/closure dates and applicable historical limits. A past scheme's rules do not prove it remains open.|Compare pension purchase product, contributory pension and savings account; label the rule date.
Schemes: education|PM eVIDYA|2022:O28|Digital, broadcast and accessible-learning components.|Study multi-mode delivery, television/radio/digital channels, disability access, connectivity constraints and school-education outcomes.|Explain why a multi-channel education programme is not the same as a single online portal.
Schemes: enterprise inclusion|Stand-Up India|2022:O29;2023:O22|Borrower eligibility, greenfield project, loan terms and default exclusions.|Study SC/ST/women ownership conditions, eligible activity, new enterprise, bank branch delivery, loan range, repayment/moratorium and updated validity. Keep it separate from MUDRA.|Decide eligibility for a woman starting a first venture, a repeat project and a wilful defaulter.
Schemes: child protection|PM CARES for Children|2022:O30|Pandemic-related beneficiary conditions, registration and assistance.|Know qualifying parental loss/date window, education/health/financial components, administrator and application process; verify historical scheme limits rather than accepting the options.|Create beneficiary timeline and distinguish immediate support from benefits at later ages.
Schemes: environment|Mission LiFE|2023:O1-4|Initiative name, categories, phases and announcement event.|Study demand/supply/policy change, lifestyle action categories, launch/announcement distinction and behaviour-to-system pathway.|Connect a household behaviour to firm response and policy support; distinguish individual action from economy-wide decarbonisation.
Schemes: tribal inclusion|PVTG development mission, PVTG criteria and geography|2023:O13-16|Budget mission, Saptarishi priority, state distribution and identification criteria.|Study PVTG versus Scheduled Tribe, vulnerability criteria, basic-service saturation, relevant Budget priority, funding period and later programme naming/version. Do not retroactively replace the name asked with a later name.|Make criteria -> needs -> service intervention table and distinguish static identification from current mission details.
Schemes: labour portals|e-Shram/NDUW and UMANG integration|2023:O17-20|Registrations, integration partner, accessible services and state targets.|Know unorganised-worker database purpose, registration versus actual social-security receipt, age/eligibility, portability, platform integration and snapshot dates.|Explain why registration totals do not establish insurance or pension coverage; keep platform and service-provider roles separate.
Schemes: health insurance|Ayushman Bharat PM-JAY|2023:O21|Household/occupation eligibility and family coverage case.|Study beneficiary basis, family coverage, cashless treatment, covered care, portability, exclusions and distinction from primary-care components of Ayushman Bharat.|Test whether family size alone excludes an eligible household; justify using scheme rules rather than intuition.
Schemes: girl-child savings|Sukanya Samriddhi Yojana|2023:O23|Opening age, deposits and transfer conditions.|Study guardian/account holder, age window, number of accounts, annual deposit bounds, maturity/withdrawal and rate revision. Never infer rule correctness from an incorrect case statement.|Compare account-opening deadline, deposit period and maturity date on a timeline.
Schemes: scholarships|Prime Minister's Scholarship Scheme (PMSS)|2023:O25|Widow/child eligibility and qualifying educational marks.|Verify which PMSS and administering department the source means; similarly named scholarship programmes differ. Study beneficiary relationship, course eligibility, marks and selection conditions.|Resolve programme identity first, then apply education/marks conditions; do not invent a universal PMSS eligibility rule.
Schemes: women protection|Swadhar Greh|2023:O26|Woman's age/stay and accompanying-child conditions.|Study target women, shelter/services, age/child provisions and subsequent convergence/renaming. Answer a historical case with the historical rules; prepare current successor separately.|Draw mother/child eligibility and duration decision tree with date-labelled rules.
Schemes: medicines|Pradhan Mantri Bhartiya Janaushadhi Pariyojana|2023:O27|Store operator margin, incentives and special assistance.|Study implementing body, generic-drug access, Kendra operator eligibility, margin versus incentive, ceilings and quality/procurement safeguards.|Separate medicine affordability for patients from financial support for store operators.
Schemes: microcredit|Pradhan Mantri MUDRA Yojana|2023:O29|New/existing enterprises, charges, insurance and commercial-vehicle use.|Study loan categories and current ceilings, eligible non-farm activities, lender/guarantee roles, collateral conditions and business use. Historical limits are not automatically current limits.|Classify a working-capital, vehicle and enterprise-expansion case; compare with Stand-Up India.
Schemes: women's savings|Mahila Samman Savings Certificate|2023:O30|Closure, interest penalty and partial withdrawal rules.|Study opening window, eligible depositor/guardian, investment ceiling, tenor, interest treatment, withdrawal and early closure. Verify whether new accounts remain available.|Build opening -> withdrawal -> maturity timeline and distinguish early closure from partial withdrawal.
Schemes: agriculture sustainability|PM-PRANAM and Agriculture Infrastructure Fund portal|2024:O19-20|Portal development partner; fertiliser-subsidy savings and grant design.|Keep the AIF interest-subvention workflow separate from PM-PRANAM incentives. Study chemical-fertiliser baseline, savings calculation, grant utilisation, agency roles and verification.|Explain fiscal incentive -> state behaviour -> farm practice -> environmental outcome, including perverse incentives.
Schemes: employment services|National Career Service|2024:O21|Jobseekers, overseas jobs, apprenticeships and ex-servicemen services.|Study employment matching, counselling, service beneficiaries, portal services and distinction from a job guarantee or a cash-transfer scheme.|Match three user needs to actual NCS services; do not promise employment merely from registration.
Schemes: child protection|Mission Vatsalya|2024:O22|Beneficiaries, sponsorship/support and adoption-related cases.|Study child protection continuum, family-based versus institutional care, sponsorship/foster care, implementing bodies and relationship with adoption law/CARA.|Distinguish support to a vulnerable child from an adoption incentive to any married couple.
Schemes: disaster/medical relief|Prime Minister's National Relief Fund|2024:O25|Disaster, accident and medical-assistance eligibility.|Study purpose, eligible distress categories, assistance process and distinction from PM CARES and statutory disaster funds.|Create event/person/assistance cases without assuming every medical expense qualifies automatically.
Schemes: farm infrastructure|Agriculture Infrastructure Fund (AIF)|2024:O26|Eligible post-harvest/community-farming projects and applicants.|Study debt financing, eligible assets/entities, interest subvention, credit guarantee, project limits and operational period. Distinguish primary processing/infrastructure from every food-processing activity.|Apply rules to a mill, pickle business, farmer and mushroom project; identify the asset and activity before deciding.
Schemes: pensions|National Pension System (NPS)|2024:O28;2025:O5|Citizenship/status eligibility, contributions, withdrawals and fund-manager changes.|Study regulator, subscriber models, age bands, Tier I/II, partial/early/normal exit, annuity/lump sum and permissible changes. Date the rules; separate resident, NRI, OCI and PIO categories.|Build subscriber-status and exit-event decision trees; calculate payout only under the applicable dated rules.
Schemes: accident insurance|Pradhan Mantri Suraksha Bima Yojana|2025:O1|Accident benefit, disability category and joining/coverage age cases.|Study insurer/bank enrolment, premium, annual renewal, death versus partial/total disability and exclusions; compare with life insurance.|Decide three cases by covered event, age and benefit category, not by poverty status alone.
Schemes: savings|Public Provident Fund|2025:O2|Loans, withdrawal, minimum deposit and discontinued-account consequences.|Study eligible account holder, deposits, lock-in/extension, loan calculation base, partial withdrawals, reactivation and interest revision. Separate account discontinuation from forfeiture.|Draw the permitted loan/withdrawal/maturity timeline and explain why PPF is not NPS.
Schemes: skill infrastructure|Pradhan Mantri Kaushal Kendra|2025:O3|Training provider's eligibility, infrastructure, history and financial conditions.|Study provider versus trainee eligibility, centre norms, NSQF alignment, financing/implementation agency and quality assurance.|Evaluate a proposed training centre using provider requirements; do not apply student rules to an organisation.
Schemes: energy|PM Surya Ghar: Muft Bijli Yojana|2025:O4|Rooftop capacity/subsidy, upgrade and ownership cases.|Study eligible household/roof, capacity-linked assistance, approved installation/net metering, application workflow and current subsidy schedule. Distinguish subsidy from guaranteed zero electricity bill.|Calculate assistance from an authenticated schedule and assess an upgrade/tenant case.
Schemes: adoption|CARA adoption rules referenced as 2025|2025:O6|Single-parent sex, parental age and child's age eligibility.|Study adoption authority, single/couple eligibility, composite age, child-age bands and restrictions; authenticate the legal instrument/year rather than assuming the recalled label is exact.|Create parent-sex/age/child-age case matrix and distinguish adoption from sponsorship/foster care.
Schemes: education inclusion|SHRESHTA|2025:O7|Eligible social group, income, entry class and education support.|Study intended SC students, residential schooling, selection/entry stages, income threshold and support components. Verify limits from the dated guidelines.|Apply social group, income and entry-class filters in sequence.
Schemes: ageing|Atal Vayo Abhyuday Yojana|2025:O8|Senior support, startup assistance, old-age-home standards and grants.|Study umbrella components, senior-citizen services, implementing ministry, institutional standards and distinction between grants and equity support.|Map each recalled statement to the relevant component before testing amount/eligibility.
Schemes: workers' pensions|PM Shram Yogi Maandhan|2025:O9|Income, entry age and membership of other pension arrangements.|Study unorganised-worker criteria, contributory structure, matching, pension age, exclusions and exit conditions.|Compare PM-SYM, PM-KMY, APY and NPS using beneficiary/entry/contribution/benefit columns.
Schemes: farm development|PM Dhan-Dhaanya Krishi Yojana and Aspirational Districts Programme|2025:O15-18|Allocation, model programme, district-plan review and indicator count.|Study district selection, convergence, productivity/diversification/irrigation/credit, governance and monitoring. Keep a Budget announcement, Cabinet approval and implementation dates distinct.|Create district problem -> converged intervention -> measurable outcome table; verify programme indicator counts by edition.
Schemes: environment regulation|Green Credit Programme and Environment Audit Rules 2025|2025:O20-21|Programme objectives and auditor certification/assignment.|Separate voluntary incentives, carbon credits, mandatory environmental clearance and audit compliance. Study responsible authority, eligible activities, measurement, independence and random allocation if confirmed in rules.|Explain why a green credit is not a substitute for statutory clearance; build an auditor independence case.
Schemes: urban housing|PMAY-U 2.0 and Angikaar 2025 outreach|2025:O23-26|Campaign name/theme, four housing verticals and special-focus groups.|Study beneficiary/income/ownership conditions, construction/partnership/rental/interest support, central assistance, campaign versus core scheme and convergence with rooftop solar.|Compare the four verticals by beneficiary, tenure, delivery and subsidy; distinguish campaign awareness from entitlement.
Policies/institutions|RBI liquidity framework, LTRO and monetary transmission|2021:O14-17;2022:D5;2023:D5;2025:D5|Identify operations, rate linkage, liquidity signals, reserve cycle, instruments and a dated policy assessment.|Study policy rate/corridor, operating target, CRR/SLR, repo/reverse repo, variable-rate operations, OMO, standing facilities and transmission. Separate liquidity quantity, policy stance and rate action; update changes after the historical paper.|Draw surplus/deficit balance-sheet flows; explain eight distinct instruments and analyse growth/inflation/credit trade-offs.
Policies/institutions|WTO, IMF, globalisation and trade/investment|2021:O4,O20,O23,D3;2022:O11-14;2023:O5-8,O12;2024:O27|Trade benefits, WTO origins/body/head, IMF missions, TRIPS waiver, ECTA, deemed exports and post-crisis globalisation.|Study GATT/WTO, institutions versus reports, tariffs/rules of origin, goods/services, deemed-export rules, trade diversion, technology transfer and global value chains. Incumbents/agreement counts are dated; founding history is not.|Compare liberalisation benefits/costs and evaluate an FTA or vaccine-IP waiver through multiple stakeholders.
Policies/institutions|Raisina Dialogue|2022:O8-10|Event identity, side-event locations, guests and themes.|Study organiser, purpose, annual theme and participants; identify this as geopolitics/general current affairs rather than static economics theory.|Make a compact dated event card; do not let incidental event trivia displace core syllabus preparation.
Policies/institutions|Union Budget, 15th Finance Commission and disinvestment|2021:O27,D1,D4;2023:O14;2024:D2|Startup changes, horizontal/vertical transfers, disinvestment rationale and digital initiatives.|Study fiscal federalism, devolution versus grants, tax/non-tax receipts, capital/revenue, strategic sale versus minority sale and policy channels. Identify the specific Budget/Commission period before citing recommendations.|Build measure -> mechanism -> beneficiaries -> fiscal cost -> implementation risk; compare vertical and horizontal distribution.
Policies/institutions|Industrial/labour reform, startups and MSME formalisation|2021:O30;2022:D2;2023:D6;2024:O24,D5;2025:O11-14|Labour-code objectives, post-1991 reforms, startup recognition, corridors, startup constraints and Udyam-related formalisation.|Study registration versus regulatory authority, enterprise thresholds, formalisation incentives, logistics/cluster effects, labour protections and implementation status. Reconstructed 2025 MSME questions have an unrelated preceding passage.|Explain how credit, compliance, skills and infrastructure interact; distinguish Udyam, Udyam Assist and TReDS.
Policies/institutions|SEBI SIF framework and revised equity-derivatives/MWPL rules|2025:O10,O27-30|SIF entry/short exposure/redemption/accreditation; position limits, ban trigger, surveillance and pre-open measures.|Study regulator, product purpose, eligible investor, minimum ticket, exposure limits, free-float versus total market cap, position-limit categories and effective dates. Do not transfer a threshold from one instrument to another.|Use a dated old-rule/new-rule/rationale table and calculate a position-limit case from authenticated inputs.
Concepts/descriptive|Poverty, welfare, jobs and rural enterprise|2021:D2;2022:D4;2023:D4,D6;2024:D1|Measurement merits/limits, safety nets, enterprise constraints, programme design and youth jobs.|Study monetary/multidimensional poverty, incidence/intensity, LFPR/WPR/unemployment, informality, skills mismatch, credit/markets and policy evaluation. For the generic three-scheme prompt, candidate-selected examples are not historically named schemes.|Write a measure -> limitation -> intervention -> outcome answer; compare three verified current programmes without claiming they were named in the paper.
Concepts/descriptive|Social structure, demography, gender and multiculturalism|2021:D5;2022:D1;2023:O15-16;2024:D4;2025:D6|Demographic transition, protective discrimination, PVTG identification, women-led development and multiculturalism.|Study caste/gender disadvantage, equality versus equity, affirmative action, demographic dividend/ageing, agency, unpaid care, pluralism and social cohesion. Link institutions and norms to outcomes rather than listing schemes.|Prepare mechanism-based answers with one counterargument and practical safeguards; compare diversity with inclusion.
Concepts/descriptive|Climate, SDGs, polycrisis and sustainable growth|2021:O18,D6;2024:O14-15,D3;2025:D3|SDG institution, interconnected crises, climate commitments and growth-environment tensions.|Study mitigation/adaptation, absolute emissions versus intensity, physical/transition risk, externalities, distributional effects, resource efficiency and just transition. Keep report-specific facts separate from stable causal concepts.|Draw climate-poverty-growth feedback loops and explain both policy trade-offs and co-benefits.
Concepts/descriptive|Financial resilience, NBFCs and AI banking|2022:D3,D6;2024:D6|FSR-linked resilience/pandemic reform, NBFC-bank differences and AI benefits/risks.|Study credit/liquidity/market/operational risk, capital buffers, interconnections, depositor protection distinctions, AI use cases, bias, privacy, model risk and human accountability.|Compare banks/NBFCs, then write a shock -> transmission -> buffer -> regulatory response chain.
Concepts/descriptive|Urbanisation, Smart Cities and inclusive development|2025:D4|Urban-growth trends and Smart Cities with a Visakhapatnam reference.|Study municipal capacity, housing, water/sanitation, transport, livelihoods, digital access, resilience and project outcomes. Authenticate the city example; do not invent local projects or statistics.|Build a city case with one verified intervention, beneficiary/outcome evidence and an inclusion limitation.
Uncertain source|Population/environment country item|2021:O5|A country-level claim whose recreated context is insufficient.|Preserve as an unresolved evidence item; do not invent a report finding or use it to create a strong preparation priority.|Identify the missing context and practise evaluating the general population-resource-environment relationship only.
"""

FM = """
Finance institutions|RBI, SEBI, NPCI, NSDL/CDSL, CCIL and market responsibilities|2021:O4-6,O14-16;2024:O7;2025:O2-4|NETC/FASTag, regulators, depositories, payment institutions, NDS-OM and transaction infrastructure.|Study regulator versus operator versus clearing corporation versus depository; payment versus securities markets; order matching versus clearing/settlement. Some recollections use imprecise institutional labels, so do not adopt their wording as fact.|Draw trade/payment lifecycles and assign each institution one correct role.
Finance institutions|DFIs: SIDBI, NHB, NABARD, RRBs, EXIM and NaBFID|2021:D4;2023:O21;2025:O1-2|Mandates, infrastructure financing and regulator.|Study target sector, refinance/direct lending/development roles, ownership versus regulation and sources/tenor of funds. Separate historical formation facts from current mandates.|Compare each institution by borrower, instrument and market failure; explain why long-term infrastructure needs a DFI.
Finance inclusion|Small Finance Banks|2024:O9-12|Identify the institution, underserved customer groups, financial access and literacy role.|Study SFB versus payments bank versus RRB, deposit/lending permission, target segment, inclusion purpose and prudential obligations. Passage-based service descriptions are not necessarily new policy.|Compare bank types by permissible activity, customer and business-model risk.
Finance investment vehicles|Infrastructure Investment Trusts (InvITs)|2025:O5-6|Public issue allocation and anchor-investor allocation proportions.|Study trust/sponsor/manager/trustee, infrastructure assets, cash distributions, listing, eligible investors and allocation denominators. Verify current SEBI provisions; a percentage of the institutional portion is not a percentage of the entire issue.|Draw investor -> trust -> infrastructure -> cash-distribution flow and calculate allocation from the correct base.
Finance markets/rules|ASBA, UPI applications and debt public issues|2021:O7-8;2024:O5-8|IPO route, eligible banks, application threshold, method, regulator and commencement date.|Study blocked versus debited funds, SCSBs/intermediaries, IPO versus debt issue, retail thresholds and circular effective date. Do not mix public issue, exchange trading and settlement timelines.|Draw application -> blocking -> allotment -> debit/unblock, then attach the correct dated circular.
Finance markets/rules|Hybrid Annuity Model and PPP|2021:O9-11|Model identification, construction/annuity sharing and infrastructure use.|Study EPC/BOT/HAM, asset ownership, financing, construction risk, traffic risk, government contribution and lifecycle maintenance.|Compare who finances, builds, operates, bears demand risk and pays under each model.
Finance markets/rules|Revenue expenditure, non-tax revenue, Budget and Contingency Fund|2021:O21,D1;2023:O29;2025:O23,D4|Revenue/capital distinctions, non-tax receipts, Budget announcements, fund corpus and policy balance.|Study receipts/expenditure, deficits, debt versus non-debt capital receipts, voted spending versus contingency provision and monetary-fiscal coordination. Date fund corpus and distinguish a current Budget demand from a conceptual Budget demand.|Classify interest, subsidy, lending and asset creation; explain growth/inflation effects without equating every outlay with productive capital.
Finance markets/rules|FDI in banking, FPI bond limits and LRS|2021:O25;2022:O27;2023:O27|Sector/individual limits, recent corporate-bond limit and outward remittance ceiling.|Study automatic/approval routes, ownership versus voting/shareholding limits, FDI/FPI, resident outward remittance and eligible transactions; date every limit.|Maintain separate sectoral cap, investor cap and transaction cap columns; apply a resident-remittance case.
Finance numericals|Valuation ratios, ROA and accounting relationships|2021:O26;2023:O22;2025:O7-9|P/E comparison, ROA and debt/net-worth/turnover/gross-profit calculations.|Study numerator/denominator, net worth, assets/liabilities, book versus market value, EPS, P/E, sales, gross profit and units. State any accounting assumption; reserve terms and balance-sheet identities must be interpreted consistently.|Derive the requested value stepwise, show formula and units, and check whether an omitted assumption makes the case ambiguous.
Finance markets/rules|Commercial paper and negotiable instruments|2022:O8-11;2023:O30|CP tenor/denomination/form and bill-of-exchange case.|Study secured/unsecured, issuer/investor, discount versus coupon, maturity, denomination, promissory note versus bill, parties and acceptance. Verify applicable CP directions rather than treating historical thresholds as permanent.|Compare CP, certificate of deposit, Treasury bill and bill of exchange; identify drawer/drawee/payee in a case.
Finance regulation|Bank outsourcing|2022:O12-14|Outsourceable activities and retained core/KYC responsibilities.|Study service-provider risk, non-delegable management/accountability, due diligence, confidentiality, business continuity, monitoring and exit. Outsourcing work does not outsource regulatory responsibility.|Classify a proposed outsourced activity and specify the responsibility the bank must retain.
Finance current/policy|RBI regulatory sandbox: cross-border payments cohort|2021:O20|Cohort/theme and controlled testing mechanism.|Study sandbox entry, live testing boundaries, safeguards, regulatory relief versus licence, cohort themes and exit; distinguish sandbox from a permanent product approval.|Explain innovation -> limited test -> evidence -> decision and why participation is not blanket regulatory endorsement.
Finance current/policy|Payments Infrastructure Development Fund (PIDF)|2022:O21|Annual touchpoint deployment target.|Study fund objective, geography, physical/digital acceptance infrastructure, subsidy design, administrator and dated targets/extension.|Distinguish number of touchpoints from transaction value or unique users; explain last-mile economics.
Finance identifiers|Legal Entity Identifier (LEI)|2022:O22|Recognise the identifier and format.|Study legal-entity identification, reporting/risk aggregation purpose and distinction from BIC/SWIFT/IFSC. Verify threshold-based implementation separately.|Match entity, bank, branch and individual identifiers to the right transaction need.
Finance enterprise rules|MSME classification and Importer Exporter Code|2022:O24,O30|Investment/turnover thresholds and IEC applicability.|Study combined classification criteria, manufacturing/services treatment, revision dates, enterprise versus proprietor identity and trade authorisation requirements/exemptions.|Classify firms from investment and turnover jointly; separate IEC from GST and Udyam registration.
Finance inclusion/schemes|PMJDY, PMJJBY, PMSBY and Atal Pension Yojana|2023:O1-5|Identify scheme; insurance amount, entry age, pension and premium.|Study basic banking versus life versus accident insurance versus contributory pension; beneficiary/age, renewal, premium, event/benefit, exclusions and administrators. Date changed premiums and joining restrictions.|Build a four-scheme comparison and test a death, accident and retirement case.
Finance governance regulation|RBI bank-board governance directions|2023:O11-15|Governance concept, audit/risk committee composition/chair, quorum and expertise.|Study independent/non-executive/executive directors, board versus committee roles, fit-and-proper, conflicts, audit/risk oversight and applicability. Verify circular title/date because reconstructed preambles may be imprecise.|Create board/ACB/RMCB composition-quorum-chair matrix; keep current amendments in a separate column.
Finance alternatives|Forfaiting and alternative finance|2023:O28|Identify an alternative financing instrument.|Study receivables financing, recourse/non-recourse, maturity, discounting, export risk transfer and distinction from factoring and ordinary loans.|Trace seller, financier and debtor cash/risk flows; compare factoring with forfaiting.
Finance inclusion/schemes|RBI Retail Direct|2023:D3|Explain retail access to government securities.|Study eligible investor, RDG account, primary/secondary access, securities, settlement, interest-rate risk, liquidity and tax treatment from current rules.|Explain sovereign credit risk versus mark-to-market risk; compare a G-sec held to maturity and sold early.
Finance digital policy|ONDC|2023:D4|Explain open commerce and competition with platforms.|Study open network versus single marketplace, buyer/seller/logistics participants, interoperability, discoverability, onboarding, fees and grievance accountability.|Explain how network design could reduce entry barriers while recognising trust, fulfilment and network-effect challenges.
Finance digital policy|Pre-sanctioned credit lines on UPI|2023:D6|Explain inclusion benefits and policy change.|Study funding source versus payment interface, eligible institutions/users, consent, interest/fees, underwriting and over-indebtedness. Date permitted categories and limits.|Compare bank-account UPI, credit-card UPI and credit-line UPI without confusing transfer channel with the lender.
Finance current/policy|SM REIT framework|2024:O22|Regulatory investment/asset threshold demand.|Study trust structure, asset value versus investor ticket versus offer size, eligibility, ownership, distributions, leverage and disclosure. The recalled phrase investment limit is ambiguous; verify the exact rule being tested.|Write unit and object beside every threshold; never substitute an asset threshold for an individual's minimum investment.
Finance current/policy|Ways and Means Advances: second half FY2024-25|2024:O23|Dated government WMA limit.|Study temporary cash-flow mismatch, government borrower, RBI facility, tenure/rate, overdraft distinction and ceiling-setting period.|Contrast WMA with fiscal deficit financing and explain why a temporary liquidity need need not equal insolvency.
Finance current/policy|UPI Circle|2024:O28|Number of delegated secondary users.|Study primary/secondary user roles, full/partial delegation, consent/control, transaction/period limits and liability safeguards; date all limits.|Draw an authorised delegated-payment case and distinguish it from sharing credentials.
Finance current/policy|Debt issue timeline and bonus/corporate-action settlement|2024:O29;2025:O25|Reduced issue timeline and T+2 applicability.|Study issue closure, allotment, listing, record date and trading availability as distinct clocks. Confirm whether the circular is mandatory, optional or phased.|Make event -> T -> next milestone timeline; do not apply equity trade settlement to every corporate action.
Finance prudential rules|Basel III, capital/risk and NBFC CRAR|2021:D5;2024:O30|Basel pillars and risks covered in capital calculation.|Study capital quality, risk-weighted assets, minimum/buffer concepts, supervision, market discipline and applicability to banks versus NBFC categories. Do not import bank risk-weight rules wholesale into NBFC cases.|Explain capital versus liquidity buffers and a loss -> capital -> lending transmission chain.
Finance instruments|Derivatives, zero-coupon bonds, index futures and AT1 bonds|2024:D1,D5;2025:O29-30|Types, users/risks, AT1 loss absorption, zero-coupon return and index-futures mechanics.|Study forward/futures/options/swaps, hedger/speculator/arbitrageur, margin, settlement, basis/counterparty risk, discount yield and AT1 write-down/conversion/perpetuity. 2025 O29-30 are explicitly uncertain reconstructions.|Compare payoff/risk; explain why a bank AT1 instrument is not an ordinary deposit or a conventional fixed-maturity bond.
Finance investment|Value versus growth investing|2024:D6|Compare investment approaches.|Study price versus intrinsic value, earnings expectations, multiples, cash flows, discount-rate sensitivity, valuation risk and overlap. Cheap price alone is not value; fast growth alone is not a good investment.|Compare two hypothetical companies and identify assumptions supporting each valuation.
Finance history/concepts|Narasimham reforms, LAF, Phillips curve, inflation and JAM|2025:O15-17,O22,O24,O28|Historical committee/reform, liquidity tool, inflation-unemployment curve, CPI/WPI, cost-push and inclusion identifiers.|Study reform objectives, prudential/competition changes, direct versus indirect instruments, demand/cost shocks, short-run trade-offs/expectations, indices and JAM delivery. 2025 O28 is expressly uncertain.|Explain CPI rising while WPI falls without assuming the entire economy has one price level; contrast liquidity tool with fiscal tool.
Finance digital infrastructure|TReDS|2025:O18-20|Regulator, invoice discounting and settlement mechanism.|Study seller/buyer/financier, accepted invoice, bidding, without-recourse structure as applicable, settlement and default responsibility. Authenticate any recalled market-infrastructure label.|Draw invoice -> acceptance -> bidding -> early seller payment -> buyer repayment; compare with a collateral loan.
Finance descriptive policy|Capital-market development and RBI supervision|2025:D1,D5|Capital markets as growth engine, SEBI measures and RBI's regulatory/supervisory role.|Study savings mobilisation, price discovery, liquidity, investor protection, primary/secondary markets, intermediary conduct, prudential versus conduct oversight and risk-based supervision. Avoid attributing SEBI's entire remit to RBI.|Use objective -> regulatory tool -> transmission -> limitation; connect current measures only when verified.
Finance technology|Blockchain, AI and financial-sector ethics|2022:D3;2025:D6|Banking disruption and AI risks/new ethical dimensions.|Study distributed ledger/consensus versus ordinary database, settlement/trade finance, privacy/scalability/interoperability; AI bias, explainability, model/cyber/vendor risk, human accountability and governance.|Compare one useful application with a case where simpler technology is preferable; make benefit/risk/control rows.
Finance macro application|LTRO and India's response to the 2008 crisis|2022:D4-5|Liquidity-operation explanation and historical crisis response.|Study collateral, tenor, rate, bank lending channel, liquidity/solvency distinction and coordinated monetary/fiscal measures. Historical crisis response is not a request for today's policy-rate trivia.|Trace policy -> bank funding -> credit -> demand and identify a transmission constraint.
Management foundations|Organisational behaviour, psychology/sociology, diversity and teams|2021:O2-3,O30;2022:O1-3|Discipline/levels, heterogeneous workforce and employee retention.|Study individual/group/organisation levels, attitudes, commitment, turnover, team roles, diversity versus inclusion and contributions of behavioural disciplines.|Diagnose a team/individual/system problem at the correct level before selecting a remedy.
Management justice/perception|Distributive justice, stereotyping and Johari Window|2021:O1,O22,O24;2024:O24|Input-output fairness, group-based perceptual error and hidden quadrant.|Study distributive/procedural/interactional justice, stereotype versus halo, open/blind/hidden/unknown self-awareness and feedback/disclosure.|Classify three fairness cases and draw how feedback/disclosure changes Johari quadrants.
Management motivation|Maslow, McClelland, Herzberg, ERG, X/Y, Vroom and attitudes|2021:O23,D6;2022:O15-17;2023:O6-8;2024:O21;2025:O27|Process/content theories, needs, hygiene, growth, managerial assumptions, outcome value and reinforcement.|Study each theory's mechanism, assumptions and workplace application; expectancy/instrumentality/valence; positive/negative reinforcement versus punishment; attitude-performance link. A recalled theorist label can be wrong: verify before learning it.|Use theory -> diagnostic clue -> intervention -> limitation; explain why removing dissatisfaction need not create motivation.
Management change|Lewin, resistance, merger transition and systematic change|2021:O12-13,O29;2022:O25,D2;2024:O27;2025:D2|Change/stages, refreezing, transition and resistance remedies.|Study individual/structural resistance, uncertainty, interests, communication, participation, training, sequencing, reinforcement and feedback. Keep model steps linked to actual managerial actions.|Write a bank-merger case through diagnosis -> implementation -> institutionalisation with measurable checks.
Management communication|Process, semantic/personal barriers, channels, networks and nonverbal signals|2021:O17,O27;2022:O18-20,O23,O29,D1;2023:O16-18;2024:O26,D2;2025:O21,D3|Barriers, message/feedback, scalar chain, cross-hierarchy flow, network, upward feedback and nonverbal leadership.|Study sender/encoding/channel/receiver/decoding/noise/feedback; direction versus network; formal/informal; semantic/psychological/organisational/personal barriers; listening, culture and nonverbal consistency.|Diagnose the exact barrier then match a remedy; draw chain/circle/wheel/all-channel and compare speed/accuracy/participation.
Management leadership/power|Transactional/transformational, trait/behavioural, Lewin, contingency, Grid and power bases|2021:D2;2023:O9-10,O19;2024:O25,D3|Compare leadership theories/styles, identify contingency models and positional/personal power.|Study leadership versus management; rewards/vision; traits versus behaviours; task/people; fit with situation; legitimate/reward/coercive/expert/referent bases and ethical use.|Compare two leaders in the same banking case and justify when a style should change rather than naming a universally best leader.
Management thinkers|Weber, Fayol, scientific management and open systems|2021:O28;2023:D1;2025:O12-14|Bureaucracy, fourteen principles, time/motion study, hierarchy and environmental interaction.|Study Taylor/standardisation, Fayol/administration, Weber/bureaucracy, human relations and systems/contingency approaches; contribution, limitation and current relevance. The 2025 hierarchy item is ambiguous because its most natural theorist is absent from options.|Make thinker -> core idea -> tool -> limitation -> bank example; flag ambiguous recollections instead of learning an incorrect attribution.
Management personality/emotions|Big Five and emotional dissonance|2022:O26;2023:O23-24,D2|Conscientiousness, personality dimensions and felt/displayed emotion difference.|Study OCEAN dimensions, behaviour examples, personality versus mood/attitude, emotional labour/dissonance and organisational applications; avoid treating traits as fixed performance guarantees.|Identify the trait from behaviour, explain one job implication and distinguish emotional dissonance from cognitive dissonance.
Management ethics/governance|CSR, stakeholder theory, governance principles and bank-board oversight|2021:D3;2022:O4-7;2023:O11-15,O20|Governance need/principles, CSR thresholds/committee and stakeholder relationships.|Study accountability/transparency/fairness/responsibility, agency/stakeholder/stewardship, independent oversight, conflicts and CSR legal triggers. Separate Companies Act requirements from RBI bank-specific directions; source attribution to SEBI is not automatically correct.|Compare governance, management, ethics and CSR; build law/authority/applicability/threshold matrix.
Management ethics/governance|Ethical theories, responsibility, codes and ethical culture|2022:O28,D6;2023:O25-26,D5;2024:D4;2025:O10-11,O26|Consequences, responsibility displacement, values, relativism/absolutism, code implementation and managerial ethics.|Study utilitarian/teleological, duty, virtue, justice, rights/care, moral disengagement, conflicts, leadership example, incentives, whistleblowing and enforcement. Distinguish a written code from effective ethical culture.|Analyse stakeholder harm/options/principle/action/safeguard; explain how a code can fail despite formal adoption.
Management passage application|Culture assessment and World Management Survey-style passage|2024:O1-4,O13-16|Learning/culture, survey tool, communication outcome, training resistance and assessment.|Study culture versus climate, learning, performance monitoring, targets, incentives and change; separate passage retrieval from external report knowledge. These items do not establish a need to memorise every survey statistic.|Answer from evidence in the passage; explain one management mechanism rather than treating every survey mention as current trivia.
Cross-cutting environment|Planetary boundaries, circular economy, MDGs and SDGs|2024:O17-20|Report finding, response model, predecessor goals and objectives.|Study ecological limits, material loops, resource efficiency, historical MDG/SDG relationship and environmental-social trade-offs; distinguish dated boundary findings from stable concepts.|Draw linear versus circular resource flows and connect a firm's action to a measurable environmental outcome.
Other policy overlap|E-aksharayan and National Language Translation Mission|2021:O18-19|Software identification and Budget-announced translation initiative.|Study tool versus mission, purpose, administering body and accessibility; keep current-policy identification separate from static semantic-barrier theory.|Explain how a language tool can reduce but not eliminate organisational or cultural communication barriers.
"""

ESSAYS = [
    (2021, 1, "Education/learning", "Coding in schools", "Computational thinking, problem solving, creativity, teacher capacity, access, screen exposure and age-appropriate pedagogy.", "Weigh benefits and costs; distinguish coding literacy from compulsory early specialisation.", "Outline thesis, two benefits, two implementation risks, balanced curriculum and conclusion."),
    (2021, 2, "Business/digital", "Future of Indian BPO", "Automation/AI, cost and skill advantages, higher-value services, data protection, global demand and reskilling.", "Analyse a future trajectory rather than narrating the industry's history.", "Build opportunity/threat/adaptation paragraphs with conditions for competitiveness."),
    (2021, 3, "Business/digital", "Creative thinking in business", "Innovation, customer problems, experimentation, organisational culture, incentives, diversity and execution.", "Explain how creativity improves outcomes and why creativity alone is insufficient.", "Use idea -> test -> implementation -> feedback; contrast innovation with novelty."),
    (2021, 4, "Social/philosophical", "Prevention rather than cure", "Public health, disaster preparedness, financial risk, maintenance, education and the limits of preventive expenditure.", "Interpret the proposition, apply it across domains and avoid an absolute claim.", "Develop three domains and a counterargument about uncertainty/resource constraints."),
    (2022, 1, "Climate/energy", "Renewables and interconnected green grids", "Intermittency, storage, geographic/time-zone diversity, transmission, grid stability, financing and sovereignty.", "Cover advantages AND disadvantages, then explain how grid integration helps and what it cannot solve.", "Use problem -> grid mechanism -> residual limitation; distinguish energy generation from transmission."),
    (2022, 2, "Business/digital", "Women entrepreneurs and growth", "Credit/collateral, property rights, care work, networks, digital markets, jobs and agency.", "Link entrepreneurship to growth through mechanisms, not only empowerment slogans.", "Explain barriers, targeted responses, measurable outcomes and diversity among women entrepreneurs."),
    (2022, 3, "Social/philosophical", "Peace through understanding", "Dialogue, trust, institutions, cultural literacy, conflict drivers, deterrence and justice.", "Interpret and evaluate a proposition without reproducing a quotation-led generic essay.", "Develop interpersonal, domestic and international examples plus limits of dialogue alone."),
    (2022, 4, "Social/philosophical", "Medical tourism in India", "Cost/quality, specialist care, accreditation, visas, language, patient safety and domestic equity.", "Assess opportunity alongside regulatory and distributional challenges.", "Balance competitiveness with capacity, ethical care and access for domestic patients."),
    (2023, 1, "Climate/energy", "Climate impacts on developing economies", "Agriculture, heat/productivity, health, infrastructure, inflation, fiscal space, debt and adaptation finance.", "Keep developing-country vulnerability and economic transmission central.", "Trace shock -> sector -> household/fiscal impact; discuss adaptation, finance and just transition."),
    (2023, 2, "Business/digital", "E-rupee", "CBDC versus cash/deposits/UPI/crypto, retail/wholesale uses, privacy, inclusion, resilience and bank funding.", "Explain what CBDC changes rather than assuming all digital payments are currency.", "Compare benefits, design trade-offs and adoption conditions; avoid unsupported pilot statistics."),
    (2023, 3, "Workplace/people", "Innovative employee motivation", "Autonomy, mastery, purpose, fair pay, recognition, growth, flexibility, feedback and goal alignment.", "Connect employee needs with organisational performance and safeguards against manipulation.", "Use intervention -> mechanism -> outcome -> risk and distinguish intrinsic/extrinsic incentives."),
    (2023, 4, "Business/digital", "Multilingual social media for business", "Market reach, trust, localisation, translation quality, moderation, brand consistency and cost.", "Evaluate need and execution, not just list languages or platforms.", "Compare central brand control with local adaptation and accessibility."),
    (2024, 1, "Social/philosophical", "Hosting Olympics: three dimensions", "Tourism/infrastructure/jobs, displacement/equity, public spending, carbon/material use, legacy and governance.", "Explicitly cover SOCIAL, ECONOMIC and ENVIRONMENTAL effects.", "Make a three-axis cost-benefit outline with opportunity cost and post-event asset use."),
    (2024, 2, "Climate/energy", "Climate migration", "Sudden/slow-onset hazards, internal/cross-border movement, livelihoods, remittances, urban services and rights.", "Discuss both origin and destination countries; avoid treating all migration as solely climate-caused.", "Use origin/destination benefits/costs matrix and coordinated adaptation/protection policies."),
    (2024, 3, "Workplace/people", "Employee mental health", "Workload, control, bullying, insecurity, stigma, managerial training, confidential support and reasonable accommodation.", "Explain importance and concrete organisational actions without diagnosing individuals.", "Separate prevention, early support and referral; include privacy and evaluation safeguards."),
    (2024, 4, "Education/learning", "Lifelong learning", "Adaptability, curiosity, adult learning, digital inclusion, workplace learning and barriers of time/cost.", "Interpret the age/learning proposition rather than write only about formal schooling.", "Use personal, organisational and social levels plus realistic access conditions."),
    (2025, 1, "Climate/energy", "India's emissions-intensity pathway", "Intensity versus absolute emissions, energy efficiency, renewables, industry/transport, finance, measurement and just transition.", "Respond to the specified target and way forward; do not confuse percentage reduction in intensity with absolute emissions.", "Build sector -> action -> constraint -> implementation metric; authenticate the target before using it as current evidence."),
    (2025, 2, "Business/digital", "Advertising: paper to digital billboards", "Digital targeting/display, real-time content, costs, measurement, energy/e-waste, distraction, privacy and regulation.", "Focus on the specified media shift and technological change, not only internet advertising.", "Compare formats, business value and public-space safeguards; distinguish correlation from measured advertising impact."),
    (2025, 3, "Education/learning", "Young people supporting older learners", "Digital literacy, mentoring, accessibility, respect, reverse mentoring, intergenerational exchange and online safety.", "Keep education and older people's agency central; avoid patronising stereotypes.", "Propose accessible peer-learning models with mutual benefit and measurable skills."),
    (2025, 4, "Business/digital", "Adapting Western startup models to India", "Purchasing power, infrastructure, language, trust, regulation, unit economics and local problem discovery.", "Evaluate contextual relevance rather than assert that all copying is either good or bad.", "Use transferable principle -> local constraint -> adaptation -> viable business outcome."),
]

TASKS = [
    (2021, "Precis", "Sand scarcity and extraction", "Distinguish abundant sand from construction-suitable sand; retain demand, extraction, environmental damage and regulatory response.", "Preserve the causal chain; remove illustrative detail before dropping a main claim.", "Approximately 170 words in supplied paper."),
    (2022, "Precis", "Space exploration and space race", "Map the passage's central claim, motivations, rivalry/cooperation and benefits/costs as actually expressed.", "Do not replace the author's argument with a general space-policy essay.", "Approximately 170 words in supplied paper."),
    (2023, "Precis", "AI and women's economic empowerment", "Retain opportunity, access/skills constraints, bias/exclusion risks and the author's policy conditions.", "Keep a balanced passage balanced; do not reduce it to AI optimism or fear.", "180-200 words in supplied paper."),
    (2024, "Precis", "AI as CEO", "Retain decision capability, efficiency, human judgement, responsibility and limits in the passage's order of reasoning.", "Distinguish automation of tasks from full substitution of leadership.", "180-200 words in supplied paper."),
    (2025, "Precis", "Amazon climate regime and forest risk", "Preserve warming/drought, forest vulnerability, feedbacks and the distinction between scientific projection and certainty.", "Do not turn may/could into will or add outside climate statistics.", "180-200 words in supplied paper."),
    (2021, "RC", "Agorism passage / insurance questions mismatch", "The printed passage and subquestions do not match; use only for source-error recognition, not scored passage-based inference.", "Do not fabricate an insurance passage or answer with unrelated outside knowledge.", "30 marks shown; content pair unusable for faithful RC marking."),
    (2022, "RC", "FMC-SEBI merger", "Retrieve reasons for integration, regulatory benefits, market-development implications and constraints from the passage.", "Distinguish what the author states from external knowledge of today's regulation.", "30 marks; use own words and the actual question limits."),
    (2023, "RC", "Inflation, business profits and distribution", "Track claims, supporting evidence, price/wage/profit relationships, competing explanations and qualifications.", "An economist's argument is not automatically the author's unconditional conclusion.", "30 marks; answer the specific causal/comparative demand."),
    (2024, "RC", "Customer Relationship Management", "Explain functions, cross-team information flow, deployment choices, integration and implementation problems from the text.", "Separate a definition, a benefit, an implementation condition and an inference.", "30 marks; unfamiliar business technology must remain passage-grounded."),
    (2025, "RC", "Desalination, osmosis and power", "Track freshwater/saltwater flows, membrane/pressure mechanism, water-energy relationship and technical limitations.", "Draw a process diagram first; do not reverse the direction of flow or substitute general water-policy facts.", "30 marks; preserve scientific relationships in plain language."),
]

ENGLISH_PAGES = {2021: (70, 72), 2022: (65, 69), 2023: (71, 73), 2024: (68, 71), 2025: (65, 68)}
RC_TARGETS = {
    2022: [
        "Explain the original reason for commodity-market oversight.",
        "Explain expected effects of bringing FMC and SEBI together.",
        "Retrieve the historical rationale for separating commodities and securities.",
        "Trace the consequences of that institutional separation.",
        "Explain implications for exchanges and market participants.",
    ],
    2023: [
        "Explain the proposed link between the cost-of-living crisis and business markups.",
        "Identify the conventional price-change measure used in the passage.",
        "Explain why CPI alone cannot allocate gains between workers and employers.",
        "Compare tax and profit contributions using the passage's stated period/evidence.",
        "Identify industries used as markup examples without generalising to every industry.",
    ],
    2024: [
        "Explain CRM's principal function and business value.",
        "Trace how shared customer information supports cross-department collaboration.",
        "Compare cloud and on-premises deployment and the conditions favouring each.",
        "Diagnose data, integration, adoption and other implementation constraints in the text.",
        "Explain the described AI contribution without adding unsupported capabilities.",
    ],
    2025: [
        "Explain the local water problem and the desalination plant's role.",
        "Connect concentrated brine's environmental problem to the power-generation proposal.",
        "Explain membrane flow, pressure and electricity generation in the right causal order.",
        "Compare the stated advantages with other renewable sources.",
        "Identify expansion potential and the technological bottleneck specified in the text.",
    ],
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def table(headers, rows, css=""):
    esc = html.escape
    head = "".join(f"<th scope='col'>{esc(str(v))}</th>" for v in headers)
    body = "".join("<tr>" + "".join(f"<td>{esc(str(v))}</td>" for v in row) + "</tr>" for row in rows)
    return f"<div class='evidence-table'><table class='{css}'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def parse_refs(text, subject):
    result = set()
    for block in text.split(";"):
        year, items = block.split(":")
        kind = None
        for item in items.split(","):
            if item[0] in "OD":
                kind, item = item[0], item[1:]
            if kind is None:
                raise ValueError(f"Missing question kind: {text}")
            bounds = [int(x) for x in item.split("-")]
            if len(bounds) not in (1, 2) or (len(bounds) == 2 and bounds[0] > bounds[1]):
                raise ValueError(f"Invalid question range: {item}")
            for q in range(bounds[0], bounds[-1] + 1):
                result.add((subject, int(year), kind, q))
    return result


def catalog(raw, subject):
    rows = []
    for line in raw.strip().splitlines():
        fields = line.split("|")
        if len(fields) != 6:
            raise ValueError(f"Expected six inventory fields: {line}")
        group, name, refs, asked, study, task = fields
        rows.append(dict(subject=subject, group=group, name=name, references=refs,
                         asked=asked, study=study, task=task,
                         keys=parse_refs(refs, subject)))
    return rows


def build_distribution(objectives, descriptives, essays):
    parts = ["""<article id="weightage"><h2>Static, rules and current-affairs distribution</h2>
<p><b>Verified counts, not invented objective marks.</b> The 2021-2025 compilations contain
30 objective questions per ESI/FM paper but omit each question's weight. The recent structure
is 50 objective plus 50 attempted descriptive marks. Question shares below are NOT measured
mark shares. Descriptive choices offer 75 marks (three 15-mark and three 10-mark questions);
the 50-mark attempt is two of each. Confirm the eventual exam rules from RBI.</p>
<p>Static = concepts, institutions and historical knowledge. Standing rules = scheme/product/
regulatory provisions, which may be old but need updating. Dated = report findings, events,
incumbents, new initiatives or changed rules. A current passage can ask a static concept.
Economics/social/environment boundaries are judgement calls; one primary label prevents
double counting and the underlying CSV preserves overlap/source notes.</p>"""]
    for subject in ("ESI", "FM"):
        sub = [r for r in objectives if r["subject"] == subject]
        counts = Counter(r["category"] for r in sub)
        rows = []
        for category, total in counts.most_common():
            ks = [sum(r["year"] == str(y) and r["category"] == category for r in sub) for y in range(2021, 2026)]
            low = sum(k + max(0, k - 10) for k in ks) / 5
            high = sum(k + min(k, 20) for k in ks) / 5
            rows.append([category, *ks, total, f"{total/150:.1%}", f"{low:.1f}-{high:.1f}"])
        parts.append(f"<h3>{subject}: objective questions and conditional marks bounds</h3>")
        parts.append(table(["Category", "2021", "2022", "2023", "2024", "2025", "Total /150",
                            "Question share", "Possible mean marks /50*"], rows))
        parts.append("<p>*Conditional on twenty 2-mark and ten 1-mark questions each year. These mathematical "
                     "bounds are not observed marks, expected weightage or yearly ranges; category endpoints "
                     "cannot generally be added. For k questions the bounds are k+max(0,k-10) to k+min(k,20).</p>")
        parts.append(table(["Knowledge basis", "Questions /150"], [
            [label, sum(r["knowledge_basis"] == code for r in sub)]
            for code, label in [("T", "Static/enduring"), ("R", "Standing scheme/regulatory rules"), ("D", "Explicitly dated/current")]
        ]))
        parts.append(f"<h3>{subject}: descriptive marks OFFERED, not necessarily attempted</h3>")
        domains = ["E", "S", "X"] if subject == "ESI" else ["F", "M"]
        rows = []
        for y in range(2021, 2026):
            ds = [r for r in descriptives if r["subject"] == subject and r["year"] == str(y)]
            marks = [sum(int(r["offered_marks"]) for r in ds if r["primary_domain"] == domain) for domain in domains]
            basis = [sum(int(r["offered_marks"]) for r in ds if r["knowledge_basis"] == b) for b in "TRD"]
            if sum(marks) != 75 or sum(basis) != 75:
                raise ValueError(f"Descriptive totals fail: {subject} {y}")
            rows.append([y, *marks, *basis])
        parts.append(table(["Year", *domains, "Concept/application/history", "Standing policy/rules", "Explicit report/current anchor"], rows))
        parts.append("<p>E = economics; S = social; X = environment/cross-cutting; F = finance; M = management. "
                     "Poverty/jobs are primarily economics; basic welfare/migration primarily social. "
                     "Corporate governance is assigned to management; 2025 financial AI/ethics primarily finance. "
                     "Hybrid answers still need both concepts and evidence; these labels do not split the marks inside an answer.</p>")
    counts = Counter(r["primary_family"] for r in essays)
    parts.append("<h3>English: 40 essay + 30 precis + 30 comprehension</h3>")
    parts.append(table(["Primary essay family", "Offered options /20", "Share of options, NOT marks"],
                       [[name, n, f"{n/20:.0%}"] for name, n in counts.most_common()]))
    parts.append("""<p>Four essay options per year, choose one. Essay limits in the supplied
recollections change from about 300 words (2021-22) to 600-620 (2023-25).
Historical frequency is not a 2027 prediction. No 2020 paper was supplied; 2019 is an older
format and the supplied 2026 paper is Phase I only. They are not pooled here.</p>
<p><a href="phase2_static_current_weightage_audit.html">Standalone weightage audit</a> |
<a href="phase2_objective_weightage_manual_audit.csv">300-question objective classification</a> |
<a href="phase2_descriptive_weightage_manual_audit.csv">60-question descriptive classification</a></p>
</article>""")
    return "".join(parts)


def render_evidence_extension(output):
    objectives = read_csv(output / "phase2_objective_weightage_manual_audit.csv")
    descriptives = read_csv(output / "phase2_descriptive_weightage_manual_audit.csv")
    essay_audit = read_csv(output / "phase2_essay_theme_weightage_audit.csv")
    if (len(objectives), len(descriptives), len(essay_audit)) != (300, 60, 20):
        raise ValueError("Unexpected size of Phase II evidence inputs")
    index = {}
    for row in objectives:
        key = (row["subject"], int(row["year"]), "O", int(row["ordinal"]))
        index[key] = row
    for row in descriptives:
        key = (row["subject"], int(row["year"]), "D", int(row["original_question"]))
        index[key] = row
    expected = {(s, y, kind, q) for s in ("ESI", "FM") for y in range(2021, 2026)
                for kind, count in (("O", 30), ("D", 6)) for q in range(1, count + 1)}
    if set(index) != expected or len(index) != len(objectives) + len(descriptives):
        raise ValueError("Missing or duplicate question keys")
    entries = catalog(ESI, "ESI") + catalog(FM, "FM")
    covered = set().union(*(r["keys"] for r in entries))
    if covered != expected:
        raise ValueError(f"Coverage mismatch; missing={sorted(expected-covered)}, invalid={sorted(covered-expected)}")
    if len(ESSAYS) != 20 or {(r[0], r[1]) for r in ESSAYS} != {(y, q) for y in range(2021, 2026) for q in range(1, 5)}:
        raise ValueError("Essay option coverage mismatch")
    if len(TASKS) != 10 or {(r[0], r[1]) for r in TASKS} != {(y, t) for y in range(2021, 2026) for t in ("Precis", "RC")}:
        raise ValueError("Precis/RC task coverage mismatch")
    esc = html.escape

    def english_evidence(year):
        start, end = ENGLISH_PAGES[year]
        path = (output.parent / "PYP" / f"{year} (Phase 1-2).pdf").resolve()
        return (f"<p class='evidence-refs'>Evidence: <a href='{esc(path.as_uri(), quote=True)}#page={start}'>"
                f"{year} English, physical PDF pp{start}-{end}</a>.</p>")

    parts = ["""<section id="detailed-what" class="evidence-extension">
<h1>Detailed WHAT to study: evidence-linked inventories</h1>
<p>This extension adds the distribution audit and concrete study demands to the original
Phase II analysis below. It maps <b>all 300 ESI/FM objective questions, all 60 descriptive
options, all 20 essay options and all 10 precis/RC tasks</b> in the supplied 2021-2025 sample.
Prompts are paraphrased, not copied. The inventories explain preparation scope, not answer keys.</p>
<p><a href="#weightage">Distribution</a> |
<a href="#what-ESI">ESI reports, schemes and policies</a> |
<a href="#what-FM">Finance and management</a> |
<a href="#what-English">English task-by-task</a> |
<a href="#inventory-method">Method and source limits</a></p>
<p><b>How to use:</b> first read WHAT WAS ASKED; then study the named mechanisms/rules in
WHAT TO PREPARE; finally complete the retrieval/application task. These are recommended
depth targets, not future question predictions. Source references are optional verification:
the study requirements are written here so you do not have to open PDFs to understand them.</p>"""]
    parts.append(build_distribution(objectives, descriptives, essay_audit))
    export = []
    for subject in ("ESI", "FM"):
        sub = [r for r in entries if r["subject"] == subject]
        parts.append(f"<article id='what-{subject}'><h2>{subject}: named-item study inventory</h2>")
        groups = list(dict.fromkeys(r["group"] for r in sub))
        parts.append("<p>" + " | ".join(f"<a href='#inventory-{subject}-{i}'>{esc(g)}</a>" for i, g in enumerate(groups)) + "</p>")
        for i, group in enumerate(groups):
            parts.append(f"<h3 id='inventory-{subject}-{i}'>{esc(group)}</h3>")
            for row in [r for r in sub if r["group"] == group]:
                keys = sorted(row["keys"])
                years = sorted({key[1] for key in keys})
                refs = []
                source_records = []
                for key in keys:
                    source = index[key]
                    _, y, kind, q = key
                    if kind == "O":
                        page = source["physical_pdf_page"]
                        page_label = page
                    else:
                        page = source["section_pdf_page_start"]
                        page_label = f"{page}-{source['section_pdf_page_end']} (section)"
                    path = (output.parent / source["source"]).resolve()
                    label = f"{y} {'O' if kind == 'O' else 'D'}Q{q} p{page_label}"
                    refs.append(f"<a href='{esc(path.as_uri(), quote=True)}#page={page}'>{esc(label)}</a>")
                    source_records.append({"year": y, "kind": kind, "question": q, "source": source["source"],
                                           "page_or_section": page_label})
                parts.append(
                    f"<div class='inventory-card' data-subject='{subject}'>"
                    f"<h4>{esc(row['name'])}</h4>"
                    f"<p class='evidence-meta'>Observed in {len(years)} distinct year(s): {', '.join(map(str, years))}. "
                    "Year count describes this named theme, not a score allocation.</p>"
                    f"<p><b>What was asked:</b> {esc(row['asked'])}</p>"
                    f"<p><b>What to prepare:</b> {esc(row['study'])}</p>"
                    f"<p><b>Depth / retrieval task:</b> {esc(row['task'])}</p>"
                    "<p class='evidence-refs'><b>Evidence:</b> " + "; ".join(refs) + "</p></div>"
                )
                export.append({k: v for k, v in row.items() if k != "keys"} | {"evidence": source_records})
        parts.append("</article>")
    parts.append("""<article id="what-English"><h2>English: detailed WHAT, not just topic labels</h2>
<p><b>No fixed report/scheme reading list is established by English PYQs.</b> Reports and
ESI/FM knowledge can supply examples for essays; precis and RC must remain faithful to the
given passage. Topic familiarity is not a substitute for reading and writing skills.
The following are study/argument directions, not model essays or official marking rubrics.</p>
<h3>All twenty offered essays: specific content and command</h3>""")
    for year, option, family, name, scope, command, task in ESSAYS:
        parts.append(f"<div class='inventory-card essay-card'><h4>{year} option {option}: {esc(name)}</h4>"
                     f"<p class='evidence-meta'>Primary preparation family: {esc(family)}. Essay: 40 marks; choose one of four.</p>"
                     f"<p><b>What to prepare:</b> {esc(scope)}</p><p><b>Exact demand to practise:</b> {esc(command)}</p>"
                     f"<p><b>Output:</b> {esc(task)}</p>{english_evidence(year)}</div>")
    parts.append("<h3>Precis and comprehension: all ten task records</h3>")
    for year, kind, theme, content, skill, limit in TASKS:
        parts.append(f"<div class='inventory-card language-task'><h4>{year} {kind}: {esc(theme)}</h4>"
                     f"<p><b>What to understand:</b> {esc(content)}</p><p><b>Skill target:</b> {esc(skill)}</p>"
                     f"<p><b>Constraint:</b> {esc(limit)}</p>")
        if kind == "RC" and year in RC_TARGETS:
            parts.append("<p><b>Five specific answer operations:</b></p><ol>" +
                         "".join(f"<li>{esc(target)}</li>" for target in RC_TARGETS[year]) + "</ol>")
        parts.append(english_evidence(year) + "</div>")
    parts.append("""<h3>The actual language syllabus to practise</h3>
<p><b>Essay:</b> decode command words, choose a defensible thesis, cover every requested
dimension, organise causal/comparative paragraphs, provide relevant examples, test a
counterargument and reach a reasoned conclusion. Practise direct introductions and precise
transitions rather than memorised essays.</p>
<p><b>Precis:</b> identify thesis and major propositions; preserve cause/contrast/qualification;
generalise lists accurately; remove repetition/examples before central ideas; paraphrase,
count words and check fidelity. Add a title only when required. An explicit word limit takes
precedence over a mechanical one-third rule.</p>
<p><b>RC:</b> distinguish retrieval, explanation, comparison and inference; match the answer
to the command, use passage evidence, preserve technical relationships and paraphrase
without changing meaning. External knowledge must not override the supplied text.</p>
<p><b>Language:</b> subject-verb agreement, articles, tense consistency, pronoun reference,
prepositions, parallel structure, punctuation, concise sentences and accurate vocabulary.
Edit first for missing subparts/logic, then repetition, then grammar and word limit.
These are recommended enabling skills, not a claim that grammar is a separate marked paper.</p>
<h3>Reusable argument/evidence bank</h3>
<p>Maintain five family sheets: climate/energy; business/digital; workplace/people;
education/learning; social/health/philosophical. For each keep three mechanisms, two dated
and verified examples, two counterarguments and practical implementation conditions.
Use ESI climate/gender/welfare and FM digital-finance/management knowledge selectively;
do not cram report names into an English essay simply to sound informed.</p></article>
<article id="inventory-method"><h2>Evidence limits, coverage and update method</h2>
<p>Every ESI/FM item has at least one inventory entry; an item can connect several themes.
Consequently inventory theme/year counts overlap and must not be added as question totals.
OQ means objective ordinal; DQ means descriptive option. Descriptive page references identify
the verified section range, not a newly inferred exact question page.</p>
<p>2021 ESI OQ1 is printed Q11 by mistake; it is distinct from the real OQ11.
2021 ESI OQ5 lacks enough context for a reliable named-report attribution.
2025 ESI OQ11-14 follow a mismatched recreated agriculture passage; classification follows
the actual MSME subquestions. The 2025 WDR welfare demand does not establish a precise
edition. 2025 FM OQ28-30 explicitly warn that reconstructed question/theme may not be exact.
Some regulatory preambles and thinker attributions are imprecise: authenticate rules and
theories rather than learning recalled errors. 2021 English RC has incompatible passage/questions.</p>
<p><b>Update workflow:</b> keep historical question evidence unchanged; add the latest verified
edition/rule in a separate dated column. For a report record publisher, title/edition,
reference period, method, three findings, policy implications and caveats. For a scheme record
ministry/agency, objective, beneficiary, eligibility/exclusions, benefits/funding, delivery,
current status and application cases. For policy record authority/instrument, old/new rule,
effective date, applicability, rationale, mechanism, risks and exceptions.</p>
<p><b>Breadth safeguard:</b> these inventories answer what the supplied papers asked; they do
not replace the official syllabus. The original syllabus-wide analysis remains below.
Suggested future reading or example programmes are not counted as historically named PYQs.
No current legal limit, statistic, scheme availability or report finding is authenticated merely
by its appearance in a memory-based question.</p>
<p><a href="phase2_detailed_what_inventory.json">Machine-readable named-item inventory</a> |
<a href="phase2_inventory_coverage.json">Coverage verification</a> |
<a href="phase2_english_task_audit.json">Original English task audit</a></p>
</article></section>""")
    english_export = []
    for year, option, family, name, scope, command, task in ESSAYS:
        start, end = ENGLISH_PAGES[year]
        english_export.append(dict(year=year, type="Essay", option=option, family=family,
                                   name=name, study=scope, demand=command, task=task,
                                   source=f"PYP\\{year} (Phase 1-2).pdf", section_pages=[start, end]))
    for year, kind, theme, content, skill, limit in TASKS:
        start, end = ENGLISH_PAGES[year]
        english_export.append(dict(year=year, type=kind, name=theme, study=content, task=skill,
                                   constraint=limit, source=f"PYP\\{year} (Phase 1-2).pdf",
                                   section_pages=[start, end],
                                   answer_operations=RC_TARGETS.get(year, []) if kind == "RC" else []))
    coverage = dict(objective_questions=300, descriptive_options=60, covered_questions=len(covered),
                    missing_questions=[], essay_options=20, precis_rc_tasks=10,
                    named_esi_entries=sum(r["subject"] == "ESI" for r in entries),
                    named_fm_entries=sum(r["subject"] == "FM" for r in entries))
    for name, data in [
        ("phase2_detailed_what_inventory.json", {"ESI_FM": export, "English": english_export}),
        ("phase2_inventory_coverage.json", coverage),
    ]:
        (output / name).write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
    print("Detailed inventory:", json.dumps(coverage))
    return "".join(parts)
