---
name: update-study-library
description: 'Update the local RBI study library and prioritised GA facts/data table from ESI, Finance, Management notes, monthly current affairs, reports, schemes and StaticGK PDFs. Scan every page across all four evidence folders on each update, curate missing facts, create source-linked maps/tables/cards, retain history and reveal all answers in printed PDFs.'
argument-hint: 'PDF paths, edition month, and optional topics/pages to process'
---

# Update the RBI Study Studio

This is a workspace-only Copilot workflow, not a standalone model or a folder watcher.
Never upload user PDFs to external services. Use local extraction and your reasoning.
The user wants useful short study aids, not reproductions of copyrighted notes.

## Files and commands

- Database: `study_library\library.json`.
- Published offline page: `study_library\index.html`.
- Validating/merging/rendering tool: `tools\study_library.py`.
- HTML template: `tools\study_library.html`.
- Complete example of the bundle format: `study_library\sample_bundle.json`.
- Tests: `tools\test_study_library.py`.
- Exact old database snapshots: `study_library\history`.
- Full-folder content/page audit: `study_library\evidence_scan.json`.
- Local extracted text for every scanned PDF page: `study_library\scan_text`.

On this Windows workspace, use the installed interpreter at
`$env:LOCALAPPDATA\Programs\Python\Python312\python.exe`.
Commands below run from the workspace root.

## Workflow

### Required sources for current-affairs linking

Always use relevant supplied PDFs from these folders under `SubjectNotesForPhase2`
when linking current affairs to study topics:

- `CurrentAffairs-Monthly`
- `Reports_NationalAndInternational`
- `SchemesAndGovernmentPortals` (the user's "SchemesAndGovernmentPortal")
- `StaticGK`

Check these four collections for relevant material rather than limiting linking
to monthly compilations. Use any relevant collection; do not force a link from
every folder. Reports provide frameworks and dated evidence; scheme notes provide
beneficiaries, exclusions and delivery details; StaticGK supplies background
connections, not proof of a recent event. Cite actual PDF pages and distinguish
static background from dated developments. Never infer currency from the folder
name or file timestamp. If no relevant supplied evidence exists, state the gap
instead of inventing a connection. Official-source verification can supplement
these PDFs but must not silently replace the requested local-source workflow.

### Processing steps

1. Begin every update by scanning every page of every PDF in all four evidence
   collections, including previously scanned files, then inspect the scan audit:

   ```powershell
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" .\tools\study_library.py scan
   ```

   The scan persists page text, content/image-stream fingerprints, new/changed
   pages, missing/removed files, low-text pages and pages not yet cited in GA.
   Review new/changed content AND uncited older content for missed facts.
   When auditing completeness, revisit previously cited pages too: one extracted
   row is not evidence that all useful facts on that page were considered.
   Do not treat unchanged file names, a machine scan or one citation on a page
   as proof of full semantic review or complete fact extraction. Use bounded
   batches and explicitly carry forward unprocessed pages; never silently
   declare the month complete. OCR/visually inspect low-text pages and complex
   tables/diagrams. The scanner deliberately does not invent or generate facts.
   If a registered PDF changed in place, restore the cited old version and
   register the new version separately; do not bypass immutable-source checks.
   If a file was only renamed or moved, match its exact SHA256/page count and
   repair its registered path using
   `study_library.py relocate <existing-source-id> "<new PDF path>"`, then build.
   Relocation rejects changed bytes and preserves a database snapshot. Existing
   bundles with the original path remain idempotent and retain the current
   registered path; do not create a duplicate source ID for an identical rename.
   Establish the PDF paths, requested coverage and edition month. Ask if a monthly
   PDF's edition is unclear. Never infer its reference period from file timestamps.
   Start with bounded batches; do not claim a whole PDF was covered after sampling.
2. Read the database's topic IDs, existing content and sources before proposing
   new topics. Prefer the same stable topic ID when new news belongs to an existing
   concept. Link related topics explicitly. Avoid duplicate topics with new spellings.
3. Extract relevant pages with the local tool. For example:

   ```powershell
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" .\tools\study_library.py extract "<workspace PDF path>" --id "unique-source-version-id" --title "Readable source title" --kind monthly --period 2026-10 --pages "3,68,88" --output "<session workspace>\extracted.json"
   ```

   Use `--kind notes` without `--period` for undated static notes. Omit `--pages`
   to extract the whole PDF, then read in bounded ranges. Output includes exact
   source path, SHA256, page count, kind, edition and one-based PDF page text.
   Copy the source object unchanged into the curated bundle. A modified PDF needs
   a new source-version ID. Never edit its old hash to bypass validation.
   Low-text/scanned pages stop extraction explicitly: locally OCR or visually
   inspect those pages before authoring. Tables, arrows and diagrams may be
   scrambled by extraction; inspect them visually where needed.
4. Read the extracted pages and actively curate concise paraphrases. Do not merely
   concatenate extracted text. Identify errors/ambiguities in the source; do not
   reinforce a doubtful rule as fact. Never invent missing statistics or fill gaps
   with purported source facts. Label original practice cases as illustrative.
5. Create one small topic packet, choosing useful tools rather than forcing every
   topic into the same shape:
   - 1-12 short map nodes and labelled, directed edges. Root comes first.
   - Comparison/fact/ratio tables. Formulas need a worked practice example.
   - Causal/mechanism chains represented by directed map edges.
   - Recall questions, confusable-rule cases and descriptive planning prompts.
   - Separate date-bearing fact observations for changing values.
   - Dated updates under `General`, `Finance` or `Economy` for monthly news.
   Every node, edge, table row, card, observation and update requires actual PDF
   page references, not guesses. Source links are provenance, not proof.
   The user requires explained teaching notes, not renamed headings, arrow
   lists or directions to consult PDFs. Use the optional `teaching_notes` list
   on the topic for original prose: each section has `id`, `title`,
   `paragraphs` (a nonempty list of strings) and `refs`. Explain definitions,
   causal mechanisms, assumptions, worked hypothetical examples, confusable
   distinctions and exam traps. Keep examples clearly separate from observed
   data and current legal rules. Retain the existing concept chapter and append
   genuinely new sections with unique IDs; a notes section is immutable.
   Begin a chapter with an explicit topic-level study plan: what to learn,
   priority and the intended explanation. Cover every listed target in detailed
   original notes; a short overview is not a substitute. When expanding an edition,
   map its contents and any body-only articles to the actual teaching chapters.
   Distinguish conceptual coverage from reproducing every clause/data cell or
   independently verifying every current claim. State omissions explicitly.
   Use optional `study_plan` entries for the checklist rendered before the prose.
   Each entry has `id`, `title`, `priority` (`P1`/`P2`/`P3`), `focus`, `refs` and
   exactly one target: `section` (a teaching-note ID in this topic), or `topic`
   (another existing chapter ID). Targets are validated and entries are immutable
   append-only. Chapter buttons navigate within the library, not to source PDFs.
   Read notes displays teaching prose followed by the revision/evidence tables.
   GA Direct notes includes the relevant family's teaching sections before
   its fact list. No PDF links or citation drawers belong in either reading
   view; preserve provenance in the separate Sources tab and database.
   Also append relevant GA facts/data to the existing `ga-family-b`,
   `ga-family-p`, `ga-family-e`, `ga-family-i`, `ga-family-t`, `ga-family-n`
   and `ga-family-a` topics (create a missing family once). Follow
   `PYP\analysis\build_ga_analysis.py`: B banking/finance, P schemes and E
   economy/data are P1; I international, T technology/infrastructure/defence,
   N environment/geography and A miscellaneous breadth are P2, not skippable.
   Use subject `GA`, exact tag `GA family: B` (or the matching letter) and a
   priority tag. Prefer compact tables with columns Item, Fact / distinction,
   Scope / caution, Edition / reference period; one paraphrased fact per row.
   Include issuer/mandate, beneficiary/exclusion, rule scope, measurement period
   and confusable distinctions as relevant. Keep numbers with units, publisher
   and period; distinguish proposals/announcements from effective rules.
   The dedicated GA view automatically collects four-folder table rows, fact
   observations and dated updates; it excludes illustrative answer cards.
   It defaults to GA-curated entries, with an explicit option for all referenced
   evidence including ESI. Do not copy the same fact into multiple GA rows merely
   because another compilation repeats it; append genuinely new observations.
6. Emit a JSON bundle using the example below and the sample bundle. Save the
   curated bundle under a distinct filename in `study_library\bundles` so it can
   be reimported. Use apply_patch for manual JSON edits.
7. Preserve identity/history:
   - Same topic ID/title/subject/summary; append new content using new item IDs.
   - Same table ID/title/columns to append rows.
   - Same fact ID/label for the SAME quantity, publisher, scope and reference
     period; append a new observation ID for a new release. Store dates in
     `as_of`. Different periods or publishers usually need different fact IDs.
   - Never overwrite an old observation to make the new source look consistent.
     The tool flags differing values automatically. It does not choose a winner.
   - Reusing an item ID with different content fails. Use new IDs instead.
     Exact repeated imports are no-ops.
   - For monthly items include a dated update plus fact observations for important
     changing values. All claims remain marked unverified by the UI. Do not promise
     official verification unless it has actually been performed.
8. Run the merge and check:

   ```powershell
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" .\tools\study_library.py merge ".\study_library\bundles\<batch>.json"
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" .\tools\study_library.py check
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" .\tools\test_study_library.py
   ```

   Errors are explicit; do not ignore failed extraction or validation.
   Merge preserves unrelated topics and creates a snapshot on changed imports.
   If HTML publishing fails after saving the database, repair the issue and run
   `build`; do not recreate or discard the database.
9. Verify the exact requested coverage, citations, displayed map connections,
   table/card usability and the review queue. Open the HTML with browser tools
   if available. Report PDFs/pages/topics processed, omissions, unresolved source
   claims and a link to the page. Tell the user to refresh an already open page.
   Each merge/build rescans all evidence pages and republishes coverage. Test the
   GA family/priority/month/collection filters and report outstanding uncited and
   low-text pages. Print/save PDF must reveal all answers and recall columns,
   open collapsed topic details and restore on-screen recall state afterwards.
   The default is notes-first: Read notes shows authored teaching sections,
   revision tables, facts and updates; the separate Recall cards view retains
   the original practice questions and all their revealable answers.
   GA defaults to Direct notes, with Compact table retained as an option.
   Author explanations that can be studied in place, not instructions merely
   telling the reader to open a source. Citations stay outside the reading
   notes in Sources; do not remove stored references or source cautions.
   Print the selected topic OR the filtered GA notes/table. Avoid duplicate
   notes plus practice panels in the same printout. Keep all answers visible.

## Bundle shape

`schema_version`, `sources` and `topics` are the only top-level fields.
Existing registered sources need not be repeated in an incremental bundle.
All topic collection fields are required; they can be empty, except map nodes.
Reference pages are physical PDF pages, not printed page labels.
`teaching_notes` is an optional additional topic field. Example section:
`{"id":"explain-output","title":"Understanding output","paragraphs":["Original explanatory prose."],"refs":[{"source":"registered-source-id","pages":[3]}]}`.
`study_plan` is an optional additional list rendered first. Example entry:
`{"id":"learn-output","title":"Output versus growth","priority":"P1","focus":"Definition, calculation and interpretation","section":"explain-output","refs":[{"source":"registered-source-id","pages":[3]}]}`.
For a course-level roadmap, replace `section` with `topic` pointing to another
chapter. Do not include both targets. Printed notes retain the checklist and
explanations; only the navigation buttons are omitted.

```json
{
  "schema_version": 1,
  "sources": [],
  "topics": [{
    "id": "existing-or-new-topic",
    "title": "Stable title",
    "subject": "ESI",
    "summary": "Stable short orientation, not a changing numeric claim.",
    "tags": ["employment"],
    "related": [],
    "map": {
      "nodes": [{"id": "root", "label": "Short concept", "refs": [{"source": "registered-source-id", "pages": [3]}]}],
      "edges": []
    },
    "tables": [{
      "id": "comparison",
      "title": "Stable comparison title",
      "columns": ["Concept", "Meaning"],
      "rows": [{"id": "row-a", "cells": ["A", "Short paraphrase"], "refs": [{"source": "registered-source-id", "pages": [3]}]}]
    }],
    "cards": [{
      "id": "recall-a",
      "question": "What would you retrieve?",
      "answer": "Short explanation.",
      "refs": [{"source": "registered-source-id", "pages": [3]}]
    }],
    "facts": [{
      "id": "specific-quantity-publisher-period",
      "label": "Clearly scoped quantity",
      "observations": [{
        "id": "release-observation-a",
        "value": "Value and unit; source claim",
        "as_of": "Release date; reference period; effective date if applicable",
        "refs": [{"source": "registered-source-id", "pages": [3]}]
      }]
    }],
    "updates": [{
      "id": "monthly-item-a",
      "date": "2026-10",
      "category": "Economy",
      "title": "What changed",
      "body": "Short paraphrase plus static-topic connection and verification caveat.",
      "refs": [{"source": "registered-source-id", "pages": [3]}]
    }]
  }]
}
```

Subjects: `ESI`, `Finance`, `Management`, `GA`. Use tags for overlaps.
Dates on updates are edition month `YYYY-MM`, or a verified event date
`YYYY-MM-DD`; do not confuse edition with event date. The tool conservatively
flags different value strings, including harmless wording differences, for human
review. It does not perform semantic deduplication, factual verification, or OCR.
