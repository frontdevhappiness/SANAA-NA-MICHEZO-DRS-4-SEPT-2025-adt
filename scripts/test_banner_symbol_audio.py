"""Decorative banner symbols stay visible but are absent from the TTS selector."""
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


class BannerSymbolAudioTests(unittest.TestCase):
    def test_offline_symbols_match_pages(self):
        source = (ROOT / 'assets/offline-preloader.js').read_text()
        inline, _ = json.JSONDecoder().raw_decode(source.split('var INLINE = ', 1)[1])
        for page in ROOT.glob('pg*.html'):
            parser = Elements()
            parser.feed(page.read_text())
            symbols = [attrs for tag, attrs in parser.items if 'data-decorative-id' in attrs]
            if not symbols:
                continue
            cached = Elements()
            cached.feed(inline['./' + page.name])
            self.assertEqual(symbols, [attrs for tag, attrs in cached.items if 'data-decorative-id' in attrs])

    def test_symbols_are_visible_and_not_playable(self):
        count = 0
        for page in ROOT.glob('pg*.html'):
            parser = Elements()
            parser.feed(page.read_text())
            for tag, attrs in parser.items:
                if 'data-decorative-id' not in attrs:
                    continue
                with self.subTest(page=page.name, image=attrs['data-decorative-id']):
                    count += 1
                    self.assertEqual(tag, 'img')
                    self.assertNotIn('data-id', attrs)
                    self.assertEqual(attrs.get('aria-hidden'), 'true')
                    self.assertEqual(attrs.get('role'), 'presentation')
                    self.assertEqual(attrs.get('alt'), '')
                    self.assertNotIn('hidden', attrs.get('class', '').split())
                    self.assertNotIn('hidden', attrs)
                    self.assertTrue((ROOT / attrs['src']).is_file())
        self.assertEqual(count, 37)


if __name__ == '__main__':
    unittest.main()
