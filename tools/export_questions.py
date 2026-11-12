"""Export a user-selected, accessible lesson region to standalone HTML."""

import argparse
import base64
import html
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_URL = (
    "https://courses.anujjindal.in/learn/home/"
    "rbi-grade-b-complete-course-phase1-2-with-practice-books/"
    "Past-Year-Paper-Analysis---RBI--SEBI---NABARD"
    "?bundleId=126879&lessonId=2397526"
)

PICK_REGION = r"""() => new Promise(resolve => {
    const banner = document.createElement('div');
    banner.textContent = 'Click content, then Arrow Up to widen / Arrow Down to narrow. Enter: capture. Escape: cancel.';
    banner.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;padding:14px;background:#fff;color:#111;border-bottom:2px solid #16803c;font:16px sans-serif;pointer-events:none';
    document.body.append(banner);
    let selected = null;
    let previousOutline = '';
    function highlight(element) {
        if (selected) selected.style.outline = previousOutline;
        selected = element;
        previousOutline = element.style.outline;
        element.style.outline = '3px solid #16803c';
    }
    function cleanup() {
        if (selected) selected.style.outline = previousOutline;
        banner.remove();
        document.removeEventListener('click', click, true);
        document.removeEventListener('keydown', key, true);
    }
    function click(event) {
        event.preventDefault();
        event.stopImmediatePropagation();
        highlight(event.target);
    }
    function key(event) {
        if (!['ArrowUp', 'ArrowDown', 'Enter', 'Escape'].includes(event.key)) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        if (event.key === 'Escape') { cleanup(); resolve(null); }
        else if (selected && event.key === 'ArrowUp' && selected.parentElement) highlight(selected.parentElement);
        else if (selected && event.key === 'ArrowDown' && selected.firstElementChild) highlight(selected.firstElementChild);
        else if (selected && event.key === 'Enter') {
            cleanup();
            resolve(selected);
        }
    }
    document.addEventListener('click', click, true);
    document.addEventListener('keydown', key, true);
})"""

SNAPSHOT = r"""root => {
    const clone = root.cloneNode(true);
    const originals = [root, ...root.querySelectorAll('*')];
    const copies = [clone, ...clone.querySelectorAll('*')];
    const assets = [];
    const warnings = [];
    function image(source) {
        const token = `EXPORT_ASSET_${assets.length}`;
        assets.push({token, source});
        return token;
    }
    for (let index = 0; index < originals.length; index++) {
        const original = originals[index];
        const copy = copies[index];
        const computed = getComputedStyle(original);
        if (computed.display === 'none' || computed.visibility === 'hidden') {
            copy.remove();
            continue;
        }
        for (const attribute of [...copy.attributes]) {
            const name = attribute.name.toLowerCase();
            if (name.startsWith('on') || ['style', 'id', 'class', 'srcdoc', 'srcset', 'autofocus'].includes(name)) copy.removeAttribute(attribute.name);
            if (['href', 'xlink:href', 'action', 'formaction'].includes(name)) copy.removeAttribute(attribute.name);
        }
        for (const property of ['font-size', 'font-weight', 'font-style', 'text-align', 'white-space', 'vertical-align']) {
            copy.style.setProperty(property, computed.getPropertyValue(property));
        }
        if (original.tagName === 'IMG') {
            const source = original.currentSrc || original.src || original.dataset.src;
            if (source) copy.setAttribute('src', image(new URL(source, document.baseURI).href));
            else warnings.push('An image had no loaded source. Scroll it into view before capturing.');
            copy.removeAttribute('width');
            copy.removeAttribute('height');
            copy.removeAttribute('loading');
        }
        if (original.tagName === 'CANVAS') {
            try {
                const replacement = document.createElement('img');
                replacement.src = original.toDataURL('image/png');
                replacement.alt = 'Captured canvas';
                copy.replaceWith(replacement);
            } catch { warnings.push('A protected canvas could not be exported.'); }
        }
        if (original.tagName === 'INPUT') {
            const replacement = document.createElement('span');
            replacement.textContent = ['radio', 'checkbox'].includes(original.type)
                ? (original.checked ? '[x] ' : '[ ] ') : original.value;
            copy.replaceWith(replacement);
        }
        if (original.tagName === 'TEXTAREA' || original.tagName === 'SELECT') {
            const replacement = document.createElement('span');
            replacement.textContent = original.tagName === 'SELECT'
                ? [...original.selectedOptions].map(option => option.textContent).join(', ') : original.value;
            copy.replaceWith(replacement);
        }
        if (original.tagName === 'BUTTON') copy.setAttribute('disabled', '');
        if (original.tagName === 'A' && /^https?:/.test(original.href)) {
            copy.setAttribute('href', original.href);
            copy.setAttribute('rel', 'noreferrer');
        }
        const background = computed.backgroundImage.match(/^url\(["']?(.*?)["']?\)$/);
        if (background) {
            const replacement = document.createElement('img');
            replacement.src = image(new URL(background[1], document.baseURI).href);
            replacement.alt = 'Content background image';
            copy.prepend(replacement);
        }
    }
    if (root.matches('iframe, embed, object')) warnings.push('The selected area is an embedded document, not HTML questions.');
    if (clone.querySelector('iframe, embed, object')) warnings.push('Embedded documents were omitted; select HTML content inside the frame, or use the official PDF download.');
    clone.querySelectorAll('script, style, link, meta, base, iframe, embed, object, video, audio, source').forEach(element => element.remove());
    if (root.matches('script, style, iframe, embed, object')) return {markup: '', assets: [], warnings};
    return {markup: clone.outerHTML, assets, warnings};
}"""


def capture_region(region, page):
    snapshot = region.evaluate(SNAPSHOT)
    replacements = {}
    for asset in snapshot['assets']:
        source = asset['source']
        if source.startswith('data:image/'):
            replacements[asset['token']] = source
            continue
        try:
            if source.startswith('blob:'):
                data_url = region.evaluate("""async (root, source) => {
                    const response = await fetch(source);
                    const blob = await response.blob();
                    return await new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    });
                }""", source)
            else:
                if urlparse(source).scheme not in ('http', 'https'):
                    raise ValueError('unsupported image URL')
                response = page.context.request.get(
                    source, headers={'Referer': page.url}, timeout=30000
                )
                if not response.ok:
                    raise ValueError(f'HTTP {response.status}')
                content_type = response.headers.get('content-type', '').split(';')[0].strip()
                if not content_type.startswith('image/'):
                    raise ValueError(f'not an image ({content_type})')
                encoded = base64.b64encode(response.body()).decode('ascii')
                data_url = f'data:{content_type};base64,{encoded}'
                response.dispose()
            replacements[asset['token']] = data_url
        except Exception as error:
            replacements[asset['token']] = source
            snapshot['warnings'].append(f'Image could not be embedded ({error}); kept its original URL.')
    markup = snapshot['markup']
    for token, source in replacements.items():
        markup = markup.replace(f'"{token}"', f'"{html.escape(source, quote=True)}"')
    return markup, snapshot['warnings']


def write_export(output, sections, source_url):
    body = '\n'.join(
        f'<section><h2>Capture {index}</h2>{section}</section>'
        for index, section in enumerate(sections, start=1)
    )
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: https: http:; style-src 'unsafe-inline'; font-src 'none'; base-uri 'none'; form-action 'none'">
<title>Lesson Questions</title>
<style>
body {{ max-width: 960px; margin: 32px auto; padding: 0 20px; font: 17px/1.6 Georgia, serif; color: #171717; background: #fff; }}
section {{ border-top: 1px solid #bbb; padding: 20px 0; overflow-wrap: anywhere; }}
img, svg {{ max-width: 100%; height: auto; }}
table {{ max-width: 100%; border-collapse: collapse; display: block; overflow-x: auto; }}
td, th {{ border: 1px solid #bbb; padding: 6px; }}
button {{ color: inherit; background: transparent; border: 0; font: inherit; text-align: left; }}
pre {{ white-space: pre-wrap; }}
@media print {{ body {{ max-width: none; margin: 0; }} section {{ break-inside: avoid; }} }}
</style></head><body><h1>Lesson Questions</h1>
<p>Source: <a href="{html.escape(source_url, quote=True)}">Course lesson</a></p>
{body}
</body></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default=DEFAULT_URL)
    parser.add_argument('--output', type=Path, default=Path('questions.html'))
    parser.add_argument('--profile', type=Path, default=Path.home() / '.rbi-question-export-browser')
    parser.add_argument('--selector', help='CSS selector for exactly one question container; otherwise use the area picker')
    parser.add_argument('--frame-url', help='Unique URL substring of an iframe containing the questions')
    parser.add_argument('--collect', action='store_true', help='Capture multiple screens into the same file')
    parser.add_argument('--screenshot', action='store_true', help='Save the selected rendered region as an image, useful for PDF viewers')
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        parser.exit(1, 'Install Playwright first: python -m pip install -r tools/requirements.txt\n')

    sections = []
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(args.profile.resolve()), headless=False, viewport={'width': 1440, 'height': 1000}
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(args.url, wait_until='domcontentloaded', timeout=60000)
            print('Sign in directly in the browser, open the questions, and scroll to load their images.')
            print('Only capture content you are authorized to access. No access controls are bypassed.')
            while True:
                command = input('Press Enter when ready to capture, or type done to finish: ').strip().lower()
                if command == 'done':
                    break
                frame = page.main_frame
                if args.frame_url:
                    matches = [candidate for candidate in page.frames if args.frame_url in candidate.url]
                    if len(matches) != 1:
                        print(f'Expected one matching frame, found {len(matches)}. Open the lesson and try again.')
                        continue
                    frame = matches[0]
                if args.selector:
                    region = frame.locator(args.selector)
                    if region.count() != 1:
                        print(f'Selector matched {region.count()} elements; choose a unique container.')
                        continue
                else:
                    print('In the browser, click the questions, adjust the outline, then press Enter.')
                    region = frame.evaluate_handle(PICK_REGION)
                    if region.as_element() is None:
                        region.dispose()
                        print('Selection cancelled.')
                        continue
                try:
                    if args.screenshot:
                        element = region if args.selector else region.as_element()
                        encoded = base64.b64encode(element.screenshot(type='png')).decode('ascii')
                        markup = f'<img src="data:image/png;base64,{encoded}" alt="Captured questions">'
                        warnings = []
                    else:
                        markup, warnings = capture_region(region, page)
                finally:
                    if not args.selector:
                        region.dispose()
                for warning in warnings:
                    print(f'Warning: {warning}')
                if not markup:
                    print('No HTML content captured. Open the questions or use the official document download.')
                    continue
                sections.append(markup)
                write_export(args.output, sections, args.url)
                print(f'Saved {len(sections)} capture(s) to {args.output.resolve()}')
                if not args.collect:
                    break
                print('Navigate to the next question/screen before capturing again.')
        finally:
            context.close()


if __name__ == '__main__':
    main()