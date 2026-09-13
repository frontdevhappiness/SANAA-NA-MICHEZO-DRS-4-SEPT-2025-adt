"""Check sign videos against section identity and the offline reader data."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SignVideoMappingTests(unittest.TestCase):
    def test_content_pages_and_covers(self):
        pages = json.loads((ROOT / 'content/pages.json').read_text())
        videos = json.loads((ROOT / 'content/i18n/sw-TZ/videos.json').read_text())
        metadata = json.loads((ROOT / 'content/video-import-metadata.json').read_text())['videos']
        expected = set()
        for index, page in enumerate(pages, 1):
            with self.subTest(section=page['section_id']):
                html = (ROOT / page['href']).read_text()
                position = re.search(r'name="page-section-id"\s+content="(\d+)"', html)
                self.assertEqual(int(position[1]), index)
                key = f'video-{index}'
                expected.add(key)
                self.assertEqual(metadata[key]['section_id'], page['section_id'])
                self.assertEqual(videos[key], f"sl_{page['section_id']}.mp4")
                self.assertEqual(videos[key], metadata[key]['filename'])
                video = ROOT / 'content/i18n/sw-TZ/video' / videos[key]
                self.assertTrue(video.is_file())
                if page['section_id'] in ('cover_sec001', 'back_cover_sec001'):
                    self.assertLess(video.stat().st_size, 5_000_000)
                    self.assertEqual(metadata[key]['audio_mode'], 'remove')
        self.assertEqual(set(videos), expected)
        self.assertEqual(set(metadata), expected)

    def test_offline_mapping_matches(self):
        source = (ROOT / 'assets/offline-preloader.js').read_text()
        inline, _ = json.JSONDecoder().raw_decode(source.split('var INLINE = ', 1)[1])
        videos = json.loads((ROOT / 'content/i18n/sw-TZ/videos.json').read_text())
        self.assertEqual(inline['./content/i18n/sw-TZ/videos.json'], videos)


if __name__ == '__main__':
    unittest.main()
