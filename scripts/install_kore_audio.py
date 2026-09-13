#!/usr/bin/env python3
"""Validate and install staged Kore audio while preserving reader mappings and features."""
import argparse
import concurrent.futures
import datetime
import fcntl
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

from align_kore_audio import tokens
from generate_kore_audio import plan, installation_mapping

ROOT = Path(__file__).resolve().parents[1]
LANG = Path('content/i18n/sw-TZ')
TIMINGS = LANG / 'timecode/timecode_output.json'
MAPPING = LANG / 'audios.json'
CONFIG = Path('assets/config.json')
OFFLINE = Path('assets/offline-preloader.js')
MANIFEST = Path('imsmanifest.xml')


def read(path):
    return json.loads(path.read_text())


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def audio_duration(audio):
    for attempt in range(3):
        try:
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-threads', '1',
                            '-i', str(audio), '-f', 'null', '-'],
                           check=True, capture_output=True, timeout=90)
            return float(subprocess.check_output(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=nw=1:nk=1', str(audio)], text=True, stderr=subprocess.PIPE, timeout=30))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            if attempt == 2:
                raise
            print(f'Retrying media validation for {audio.name} ({attempt + 2}/3).', flush=True)
            time.sleep(1)


def inline_data(source):
    marker = 'var INLINE = '
    start = source.index(marker) + len(marker)
    data, length = json.JSONDecoder().raw_decode(source[start:])
    return data, start, start + length


def protected_files(root):
    # Hash all existing reader files, including sign videos and their metadata.
    excluded = {'.git', '.kore-tts', '.adt-tts-work', 'tts_samples', 'scripts', '__pycache__'}
    changed = {TIMINGS, CONFIG, OFFLINE, MAPPING, MANIFEST}
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts) or not path.is_file():
            continue
        if relative in changed or relative.is_relative_to(LANG / 'audio'):
            continue
        yield relative, digest(path)


def validate(stage, model):
    jobs, proposed = plan(model)
    if read(stage / 'transcripts.json') != jobs or read(stage / 'audios.proposed.json') != proposed:
        raise ValueError('Narration plan changed; rerun generation before installation')
    completed = read(stage / 'completed.json')
    # Existing #t offsets trim the old recordings and cannot apply to the new voice.
    mapping = installation_mapping(read(ROOT / MAPPING), proposed, read(ROOT / LANG / 'texts.json'))
    missing = set(jobs) - completed.keys()
    if missing:
        raise ValueError(f'{len(missing)} clips are incomplete; installation refused')
    # Independent media checks run in a small bounded pool; mutations remain sequential.
    durations = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for index, (name, duration) in enumerate(zip(jobs, pool.map(
                audio_duration, (stage / 'audio' / name for name in jobs))), 1):
            durations[name] = duration
            if index % 250 == 0 or index == len(jobs):
                print(f'Decoded {index}/{len(jobs)} recordings.', flush=True)
    measured = {}
    for index, (name, job) in enumerate(jobs.items(), 1):
        expected = completed[name]['sha256']
        audio = stage / 'audio' / name
        if digest(audio) != expected:
            raise ValueError('Audio checksum mismatch: ' + name)
        duration = durations[name]
        timing = None
        for alignment in ('small', 'base'):
            path = stage / ('alignment-' + alignment) / (Path(name).stem + '.json')
            if path.exists():
                candidate = read(path)
                if candidate.get('sha256') == expected:
                    timing = candidate['word_timestamps']
                    break
        if not timing or [w['text'] for w in timing] != tokens(job['text']):
            raise ValueError('Missing or mismatched measured timings: ' + job['ids'][0])
        previous = 0
        for word in timing:
            start, end = word['start'], word['end']
            if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= duration + .1):
                raise ValueError('Invalid measured timing: ' + name)
            if start < previous - .03:
                raise ValueError('Overlapping word timing: ' + name)
            previous = end
        measured[name] = {'timecodes': [None, {'word_timestamps': timing}]}
        if index % 250 == 0 or index == len(jobs):
            print(f'Validated {index}/{len(jobs)} recordings and timings.', flush=True)
    # Keep unmapped legacy entries; replace every active mapped ID with new timings.
    timings = read(ROOT / TIMINGS)
    timings.update({text_id: measured[name] for text_id, name in proposed.items()})
    for element in ET.parse(ROOT / 'imsmanifest.xml').iter():
        if element.tag.endswith('}file') and not (ROOT / element.attrib['href']).is_file():
            raise ValueError('Missing IMS resource: ' + element.attrib['href'])
    return mapping, proposed, timings


def install(stage, model, check=False):
    mapping, proposed, timings = validate(stage, model)
    source = (ROOT / OFFLINE).read_text()
    embedded, start, end = inline_data(source)
    config = read(ROOT / CONFIG)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    config['bundleVersion'] = str(config['bundleVersion']) + '-kore-' + stamp
    for relative, value in ((TIMINGS, timings), (CONFIG, config), (MAPPING, mapping)):
        key = './' + relative.as_posix()
        if key not in embedded:
            raise ValueError('Expected offline entry is missing: ' + key)
        embedded[key] = value
    updated = source[:start] + json.dumps(embedded, ensure_ascii=True, separators=(',', ':')) + source[end:]
    manifest = (ROOT / MANIFEST).read_text()
    known = {e.attrib.get('href') for e in ET.fromstring(manifest).iter()}
    added = sorted({(LANG / 'audio' / f).as_posix() for f in mapping.values()
                    if not (ROOT / LANG / 'audio' / f).exists()} - known)
    if added:
        manifest = manifest.replace('</resource>', ''.join(f'<file href="{f}"/>\n' for f in added) + '</resource>', 1)
    if check:
        print(f'Validated {len(proposed)} IDs. Reader unchanged.')
        return
    protected = dict(protected_files(ROOT))
    backup = ROOT / '.kore-tts' / ('reader-backup-' + stamp)
    # Full reader backup; ignore development/staging directories to avoid recursion.
    shutil.copytree(ROOT, backup, ignore=shutil.ignore_patterns(
        '.git', '.kore-tts', '.adt-tts-work', 'tts_samples', '__pycache__', '.env', '.env.*'))
    try:
        for text_id, filename in mapping.items():
            target = ROOT / LANG / 'audio' / filename
            temp = target.with_suffix('.kore-tmp')
            shutil.copy2(stage / 'audio' / proposed[text_id], temp)
            temp.replace(target)
        (ROOT / TIMINGS).write_text(json.dumps(timings, ensure_ascii=False) + '\n')
        (ROOT / MAPPING).write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n')
        (ROOT / CONFIG).write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
        (ROOT / OFFLINE).write_text(updated)
        (ROOT / MANIFEST).write_text(manifest)
        if dict(protected_files(ROOT)) != protected:
            raise ValueError('An unrelated reader file changed')
        for text_id, filename in mapping.items():
            if digest(ROOT / LANG / 'audio' / filename) != digest(stage / 'audio' / proposed[text_id]):
                raise ValueError('Installed audio mismatch: ' + text_id)
        actual, _, _ = inline_data((ROOT / OFFLINE).read_text())
        if actual != embedded:
            raise ValueError('Offline data verification failed')
        subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
    except BaseException:
        shutil.copytree(backup / LANG / 'audio', ROOT / LANG / 'audio', dirs_exist_ok=True)
        for relative in (TIMINGS, CONFIG, OFFLINE, MAPPING, MANIFEST):
            shutil.copy2(backup / relative, ROOT / relative)
        # Remove newly installed files that did not exist before installation.
        for filename in set(mapping.values()):
            if not (backup / LANG / 'audio' / filename).exists():
                (ROOT / LANG / 'audio' / filename).unlink(missing_ok=True)
            (ROOT / LANG / 'audio' / filename).with_suffix('.kore-tmp').unlink(missing_ok=True)
        raise
    print('Installed Kore audio and timings. Backup:', backup)
    print('Hard-refresh the browser; review highlighting and offline playback before sharing.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--tts-model', default='gemini-3.1-flash-tts-preview')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9._-]+', args.tts_model):
        parser.error('Invalid model name')
    stage = ROOT / '.kore-tts' / args.tts_model
    if not (stage / 'completed.json').exists():
        parser.error('No completed generation checkpoint; generate and align audio first')
    with (stage / 'run.lock').open('w') as generation_lock, (stage / 'alignment.lock').open('w') as alignment_lock:
        for lock in (generation_lock, alignment_lock):
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        install(stage, args.tts_model, args.check)


if __name__ == '__main__':
    main()
