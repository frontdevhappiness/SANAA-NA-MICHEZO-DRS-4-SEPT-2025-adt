# Kore narration — Sanaa na Michezo

The website is this repository's root; its language is `sw-TZ`. The current
audit finds 2,997 audio IDs and 2,076 distinct narration jobs, including easy-read,
glossary, activity and image-description audio. The scripts are adapted from the
Afya workspace referenced in the supplied guide. Kore narration and new word timings were installed on 2026-09-13.

All 2,075 original migration recordings passed checksum, MP3 decoding and measured-timing
validation, covering 2,997 mapped IDs. Feature flags, page content, sign-video
mappings and decorative-symbol exclusions were preserved. Post-install tests
and local HTTP resource checks passed. Browser playback/listening still needs
user review; headless Chromium was unavailable because of a local library error.

The original reader backup is
`.kore-tts/reader-backup-20260913-121756-317176/`.
The installed audio, timings and reusable scripts are included in the Kore installation commit.
No push or export was performed.

## Pronunciation correction installed

The 62 affected recordings were regenerated and installed with measured timings.
Pencil grades use “mbili B” and “nne B”; Roman list numbers use “moja”, “mbili”,
and the corresponding Swahili cardinal numbers. The two alphabetical lists retain
letter “i” through `kore_narration_id_overrides.json`. Different meanings of the
same printed label now use separate audio files, bringing the current total to
2,076 recordings. Printed text, sign-video mappings and decorative exclusions
are unchanged. Validation and post-install tests passed.

Backup before this correction:
`.kore-tts/reader-backup-20260913-133756-161271/`.
These pronunciation corrections are included in the pencil-grade and Roman-numeral pronunciation commit.

## Letter-only labels installed

The 15 replacement recordings for alphabetical labels were installed with new
measured timings. Their narration contains only the letter, without “Kipengele”
or “Herufi”. Alphabetical “i” remains separate from Roman “i” (moja); the Roman
number and pencil-grade corrections remain intact. All 2,076 recordings passed
installation validation, and all 21 local regression tests passed.

Backup before this update:
`.kore-tts/reader-backup-20260913-140434-539552/`.
This update is included in the English-letter pronunciation commit. Listen to the labels after a browser hard refresh.

The subsequent English-letter clarification is now installed:
alphabetical labels now request English names (for example h = aitch, g = jee,
i = eye). A label-specific language option avoids the normal Swahili prompt for
these clips. All 19 replacement recordings were generated and aligned, reusing
2,057 recordings. Installation validated all 2,076 recordings and timings;
all 21 regression tests passed. Roman numerals and pencil-grade narration are
unchanged. Backup: `.kore-tts/reader-backup-20260913-141737-458357/`.
The English-letter update is included in the English-letter pronunciation commit; browser listening remains to be reviewed.

## Generate and review three samples first

Run from the workspace root in the VS Code terminal:

```bash
python3 scripts/generate_kore_audio.py --dry-run --samples
python3 scripts/generate_kore_audio.py --samples
```

The second command uses `GEMINI_API_KEY` or `GOOGLE_API_KEY` if set; otherwise it
asks for a key without displaying or saving it. Do not paste the key into chat.
It does not read `.env` files. It sends the selected narration to the Gemini API
at `generativelanguage.googleapis.com`, using your key's account and quota.
It does not use the old Google Cloud project's credentials.

The default model is `gemini-3.1-flash-tts-preview` with voice `Kore`. API/model
access was verified during the completed generation runs. Python 3 and ffmpeg are available here.
Generation uses Python's standard library and requires network access.

Samples are `pg002_n0013` (telephone number), `pg008_n0006` (sentence), and
`pg001_im001` (image description). With Live Server on port 5500, open:

<http://127.0.0.1:5500/.kore-tts/gemini-3.1-flash-tts-preview/review.html>

Use your actual server port. The preview appears after generation starts. Listen
for Tanzanian Swahili, exact wording, numbers, pace and pauses before approving
full generation. `+255` is spoken as “jumlisha mbili tano tano”. Phone digits
are expanded without changing displayed text. Overrides translate the existing
`true`/`false` narration labels as “Kweli”/“Si kweli”; no other book's overrides
were copied. Overrides and added spoken words must be checked in alignment.

## Resume generation after sample review

```bash
python3 scripts/generate_kore_audio.py --all
python3 scripts/generate_kore_audio.py --all --retry-errors
```

Ctrl+C stops after preserving completed checkpoints. Checksums are checked on
resume. Failed clips remain in `pending.json`; explicit content rejections are
not retried automatically. Authentication/configuration failures are recorded and stop the run. Timeouts
and malformed audio receive bounded retries, then remain pending while the batch
continues. `--all` also retries existing nonblocked failures. `--ids ID1 ID2` selects additional
passages. `--limit` bounds new requests; selected completed clips are skipped.
Staging, checkpoints, preview, environments and models live in ignored `.kore-tts/`.

## Measure new highlighting timings

After sample approval, install alignment dependencies into an isolated environment:

```bash
python3 -m venv .kore-tts/alignment-env
.kore-tts/alignment-env/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
.kore-tts/alignment-env/bin/pip install stable-ts faster-whisper
.kore-tts/alignment-env/bin/python scripts/align_kore_audio.py --backend faster --limit 3
```

Alignment was completed using the existing Afya CPU alignment environment and
models copied into this workspace. The commands above prepare a fresh environment
when needed; the partially prepared local environment is not required for playback.
Alignment uses `sw` and measures boundaries from audio; it never copies old timings
or invents evenly spaced timestamps. It skips ungenerated clips, preserves failure
records and prevents simultaneous alignment writers. Phone expansions are grouped
back to displayed word indices. Other mismatches remain failures for review.

After generation, align all remaining recordings and review unresolved clips:

```bash
.kore-tts/alignment-env/bin/python scripts/align_kore_audio.py --backend faster
.kore-tts/alignment-env/bin/python scripts/align_kore_audio.py --backend faster --model small --failed-from base --missing-only
```

Forced alignment estimates boundaries; it is not proof that Gemini pronounced
every word correctly. Listen to difficult cases and test highlighting in the reader.
If selecting another generation model, use `--model NAME` on the generator and
`--tts-model NAME` on both aligner and installer, so all use the same staging folder.

## Install only after generation, timing validation and review

```bash
python3 scripts/install_kore_audio.py --check
python3 scripts/install_kore_audio.py
```

The installer rejects incomplete generation, changed narration plans, corrupt audio,
missing timings, invalid word order/duration and missing existing IMS resources.
It creates a complete reader backup under `.kore-tts/reader-backup-*` and restores
the changed files on installation/check failure.

It preserves existing audio filenames except where different texts shared a
recording: `pg079_n0010` and its easy-read alias say “4.” but previously shared
`pg001_n0012_easy_read.mp3` with “Jina la chapisho: Nne”. Those receive distinct
Kore filenames. Old `#t=...` audio offsets are removed because new recordings have
different pacing. Unmapped audio and timing entries are retained.

This workspace has no README, deployment scripts, or reusable release-check scripts.
Its offline mechanism embeds data in `assets/offline-preloader.js`, rather than
using a service worker. Installation changes only recordings, audio mappings,
measured word timings, `bundleVersion`, the corresponding embedded offline data,
and IMS file entries for newly named audio. It preserves the preloader's JavaScript.
Hashes check all other existing reader files, including pages, videos and video
metadata. Feature flags, sign-language logic and compiled runtime remain intact.

After installation, hard-refresh the browser and manually test normal/easy-read
narration, glossary, images, exercises, synchronized highlighting and sign videos.
Test the existing offline workflow too. Reusing filenames requires clearing an old
browser cache if a hard refresh still serves previous audio. Offline embedded data and local HTTP resources passed post-install checks.
Interactive browser playback and listening should still be reviewed after refresh.

## Local verification

```bash
python3 scripts/test_kore_audio.py
python3 scripts/generate_kore_audio.py --dry-run --samples
git diff --check
```

Tests use local fixtures and mocks; they verify format parsing, measured-word mapping,
the actual alias/offset plan, and installer preservation/rollback. They do not make
API calls or assess generated pronunciation. The scripts do not push, commit or export.

References: [Gemini TTS](https://ai.google.dev/gemini-api/docs/generate-content/speech-generation),
[stable-ts](https://github.com/jianfch/stable-ts),
[faster-whisper](https://github.com/SYSTRAN/faster-whisper).
