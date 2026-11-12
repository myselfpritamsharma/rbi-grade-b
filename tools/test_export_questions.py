import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from playwright.sync_api import sync_playwright

from export_questions import capture_region, write_export


class ExportQuestionsTest(unittest.TestCase):
    def test_questions_options_images_and_offline_html(self):
        picture = (
            'data:image/svg+xml;base64,'
            'PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMCIg'
            'aGVpZ2h0PSIxMCI+PHJlY3Qgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiBmaWxsPSJyZWQi'
            'Lz48L3N2Zz4='
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_content(
                    '<div id="question"><p>What is 2 + 2?</p>'
                    '<label><input type="radio" checked>4</label>'
                    '<label><input type="radio">5</label>'
                    + f'<img src="{picture}" alt="Diagram">' * 12
                    + '<script>window.example = true</script>'
                    '<span style="display:none">Hidden answer</span></div>'
                )
                markup, warnings = capture_region(page.locator('#question'), page)
                self.assertIn('What is 2 + 2?', markup)
                self.assertIn('[x] ', markup)
                self.assertIn('[ ] ', markup)
                self.assertNotIn('EXPORT_ASSET_', markup)
                self.assertNotIn('<script', markup)
                self.assertNotIn('Hidden answer', markup)
                self.assertEqual(warnings, [])
                with TemporaryDirectory() as directory:
                    output = Path(directory) / 'questions.html'
                    write_export(output, [markup, markup], 'https://example.com/?a=1&b=2')
                    self.assertIn('a=1&amp;b=2', output.read_text(encoding='utf-8'))
                    page.goto(output.as_uri())
                    self.assertEqual(page.locator('section').count(), 2)
                    self.assertEqual(page.locator('img').count(), 24)
                    self.assertTrue(page.locator('img').evaluate_all(
                        '(images) => images.every(image => image.complete && image.naturalWidth > 0)'
                    ))
                    self.assertTrue(page.locator('section').first.screenshot(type='png').startswith(b'\x89PNG'))
            finally:
                browser.close()


if __name__ == '__main__':
    unittest.main()