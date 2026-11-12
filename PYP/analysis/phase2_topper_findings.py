"""Render the persisted, partial topper-interview review into the Phase II reader."""

import html
import json


def render_topper_findings(output):
    data = json.loads((output / "rbi_topper_tips_traps_evidence.json").read_text(encoding="utf-8"))
    sources = data["sources"]
    esc = html.escape
    parts = [
        "<section id='topper-insights'><h1>Topper interviews: tips, traps and practical decisions</h1>",
        f"<p class='evidence-meta'>Research checked {esc(data['researched_on'])}. "
        "Publisher-labelled cohorts 2022-2026; partial content review, not a complete playlist audit.</p>",
        "<article id='topper-coverage'><h2>What was actually reviewed</h2>",
        f"<p><b>{data['playlist_entries']} playlist entries inventoried; "
        f"{data['metadata_retrieved']} metadata records retrieved; "
        f"{data['full_transcripts_retrieved']} public transcript retrieved "
        "(selected preparation passages reviewed); "
        f"{data['publisher_profiles_reviewed']} publisher-written profiles reviewed.</b></p>",
        "<p class='topper-warning'>YouTube rate-limited the remaining metadata requests and "
        "further transcript access. This is not a claim to have watched every video. "
        "Written profiles are edited publisher accounts, not verified verbatim transcripts. "
        "Auto-captions can mishear names and technical terms. Year labels come from publisher "
        "titles/descriptions, not independently verified RBI selection records. Upload years "
        "are not selection years. Multiple clips from one person are not independent endorsements.</p>",
        "<p>The 2026 evidence uses Divyanshu's timestamped transcript passages; 2025 uses "
        "Raghav Manglik's written profile; 2024 uses Ankit Pandey, Satender Singh and Tanay Gaurav; "
        "2023 uses Sai Gireesh, Prashant Meena and Tejdeepthi; 2022 uses Utkarsh Agrawal, "
        "Prasanth Akkiraju and Shobhita Bhola. Bhavana P J is supplemental evidence with "
        "no independently established cohort here.</p>",
        "<p>All findings are paraphrased. Practical actions and safeguards below are our synthesis, "
        "not topper quotations or official RBI prescriptions.</p>",
        "<h3>The preparation loop to remember</h3>"
        "<ol><li>Learn the exact demand.</li><li>Recall without notes.</li>"
        "<li>Apply, calculate or type.</li><li>Diagnose the error.</li>"
        "<li>Repair and retest on fresh material.</li></ol>",
        "<p><a href='rbi_topper_playlist_coverage.csv'>357-entry coverage inventory</a> | "
        "<a href='rbi_topper_tips_traps_evidence.json'>Evidence data and sources</a> | "
        "<a href='rbi_topper_tips_traps_2022_2026.html'>Standalone readable report</a></p></article>",
        "<article id='topper-practical-findings'><h2>18 actionable tips and corresponding traps</h2>",
    ]
    for number, item in enumerate(data["findings"], 1):
        parts.append(
            f"<div class='inventory-card topper-card' id='topper-{esc(item['id'], quote=True)}'>"
            f"<p class='evidence-meta'>{esc(item['area'])}</p>"
            f"<h3>{number}. {esc(item['title'])}</h3>"
            "<h4>What the accessible sources report</h4><ul>"
        )
        for key, seconds, statement in item["evidence"]:
            source = sources[key]
            url = source["url"]
            label = source["name"]
            if seconds is not None:
                url += f"&t={seconds}s"
                label += f" at {seconds // 60:02}:{seconds % 60:02}"
            else:
                label += " (written summary)"
            parts.append(f"<li>{esc(statement)} "
                         f"<a href='{esc(url, quote=True)}'>{esc(label)}</a>.</li>")
        parts.append("</ul><h4>How to apply it: our recommendation</h4>"
                     f"<p>{esc(item['action'])}</p>"
                     f"<p class='topper-trap'><b>Trap:</b> {esc(item['trap'])}</p></div>")
    parts.append("</article><article id='topper-conflicting-advice'>"
                 "<h2>Conflicting advice: use a decision rule instead</h2>"
                 "<p>Ask what prior preparation, time pressure and paper conditions made a "
                 "candidate's choice possible. Do not turn a successful gamble into a general rule.</p>"
                 "<div class='evidence-table'><table><thead><tr><th>Advice that conflicts</th>"
                 "<th>Differences in the accounts</th><th>Safer interpretation</th>"
                 "</tr></thead><tbody>")
    for topic, difference, rule in data["conflicts"]:
        parts.append(f"<tr><th scope='row'>{esc(topic)}</th>"
                     f"<td>{esc(difference)}</td><td>{esc(rule)}</td></tr>")
    parts.append("</tbody></table></div></article>"
                 "<article id='topper-study-workflow'><h2>Apply this to your chapter tasks</h2>"
                 "<p><b>The 480 prompts are a menu, not 480 notes-generation chores.</b> "
                 "Pick one task, obtain an explanation, verify it, retrieve it, then use it. "
                 "Generating an answer is not evidence that you have learned it.</p>"
                 "<div class='evidence-table'><table><thead><tr><th>When</th>"
                 "<th>Suggested action: our synthesis</th><th>Evidence of completion</th>"
                 "</tr></thead><tbody>")
    for when, task, result in data["suggested_workflow"]:
        parts.append(f"<tr><th scope='row'>{esc(when)}</th>"
                     f"<td>{esc(task)}</td><td>{esc(result)}</td></tr>")
    parts.append("</tbody></table></div>"
                 "<p>For ESI, pair a concept with a verified report or scheme application. "
                 "For Finance, add a worked calculation or rule-application case. For Management, "
                 "compare plausible theories in a fresh case. For English, type and review the "
                 "actual task rather than only reading model responses.</p>"
                 "<p><a href='#chapter-roadmap'>Choose a chapter task and AI prompt</a></p></article>"
                 "<article id='topper-evidence-bias'><h2>Traps in topper interviews themselves</h2><ul>")
    for warning in (
        "Survivorship bias: candidates who made the same gamble and failed are missing.",
        "Hidden starting advantage: three months of focused preparation may follow years of UPSC, "
        "banking, aptitude or writing practice.",
        "Provider selection and editing: these sources are associated with one coaching publisher. "
        "Product praise is not an independent comparison or a purchase recommendation.",
        "Recall and transcription error: scores, cutoffs, scheme figures and technical interview "
        "recollections are not verified official facts here.",
        "Outcome does not validate every tactic: surviving little typing practice, a Finance omission "
        "or an incomplete paper does not make that tactic desirable.",
        "Fixed-template trap: a successful framework is not a universal word split or official rubric.",
        "Escalating commitment: persistence is not an instruction to sacrifice sleep, livelihood or "
        "all backup options indefinitely.",
    ):
        parts.append(f"<li>{esc(warning)}</li>")
    parts.append("</ul></article><article id='topper-source-register'><h2>Topper source register</h2>"
                 "<p>Evidence links allow you to audit the recommendations; the usable notes "
                 "are already included above. No raw transcript is reproduced.</p>"
                 "<div class='evidence-table'><table><thead><tr><th>Person</th><th>Publisher-labelled "
                 "year</th><th>Evidence used</th><th>Links</th></tr></thead><tbody>")
    for source in sources.values():
        parts.append(f"<tr><td>{esc(source['name'])}</td><td>{esc(source['year'])}</td>"
                     f"<td>{esc(source['kind'])}</td><td>"
                     f"<a href='{esc(source['url'], quote=True)}'>Evidence source</a>")
        if source.get("video"):
            parts.append(f" | <a href='https://www.youtube.com/watch?v={esc(source['video'], quote=True)}'>"
                         "Playlist video</a>")
        parts.append("</td></tr>")
    parts.append("</tbody></table></div><p>Further playlist-wide content review remains incomplete. "
                 "Do not interpret the inventory as 357 content-reviewed interviews.</p></article></section>")
    return "".join(parts)
