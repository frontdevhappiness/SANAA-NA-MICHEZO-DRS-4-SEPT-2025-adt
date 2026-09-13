"""Offline regression checks for narration planning, timings and safe installation."""
import base64
import contextlib
import io
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import align_kore_audio as align
import generate_kore_audio as generate
import install_kore_audio as installer


class KoreTests(unittest.TestCase):
    def test_roman_and_pencil_pronunciation(self):
        jobs, mapping = generate.plan('gemini-3.1-flash-tts-preview')
        self.assertEqual(jobs[mapping['pg026_n0033']]['narration'], 'moja')
        self.assertEqual(jobs[mapping['pg026_n0003']]['narration'], 'mbili')
        self.assertEqual(jobs[mapping['pg039_n0014']]['narration'], 'i')
        self.assertEqual(jobs[mapping['pg070_n0039_easy_read']]['narration'], 'i')
        self.assertIn('mbili B', jobs[mapping['pg025_n0017']]['narration'])
        self.assertIn('nne B', jobs[mapping['pg025_n0017']]['narration'])
        language = generate.ROOT / 'content/i18n/sw-TZ'
        installed = generate.installation_mapping(
            json.loads((language / 'audios.json').read_text()), mapping,
            json.loads((language / 'texts.json').read_text()))
        self.assertNotEqual(installed['pg026_n0033'], installed['pg039_n0014'])

    def test_letter_labels_have_no_spoken_prefix(self):
        overrides = json.loads((generate.ROOT / 'scripts/kore_narration_overrides.json').read_text())
        for letter in 'abcdefghlmno':
            self.assertEqual(overrides[f'({letter})']['narration'], letter)
        for letter in 'ABCDEF':
            self.assertEqual(overrides[letter]['narration'], letter)
        self.assertEqual(overrides['(i)']['narration'], 'moja')
        self.assertEqual(overrides['(ii)']['narration'], 'mbili')
        jobs, mapping = generate.plan('gemini-3.1-flash-tts-preview')
        for job in jobs.values():
            if len(job['narration']) == 1 and job['narration'].isalpha():
                self.assertIn('English alphabet', job['style'])
                self.assertNotIn('Pronounce letter names and numbers in Swahili', job['style'])
        self.assertIn('"eye"', jobs[mapping['pg039_n0014']]['style'])
        self.assertIn('Pronounce letter names and numbers in Swahili',
                      jobs[mapping['pg026_n0033']]['style'])

    def test_adjacent_spoken_expansions_map_to_measured_words(self):
        for text, narration in [('2B 4B', 'mbili B nne B'),
                                ('(i)-(iv)', 'moja hadi nne')]:
            spoken = align.tokens(narration)
            words = [{'word': word, 'start': i, 'end': i + .8} for i, word in enumerate(spoken)]
            result = align.display_timings(text, narration, words)
            self.assertEqual([w['text'] for w in result], align.tokens(text))
            self.assertEqual(result[0]['start'], 0)
            self.assertEqual(result[-1]['end'], words[-1]['end'])

    def test_validation_retries_decoder_crash(self):
        with patch.object(installer.subprocess, 'run', side_effect=[
                subprocess.CalledProcessError(-11, ['ffmpeg']), None]) as decode, \
             patch.object(installer.subprocess, 'check_output', return_value='3.5'), \
             patch.object(installer.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(installer.audio_duration(Path('sample.mp3')), 3.5)
            self.assertEqual(decode.call_count, 2)

    def test_generic_html_400_becomes_pending(self):
        def failure(*args, **kwargs):
            raise generate.urllib.error.HTTPError('https://example.invalid', 400, 'Bad Request', {},
                io.BytesIO(b'<html><title>Error 400 (Bad Request)!!1</title></html>'))
        with patch.object(generate.urllib.request, 'urlopen', side_effect=failure) as request, \
             patch.object(generate.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(generate.RejectedClipError):
                generate.generate('sample', 'model', 'test-key')
            self.assertEqual(request.call_count, 3)

    def test_invalid_key_still_stops(self):
        error = generate.urllib.error.HTTPError('https://example.invalid', 400, 'Bad Request', {},
            io.BytesIO(b'{"error":{"message":"API key not valid"}}'))
        with patch.object(generate.urllib.request, 'urlopen', side_effect=error) as request:
            with self.assertRaises(RuntimeError) as caught:
                generate.generate('sample', 'model', 'test-key')
            self.assertNotIsInstance(caught.exception, generate.RejectedClipError)
            self.assertEqual(request.call_count, 1)

    def test_timeouts_remain_pending_after_bounded_retries(self):
        with patch.object(generate.urllib.request, 'urlopen', side_effect=TimeoutError('read timed out')) as request, \
             patch.object(generate.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(generate.IncompleteAudioError):
                generate.generate('sample', 'model', 'test-key')
            self.assertEqual(request.call_count, 3)

    def test_plain_text_http_error_redacts_key(self):
        error = generate.urllib.error.HTTPError('https://example.invalid', 400, 'Bad Request', {},
                                                io.BytesIO(b'Invalid request: test-secret'))
        with patch.object(generate.urllib.request, 'urlopen', side_effect=error):
            with self.assertRaisesRegex(RuntimeError, r'Invalid request: \[REDACTED\]'):
                generate.generate('sample', 'model', 'test-secret')

    def test_empty_http_400_retries_are_bounded(self):
        def failure(*args, **kwargs):
            raise generate.urllib.error.HTTPError('https://example.invalid', 400, 'Bad Request', {}, io.BytesIO(b''))
        with patch.object(generate.urllib.request, 'urlopen', side_effect=failure) as request, \
             patch.object(generate.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(generate.RejectedClipError):
                generate.generate('sample', 'model', 'test-secret')
            self.assertEqual(request.call_count, 3)

    def test_invalid_base64_retries_then_recovers(self):
        def response(data):
            return io.StringIO(json.dumps({'candidates': [{'finishReason': 'STOP',
                'content': {'parts': [{'inlineData': {'mimeType': 'audio/L16;rate=24000',
                                                     'data': data}}]}}]}))
        with patch.object(generate.urllib.request, 'urlopen', side_effect=[
                response('not!base64'), response('AAA=')]) as request, \
             patch.object(generate.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(generate.generate('sample', 'model', 'test-key'), (b'\0\0', 24000))
            self.assertEqual(request.call_count, 2)

    def test_invalid_base64_retries_are_bounded(self):
        payload = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'inlineData': {'mimeType': 'audio/L16;rate=24000', 'data': 'invalid!'}}]}}]}
        with patch.object(generate.urllib.request, 'urlopen',
                          side_effect=lambda *a, **k: io.StringIO(json.dumps(payload))) as request, \
             patch.object(generate.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(generate.IncompleteAudioError):
                generate.generate('sample', 'model', 'test-key')
            self.assertEqual(request.call_count, 3)

    def test_conversion_recovers_after_abort(self):
        real_run = subprocess.run
        calls = []
        def crash_once(command, **kwargs):
            calls.append(command)
            if len(calls) == 1:
                raise subprocess.CalledProcessError(-6, command, stderr=b'Simulated abort')
            return real_run(command, **kwargs)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'sample.mp3'
            with patch.object(generate.subprocess, 'run', side_effect=crash_once), \
                 patch.object(generate.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
                generate.encode(b'\0\0' * 24000, 24000, target)
            self.assertTrue(target.is_file())
            self.assertGreater(target.stat().st_size, 0)
            self.assertEqual(len(calls), 3)

    def test_conversion_retries_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'sample.mp3'
            with patch.object(generate.subprocess, 'run', side_effect=subprocess.CalledProcessError(-6, ['ffmpeg'])) as run, \
                 patch.object(generate.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(subprocess.CalledProcessError):
                    generate.encode(b'\0\0' * 24000, 24000, target)
            self.assertEqual(run.call_count, 3)
            self.assertFalse(target.exists())

    def test_audio_format_and_incomplete_response(self):
        response = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'inlineData': {'mimeType': 'Audio/L16; rate=24000; channels=1; codec=pcm',
                            'data': base64.b64encode(b'\0\0' * 100).decode()}}
        ]}}]}
        self.assertEqual(generate.parse_audio(response), (b'\0\0' * 100, 24000))
        response['candidates'][0]['finishReason'] = 'MAX_TOKENS'
        with self.assertRaises(RuntimeError):
            generate.parse_audio(response)
        with self.assertRaises(generate.BlockedAudioError):
            generate.parse_audio({'promptFeedback': {'blockReason': 'SAFETY'}})

    def test_phone_measured_word_mapping(self):
        text = 'Simu: +255 735 / 170'
        narration = generate.spoken_text(text)
        self.assertIn('jumlisha mbili tano tano', narration)
        # Synthetic boundaries exercise mapping only, never used for actual audio.
        words = [{'word': w, 'start': i, 'end': i + .8}
                 for i, w in enumerate(align.tokens(narration))]
        timing = align.display_timings(text, narration, words)
        self.assertEqual([w['text'] for w in timing], ['Simu', '255', '735', '170'])
        self.assertEqual(timing[1]['start'], 1)
        self.assertEqual(timing[1]['end'], 4.8)

    def test_existing_alias_and_trim_offsets(self):
        jobs, proposed = generate.plan('gemini-3.1-flash-tts-preview')
        language = generate.ROOT / 'content/i18n/sw-TZ'
        old = json.loads((language / 'audios.json').read_text())
        texts = json.loads((language / 'texts.json').read_text())
        installed = generate.installation_mapping(old, proposed, texts)
        self.assertEqual(set(installed), set(old))
        self.assertNotEqual(installed['pg079_n0010'], installed['pg001_n0012_easy_read'])
        self.assertEqual(installed['pg079_n0010'], installed['pg079_n0010_easy_read'])
        self.assertFalse(any('#' in value for value in installed.values()))
        self.assertEqual(sum(len(job['ids']) for job in jobs.values()), len(old))

    def fixture(self, root):
        files = {
            'index.html': '<html>Unchanged book</html>',
            'content/i18n/sw-TZ/video/sign.mp4': 'unchanged video bytes',
            'content/i18n/sw-TZ/audio/old.mp3': 'original audio bytes',
            str(installer.TIMINGS): '{}',
            str(installer.MAPPING): '{"id":"old.mp3#t=1"}',
            str(installer.CONFIG): '{"bundleVersion":"1","features":{"signLanguage":true}}',
            'imsmanifest.xml': '<manifest><resources><resource><file href="index.html"/></resource></resources></manifest>',
        }
        embedded = {'./' + str(p): json.loads(files[str(p)]) for p in (
            installer.TIMINGS, installer.MAPPING, installer.CONFIG)}
        files[str(installer.OFFLINE)] = 'var INLINE = ' + json.dumps(embedded) + ';\n// preserve runtime'
        for name, data in files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(data)
        stage = root / '.kore-tts/model'
        (stage / 'audio').mkdir(parents=True)
        (stage / 'audio/new.mp3').write_bytes(b'new staged audio')
        return files, stage

    def test_install_and_rollback(self):
        for fail in (False, True):
            with self.subTest(rollback=fail), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                files, stage = self.fixture(root)
                validated = ({'id': 'old.mp3'}, {'id': 'new.mp3'}, {'id': {'timecodes': []}})
                with patch.object(installer, 'ROOT', root), patch.object(installer, 'validate', return_value=validated), \
                     patch.object(installer.subprocess, 'run', side_effect=RuntimeError('check failed') if fail else None), \
                     contextlib.redirect_stdout(io.StringIO()):
                    if fail:
                        with self.assertRaises(RuntimeError):
                            installer.install(stage, 'model')
                    else:
                        installer.install(stage, 'model')
                if fail:
                    for name, original in files.items():
                        self.assertEqual((root / name).read_text(), original)
                else:
                    self.assertEqual((root / 'content/i18n/sw-TZ/audio/old.mp3').read_bytes(), b'new staged audio')
                    self.assertEqual((root / 'index.html').read_text(), files['index.html'])
                    self.assertEqual((root / 'content/i18n/sw-TZ/video/sign.mp4').read_text(), 'unchanged video bytes')
                    self.assertTrue(installer.read(root / installer.CONFIG)['features']['signLanguage'])
                    embedded, _, _ = installer.inline_data((root / installer.OFFLINE).read_text())
                    self.assertEqual(embedded['./' + str(installer.MAPPING)], {'id': 'old.mp3'})


if __name__ == '__main__':
    unittest.main()
