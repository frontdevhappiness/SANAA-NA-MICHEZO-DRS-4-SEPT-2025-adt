#!/usr/bin/env python3
"""Measure word timings from staged Kore audio without changing the reader."""
import argparse
import fcntl
import difflib
import hashlib
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / '.kore-tts/gemini-3.1-flash-tts-preview'
WORDS = re.compile(r'[^\W_]+(?:[’\'-][^\W_]+)*', re.UNICODE)


def tokens(text):
    return WORDS.findall(text)


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def display_timings(text, narration, aligned):
    """Map measured spoken words onto the reader's original word indices."""
    source = tokens(text)
    spoken = tokens(narration)
    timed = []
    for word in aligned:
        parts = tokens(word['word'])
        if len(parts) > 1:
            raise ValueError('Aligner combined multiple display words; needs review')
        if parts:
            timed.append({'text': parts[0], 'start': word['start'], 'end': word['end']})
    if [w['text'].casefold() for w in timed] != [w.casefold() for w in spoken]:
        raise ValueError('Aligned words differ from narration tokens')
    result = [None] * len(source)
    if text.lstrip().lower().startswith('simu:'):
        # Phone groups are spoken digit-by-digit; preserve each printed group's index.
        position = 0
        for i, word in enumerate(source):
            if i == 0:
                size = 1
            else:
                if position < len(timed) and timed[position]['text'].lower() == 'au':
                    position += 1
                size = len(word) if word.isdigit() else 1
                if position < len(timed) and timed[position]['text'].lower() == 'jumlisha':
                    size += 1
            selected = timed[position:position + size]
            if len(selected) != size:
                raise ValueError('Phone alignment token mismatch')
            result[i] = {'text': word, 'start': selected[0]['start'], 'end': selected[-1]['end']}
            position += size
        if position != len(timed):
            raise ValueError('Unmapped phone narration words')
    else:
        matcher = difflib.SequenceMatcher(None, [w.casefold() for w in source],
                                          [w.casefold() for w in spoken], autojunk=False)
        for kind, a, b, c, d in matcher.get_opcodes():
            if kind == 'equal':
                for i, j in zip(range(a, b), range(c, d)):
                    result[i] = {**timed[j], 'text': source[i]}
            elif kind == 'insert':
                continue  # Context labels such as "Kipengele" are not printed words.
            elif kind == 'replace' and b - a == 1 and d > c:
                result[a] = {'text': source[a], 'start': timed[c]['start'], 'end': timed[d-1]['end']}
            else:
                raise ValueError('Narration/display differences need explicit mapping')
    if not result or any(w is None or w['end'] <= w['start'] for w in result):
        raise ValueError('Missing or zero-duration word timing')
    if any(a['end'] > b['start'] + .03 for a, b in zip(result, result[1:])):
        raise ValueError('Overlapping word timings')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tts-model', default='gemini-3.1-flash-tts-preview')
    parser.add_argument('--ids', nargs='+', help='Align only selected text IDs for a sample check')
    parser.add_argument('--model', default='base')
    parser.add_argument('--limit', type=int, default=0, help='0 means all remaining')
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--backend', choices=['torch', 'faster'], default='torch')
    parser.add_argument('--missing-only', action='store_true',
                        help='Skip timings already measured by another model')
    parser.add_argument('--failed-from', choices=['base', 'small'],
                        help='Process only the failures recorded by this model')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9._-]+', args.tts_model) or not re.fullmatch(r'[A-Za-z0-9._-]+', args.model):
        parser.error('Invalid model name')
    global STAGE
    STAGE = ROOT / '.kore-tts' / args.tts_model
    STAGE.mkdir(parents=True, exist_ok=True)
    lock = (STAGE / 'alignment.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('Another alignment run is active')
    import torch
    import stable_whisper
    torch.set_num_threads(args.threads)
    jobs = json.loads((STAGE / 'transcripts.json').read_text())
    if args.ids:
        selected = set(args.ids)
        known = {text_id for job in jobs.values() for text_id in job['ids']}
        if selected - known:
            parser.error('Unknown text IDs: ' + ', '.join(sorted(selected - known)))
        jobs = {name: job for name, job in jobs.items() if selected.intersection(job['ids'])}
    if args.failed_from:
        failed = json.loads((STAGE / ('alignment-' + args.failed_from) / 'failures.json').read_text())
        jobs = {name: job for name, job in jobs.items() if name in failed}
    completed = json.loads((STAGE / 'completed.json').read_text())
    output = STAGE / ('alignment-' + args.model)
    output.mkdir(exist_ok=True)
    print('Loading alignment model ' + args.model, flush=True)
    if args.backend == 'faster':
        model = stable_whisper.load_faster_whisper(args.model, device='cpu',
            compute_type='int8', cpu_threads=args.threads,
            download_root=str(ROOT / '.kore-tts/models-faster'))
    else:
        model = stable_whisper.load_model(args.model, device='cpu',
                                         download_root=str(ROOT / '.kore-tts/models'))
    failure_path = output / 'failures.json'
    failures = json.loads(failure_path.read_text()) if failure_path.exists() else {}
    count, start = 0, time.monotonic()
    for name, job in jobs.items():
        if name not in completed:
            continue
        target = output / (Path(name).stem + '.json')
        expected_hash = completed[name]['sha256']
        if target.exists():
            previous = json.loads(target.read_text())
            if previous.get('sha256') == expected_hash:
                continue
        if args.missing_only:
            existing = [p for p in STAGE.glob('alignment-*/' + Path(name).stem + '.json')
                        if json.loads(p.read_text()).get('sha256') == expected_hash]
            if existing:
                continue
        if args.limit and count >= args.limit:
            break
        audio = STAGE / 'audio' / name
        if hashlib.sha256(audio.read_bytes()).hexdigest() != expected_hash:
            raise ValueError('Changed audio: ' + name)
        count += 1
        words = []
        try:
            # Separate punctuation-delimited display words (e.g. website addresses)
            # before alignment so each receives its own measured boundary.
            alignment_text = ' '.join(tokens(job['narration']))
            result = model.align(str(audio), alignment_text, language='sw', stream=False,
                                 verbose=None, regroup=False, fast_mode=True)
            if result is None:
                raise ValueError('Alignment returned no words')
            words = [w for segment in result.to_dict()['segments'] for w in segment['words']]
            displayed = display_timings(job['text'], job['narration'], words)
            duration = completed[name]['seconds']
            if displayed[-1]['end'] > duration + .1 or displayed[0]['start'] < 0:
                raise ValueError('Timing exceeds audio duration')
            save(target, {'sha256': expected_hash, 'model': args.model,
                          'word_timestamps': displayed, 'spoken_words': words})
            failures.pop(name, None)
            print(f'Aligned {count}: {job["ids"][0]} ({time.monotonic()-start:.1f}s elapsed)', flush=True)
        except ValueError as error:
            failures[name] = {'ids': job['ids'], 'error': str(error), 'spoken_words': words}
            print(f'Review: {job["ids"][0]}: {error}', flush=True)
        save(output / 'failures.json', failures)
    print('Alignment pass finished. Reader unchanged.', flush=True)


if __name__ == '__main__':
    main()
