# Question Exporter

## Export An OBS Recording

On Windows, the recording exporter uses portable FFmpeg and built-in Windows OCR; Python is not required. FFmpeg is downloaded to `%LOCALAPPDATA%/RBI-Recording-Exporter` if needed. No video is uploaded.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
./tools/export_recording.ps1 -Video "C:\Users\Pritam Sharma\Videos\phase1-2025-questions-answers-full.mp4" -OutputDirectory "recording-export/phase1-2025"
```

Open `recording-export/phase1-2025/questions-answers.html`. It is an image-first reader with topic navigation, recording timestamps, and a 1-200 question index. All 906 saved screens are included. OCR recognizes 196 question numbers; 4, 7, 9, and 52 are marked for source review rather than silently omitted. Topic labels are inferred from visible section headers, so mixed or unclear pages remain in review sections. The page images preserve the original options and explanations; question text is not reconstructed from noisy OCR, and spoken-only answers are not transcribed.

The default crop `1170:968:377:0` matches this 1920x1080 recording's PDF area. Use `-Crop ''` for the full frame or provide FFmpeg's `width:height:x:y` syntax. Frames are sampled every 0.5 seconds, and near-duplicate images are removed. Content that was never visible, moved too fast, or was unreadable cannot be recovered reliably.

Use a fresh output directory for another export. `-ReuseFrames` reruns OCR/HTML generation from an existing directory's frames and log without re-extracting video. When reusing a limited test export, pass the same `-LimitSeconds` value. `-Inspect` previews the recording; `-LimitSeconds 10` provides a short end-to-end test. Extracted JPEGs and `captures.json` are retained alongside the self-contained HTML.

Use `-BuildOnly` to rebuild just the HTML from saved `captures.json`, without rerunning OCR. The current recording produced 906 text screens; browser checks verified topic navigation, the 200-row question index, image rendering, and mobile fit. Four question numbers remain unrecognized by OCR and link to the full source archive for manual review.

## Export A Course Page

Export questions, options, and images from course content you are authorized to access. The supplied lesson URL requires sign-in and purchase/enrolment. The script does not bypass either requirement. Keep exports for permitted personal use; do not redistribute protected course material.

## Setup

Install Python 3.10 or newer from python.org if `python --version` does not report a version. Enable its PATH option during installation. The Windows Store app alias alone is not a Python installation.

Run these commands from the workspace root:

```powershell
python -m pip install -r tools/requirements.txt
python -m playwright install chromium
python tools/export_questions.py --output questions.html
```

Sign in directly in the opened browser. Open the questions and scroll through the intended content so lazy-loaded images appear, then press Enter in the terminal. In the browser, click the question text, press Arrow Up to widen the green outline until it includes the options and images, and press Enter to capture. Arrow Down narrows the selection; Escape cancels it. The resulting HTML can be opened directly in a browser.

The browser stores your session in `~/.rbi-question-export-browser`, outside the workspace. This directory contains sensitive login state: do not share or commit it. Close other exporter instances before reusing the same profile. Delete that directory when you no longer need the saved login.

## Multiple Screens

```powershell
python tools/export_questions.py --collect --output questions.html
```

Navigate manually between questions or pages, then capture each screen. Type `done` in the terminal to finish. Each capture is saved immediately. A new script run replaces the output file after its first successful capture; it does not append to an earlier run. Use a different output filename to keep previous exports.

If you know the actual question container's CSS selector, pass `--selector "YOUR_SELECTOR"` to skip the picker. It must match exactly one element. For HTML questions inside an iframe, pass `--frame-url "UNIQUE_FRAME_URL_SUBSTRING"`; selection occurs within that frame.

## PDF Or Image-Based Questions

The supplied lesson is labelled as a PDF. If the viewer does not expose HTML question text, use:

```powershell
python tools/export_questions.py --screenshot --collect --output questions.html
```

Select the rendered question/page area, including its options and diagrams. This embeds a PNG of that area in the HTML, so text is preserved visually, not as selectable text. Navigate or scroll to each page and capture again. Screenshots capture rendered pixels only, not unseen pages or an entire scrollable viewer. This mode does not bypass access restrictions or decrypt/download protected documents.

## Limits

- Only the selected, currently rendered DOM is captured. Hidden, unloaded, paginated, or virtualized questions require additional manual captures. No automatic question identification or deduplication is attempted.
- Images are embedded as data URLs where accessible using your browser session. Failed downloads retain the original URL and print a warning, so those images may not work offline. No credentials are written into the HTML.
- Text, radio/checkbox state, tables, inline SVG, readable canvases, and image backgrounds are retained. Layout is simplified for reading and printing; interactive scripts are removed.
- PDF viewers, video lessons, protected canvases, and text inside images are not converted into question text. Use screenshot mode for visible content, or an official PDF download when available; OCR is not included.
- The paid lesson's question layout has not been verified in an authenticated account. The region picker avoids assuming undocumented site selectors.

## Validation

After setup, run `python tools/test_export_questions.py` or the VS Code task `Validate Question Exporter`. The local fixture checks question text, options, script/hidden-content removal, multiple captures, and offline rendering of embedded images. It does not access your course account.