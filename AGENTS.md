# Sanaa na Michezo — ADT Bundle Reference

This document describes the structure of this Accessible Digital Textbook (ADT) bundle. Use it to orient yourself when doing post-processing.

## About This Book

**Sanaa na Michezo** — Kitabu hiki cha **Sanaa na Michezo** ni kitabu cha mwanafunzi wa **Darasa la Nne** kinachotumika **Tanzania Bara**, kikiwa kimeandikwa kwa **Kiswahili** na kuchapishwa na **Taasisi ya Elimu Tanzania**. Kinajikita katika kujenga ujuzi wa msingi wa uigizaji, uimbaji na ala za muziki, uchoraji, ufinyanzi, mazoezi ya viungo, pamoja na michezo ya asili na ya kisasa. Maudhui yake yanaonesha kiwango cha shule ya msingi, yakiwasilishwa kwa mtindo wa vitendo kupitia maelezo, picha, kazi za kufanya na mazoezi, huku yakisisitiza ubunifu, ushirikiano, kujiamini, uzalendo na ukuzaji wa vipaji vya wanafunzi.

- **Source language**: `sw-TZ`
- **Available languages in this bundle**: `sw-TZ`
- **Total pages**: 82
- **Glossary**: yes

## Quick Overview

An ADT bundle is a self-contained, offline-capable web app for reading a book. It has:

- One HTML file per page/section and per quiz
- A localization system (`i18n`) for text, audio, and glossary — keyed by stable IDs
- A `pages.json` manifest that defines reading order
- A shared `assets/` directory with JS runtime, fonts, and UI resources

The `adt/` subdirectory is the self-contained web app. Other top-level files (`.db`, `.pdf`, `images/`, `audio/`, `.cache/`) are pipeline artifacts and not part of the reader.

## Directory Structure

```
SANAA-NA-MICHEZO-DRS-4-SEPT-2025/
├── adt/                              # THE WEB APP
│   ├── index.html                    # Redirects to first page
│   ├── cover.png                     # Book cover image
│   ├── pg001_sec001.html             # Page HTML files (one per section)
│   ├── pg002_sec001.html
│   ├── ...
│   ├── qz001.html                    # Quiz HTML files
│   ├── qz002.html
│   ├── ...
│   │
│   ├── images/                       # Images referenced by page HTML
│   │   ├── pg001_im001.png
│   │   └── pg002_im002.png
│   │
│   ├── content/
│   │   ├── pages.json                # Reading order manifest
│   │   ├── toc.json                  # Table of contents
│   │   ├── tailwind_output.css       # Compiled Tailwind CSS
│   │   ├── navigation/
│   │   │   └── nav.html              # Navigation sidebar fragment
│   │   └── i18n/
│   │       └── {lang}/               # One directory per language: sw-TZ
│   │           ├── texts.json        # All text content (textId → string)
│   │           ├── audios.json       # Audio mappings (textId → mp3 filename)
│   │           ├── videos.json       # Video mappings (currently unused)
│   │           ├── glossary.json     # Glossary entries (word → object)
│   │           └── audio/            # MP3 files for read-aloud / TTS
│   │
│   └── assets/                       # Shared runtime (JS, fonts, icons)
│       ├── config.json               # Book title, languages, feature flags
│       ├── base.bundle.min.js        # Main JS runtime (do not edit)
│       ├── interface.html            # Accessibility sidebar template
│       ├── fonts/                    # Font files
│       ├── libs/fontawesome/         # Icon library
│       ├── modules/                  # JS feature modules (do not edit)
│       ├── sounds/                   # UI feedback sounds
│       └── interface_translations/
│           └── {lang}/
│               └── interface_translations.json
│
├── images/                           # Raw extracted images and page renders (pipeline artifact)
│   ├── pg001_page.png                # Full-page render from PDF (useful for visual reference)
│   ├── pg001_im001.png               # Extracted image from page
│   └── ...
├── audio/                            # Source audio files (pipeline artifact)
│   └── {lang}/                       # TTS audio per language
├── SANAA-NA-MICHEZO-DRS-4-SEPT-2025.db                    # SQLite database (pipeline state)
├── SANAA-NA-MICHEZO-DRS-4-SEPT-2025.pdf                   # Original source PDF
└── config.yaml                       # Pipeline configuration
```

## Page Images (Visual Reference)

The `images/` directory at the top level (outside `adt/`) contains raw renders of each original PDF page. These are useful as visual reference when editing content — you can see exactly what the original page looked like.

Page renders follow the pattern `pg{NNN}_page.png`:

- `images/pg001_page.png`
- `images/pg002_page.png`
- `images/pg003_page.png`
- `images/pg004_page.png`
- `images/pg005_page.png`
- `images/pg006_page.png`
- `images/pg007_page.png`
- `images/pg008_page.png`
- `images/pg009_page.png`
- `images/pg010_page.png`
- `images/pg011_page.png`
- `images/pg012_page.png`
- `images/pg013_page.png`
- `images/pg014_page.png`
- `images/pg015_page.png`
- `images/pg016_page.png`
- `images/pg017_page.png`
- `images/pg018_page.png`
- `images/pg019_page.png`
- `images/pg020_page.png`
- `images/pg021_page.png`
- `images/pg022_page.png`
- `images/pg023_page.png`
- `images/pg024_page.png`
- `images/pg025_page.png`
- `images/pg026_page.png`
- `images/pg027_page.png`
- `images/pg028_page.png`
- `images/pg029_page.png`
- `images/pg030_page.png`
- `images/pg031_page.png`
- `images/pg032_page.png`
- `images/pg033_page.png`
- `images/pg034_page.png`
- `images/pg035_page.png`
- `images/pg036_page.png`
- `images/pg037_page.png`
- `images/pg038_page.png`
- `images/pg039_page.png`
- `images/pg040_page.png`
- `images/pg041_page.png`
- `images/pg042_page.png`
- `images/pg043_page.png`
- `images/pg044_page.png`
- `images/pg045_page.png`
- `images/pg046_page.png`
- `images/pg047_page.png`
- `images/pg048_page.png`
- `images/pg049_page.png`
- `images/pg050_page.png`
- `images/pg051_page.png`
- `images/pg052_page.png`
- `images/pg053_page.png`
- `images/pg054_page.png`
- `images/pg055_page.png`
- `images/pg056_page.png`
- `images/pg057_page.png`
- `images/pg058_page.png`
- `images/pg059_page.png`
- `images/pg060_page.png`
- `images/pg061_page.png`
- `images/pg062_page.png`
- `images/pg063_page.png`
- `images/pg064_page.png`
- `images/pg065_page.png`
- `images/pg066_page.png`
- `images/pg067_page.png`
- `images/pg068_page.png`
- `images/pg069_page.png`
- `images/pg070_page.png`
- `images/pg071_page.png`
- `images/pg072_page.png`
- `images/pg073_page.png`
- `images/pg074_page.png`
- `images/pg075_page.png`
- `images/pg076_page.png`
- `images/pg077_page.png`
- `images/pg078_page.png`
- `images/pg079_page.png`
- `images/pg080_page.png`

## The Text ID System

Every piece of displayable text has a unique, stable **text ID**. This ID is the key that connects everything together. The same ID appears in three places simultaneously:

1. As a `data-id` attribute on HTML elements in page files
2. As a key in `content/i18n/{lang}/texts.json` (the string value)
3. As a key in `content/i18n/{lang}/audios.json` (the audio filename)

### ID Naming Conventions

| Pattern | What it is | Example |
|---|---|---|
| `pg{NNN}_gp{NNN}_tx{NNN}` | Page body text | `pg001_gp001_tx001` |
| `pg{NNN}_im{NNN}` | Image alt text / description | `pg001_im001` |
| `gl{NNN}` | Glossary word | `gl001` |
| `gl{NNN}_def` | Glossary definition | `gl001_def` |

Page/group/text numbers are zero-padded to 3 digits. Quiz option numbers are single digits.

## Key Files in Detail

### `content/pages.json` — Reading Order

An ordered array that defines the navigation spine. Every page section and quiz appears here in reading order. Here are the first entries from this book:

```json
[
  { "section_id": "pg001_sec001", "href": "index.html", "page_number": 1 },
  { "section_id": "pg002_sec001", "href": "pg002_sec001.html" },
  { "section_id": "pg003_sec001", "href": "pg003_sec001.html" },
  { "section_id": "pg004_sec001", "href": "pg004_sec001.html" },
  { "section_id": "pg005_sec001", "href": "pg005_sec001.html" }
]
```

- `section_id` — matches the `<meta name="title-id">` in the HTML file
- `href` — relative path to the HTML file from the `adt/` root
- `page_number` — original PDF page number (omitted for cover pages, quizzes, etc.)

Quizzes are interleaved after their anchor content page.

### `content/i18n/{lang}/texts.json` — All Text Content

A flat `Record<textId, string>` containing every piece of text in the book. Example entries from this book:

```json
{
  "pg001_gp001_tx001": "",
  "pg001_im001": "Cheti cha ithibati cha Jamhuri ya Muungano wa Tanzania kutoka Wizara ya Elimu, Sayansi na Teknolojia, kinachoidhinisha kitabu cha Sanaa na Michezo cha mwanafunzi wa Darasa la Nne.",
  "gl001": "aibu",
  "gl001_def": "Hisia ya kuona soni au kutaka kujificha kwa sababu ya jambo fulani."
}
```

### `content/i18n/{lang}/audios.json` — Audio Mappings

Maps each text ID to its MP3 filename in the `audio/` subdirectory:

```json
{
  "pg001_gp001_tx001": "pg001_gp001_tx001.mp3",
  "gl001": "gl001.mp3"
}
```

Audio files live at `content/i18n/{lang}/audio/{filename}.mp3`.

### `content/i18n/{lang}/glossary.json` — Glossary

Keyed by word (lowercase). Each entry has the word, a simple definition, inflected variations for matching, and decorative emoji. Example from this book:

```json
{
  "aibu": {
    "word": "aibu",
    "definition": "Hisia ya kuona soni au kutaka kujificha kwa sababu ya jambo fulani.",
    "variations": ["kuaibika","mwenye aibu"],
    "emoji": "😳🙈"
  }
}
```

The runtime uses `variations` to match and highlight glossary words anywhere in the page text.

### `assets/config.json` — Feature Flags and Languages

Controls which features the reader UI enables. This book's config:

```json
{
  "title": "Sanaa na Michezo",
  "bundleVersion": "1",
  "languages": {
    "available": [
      "sw-TZ"
    ],
    "default": "sw-TZ"
  },
  "features": {
    "signLanguage": false,
    "easyRead": true,
    "glossary": true,
    "eli5": false,
    "readAloud": true,
    "autoplay": true,
    "showTutorial": true,
    "showNavigationControls": true,
    "describeImages": true,
    "notepad": false,
    "state": true,
    "characterDisplay": false,
    "highlight": true,
    "activities": true
  },
  "analytics": {
    "enabled": false,
    "siteId": 0,
    "trackerUrl": "https://unisitetracker.unicef.io/matomo.php",
    "srcUrl": "https://unisitetracker.unicef.io/matomo.js"
  },
  "defaultSettings": {
    "dockLayout": {
      "width": "full",
      "position": "bottom",
      "align": "spread"
    },
    "theme": "dark",
    "iconSize": "md",
    "reduceMotion": false
  },
  "lockedSettings": [
    "dockLayout",
    "theme",
    "iconSize",
    "reduceMotion"
  ]
}
```

## Page HTML Structure

Each page is a standalone HTML file at the root of `adt/`. Key structural elements:

```html
<!DOCTYPE html>
<html lang="sw-TZ">
<head>
    <meta name="title-id" content="pg001_sec001" />      <!-- section identity -->
    <meta name="page-section-id" content="2" />           <!-- 1-based index in pages.json -->
    <link href="./content/tailwind_output.css" rel="stylesheet">
    <link href="./assets/libs/fontawesome/css/all.min.css" rel="stylesheet">
    <link href="./assets/fonts.css" rel="stylesheet">
</head>
<body>
    <div id="content" class="opacity-0">
        <section role="article" data-section-type="text_and_single_image"
                 data-section-id="pg001_sec001">
            <!-- Images use relative paths and carry data-id for alt text lookup -->
            <img data-id="pg001_im001" src="images/pg001_im001.png" ...>

            <!-- Text elements carry data-id for i18n and TTS -->
            <span data-id="pg001_gp001_tx001"></span>
        </section>
    </div>

    <div id="interface-container"></div>
    <div id="nav-container"></div>
    <script src="./assets/base.bundle.min.js?v=1" type="module"></script>
</body>
</html>
```

Key conventions:

- **`data-id` on text elements** links to `texts.json` and `audios.json` — the runtime replaces inner text with the value from the active language's `texts.json` and wires up audio playback from `audios.json`
- **`data-id` on images** links to image description text and audio
- **Images** use relative paths: `images/{filename}`
- **`page-section-id`** meta tag is the 1-based numeric index of this page's position in `pages.json` — the runtime uses this for navigation
- **Content starts `opacity-0`** — the JS runtime fades it in after loading the interface

## How to Edit Text

To change text content for a given language, you must update all three locations that reference the text:

1. **`texts.json`** — Change the value in `content/i18n/{lang}/texts.json` for the text ID.
2. **The HTML file** — The text also appears inline in the page HTML. Update the inner text of the element with the matching `data-id`. The runtime replaces this on load, but the inline text serves as fallback.
3. **Audio** (if applicable) — Regenerate the MP3 at `content/i18n/{lang}/audio/{textId}.mp3` and verify `audios.json` maps the text ID to the correct filename.

### Editing Glossary

Update both:

- `content/i18n/{lang}/glossary.json` — the glossary entry for the word
- `content/i18n/{lang}/texts.json` — the `gl{NNN}` and `gl{NNN}_def` entries

## How to Add a New Page

1. **Create the HTML file** — Copy an existing page as a template. Name it `pg{NNN}_sec001.html` following the sequential numbering pattern.

2. **Set the `title-id` meta tag** — `<meta name="title-id" content="pg012_sec001">`.

3. **Add text with `data-id` attributes** — Use the naming pattern `pg{NNN}_gp{NNN}_tx{NNN}` for each text element.

4. **Add images** — Place image files in `images/` and reference them with relative paths. Give each `<img>` a `data-id` attribute (e.g. `pg012_im001`).

5. **Update `pages.json`** — Insert the new entry at the correct position in reading order:
   ```json
   { "section_id": "pg012_sec001", "href": "pg012_sec001.html", "page_number": 11 }
   ```

6. **Renumber `page-section-id`** — Update the `<meta name="page-section-id">` in every HTML file that comes after the insertion point (this is a 1-based index into `pages.json`).

7. **Add text entries** — Add entries for every `data-id` in the new page to `content/i18n/{lang}/texts.json` for each language.

8. **Add audio entries** — Map each new text ID in `content/i18n/{lang}/audios.json` and place MP3 files in `content/i18n/{lang}/audio/`.

## How to Add a New Language

1. Create `content/i18n/{lang}/` with all required files:
   - `texts.json` — translated strings for every text ID
   - `audios.json` — audio filename mappings (can reuse the same naming pattern)
   - `glossary.json` — translated glossary entries
   - `videos.json` — `{}` (placeholder)
   - `audio/` — MP3 files for each text ID

2. Add the language code to `languages.available` in `assets/config.json`.

3. Optionally add UI translations at `assets/interface_translations/{lang}/interface_translations.json`.

## Where to Find Things

| What you need | Where to look |
|---|---|
| Rendered page HTML | `adt/pg{NNN}_sec{NNN}.html` |
| Entry point | `adt/index.html` (redirects to first page) |
| Page images | `adt/images/` |
| All text content | `adt/content/i18n/{lang}/texts.json` |
| Audio file mappings | `adt/content/i18n/{lang}/audios.json` |
| Audio MP3 files | `adt/content/i18n/{lang}/audio/` |
| Glossary | `adt/content/i18n/{lang}/glossary.json` |
| Reading order | `adt/content/pages.json` |
| Table of contents | `adt/content/toc.json` |
| Book config & features | `adt/assets/config.json` |
| CSS styles | `adt/content/tailwind_output.css` |
| JS runtime | `adt/assets/base.bundle.min.js` |
| UI string translations | `adt/assets/interface_translations/{lang}/` |
| Cover image | `adt/cover.png` |
| Original PDF | `SANAA-NA-MICHEZO-DRS-4-SEPT-2025.pdf` |
| Pipeline database | `SANAA-NA-MICHEZO-DRS-4-SEPT-2025.db` (SQLite) |
| Raw page renders | `images/pg{NNN}_page.png` (visual reference for original pages) |
| Raw extracted images | `images/pg{NNN}_im{NNN}.png` (pipeline artifact) |
| Source TTS audio | `audio/{lang}/` (pipeline artifact) |

## Audio Naming Conventions

| Pattern | What it is |
|---|---|
| `pg{NNN}_gp{NNN}_tx{NNN}.mp3` | Page body text read-aloud |
| `pg{NNN}_im{NNN}.mp3` | Image description read-aloud |
| `gl{NNN}.mp3` | Glossary word pronunciation |
| `gl{NNN}_def.mp3` | Glossary definition read-aloud |

## Important: What Not to Edit

- **`assets/base.bundle.min.js`** and **`assets/modules/`** — compiled JS runtime; do not modify
- **`assets/libs/`** — vendored third-party libraries (FontAwesome, MathJax)
- **`assets/fonts/`** — font files
- **`assets/sounds/`** — UI feedback sounds
- **`content/tailwind_output.css`** — compiled from all HTML files; if you add new Tailwind classes to HTML, this file must be regenerated
