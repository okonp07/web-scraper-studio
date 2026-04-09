# Web Scraper Studio

Web Scraper Studio is a production-oriented Streamlit application for scraping either a single web page or an in-scope portion of a website, then exporting the cleaned result as TXT, DOCX, and PDF.

It is designed for readable research capture, documentation workflows, and content archiving rather than aggressive crawling. By default it respects `robots.txt`, rate limits requests, stays within the intended domain boundary, and avoids common non-content paths like login, cart, checkout, admin, and tag pages.

## Features

- Page Only mode for extracting the main readable content from one exact URL
- Full Scrape mode for breadth-first, in-domain crawling with sitemap discovery
- URL normalization, deduplication, canonical handling, and loop prevention
- `robots.txt` respect by default, with a developer-only config override
- Rate limiting, retries, timeout safeguards, and file-size caps
- Readability-focused extraction using `readability-lxml` and `trafilatura`
- Structured exports:
  - TXT with ordered page separators
  - DOCX with headings, summary pages, and a table-of-contents field
  - PDF with sectioned layout, table of contents, and optional content images
- Progress UI with counts, current page, logs, skipped pages, and errors
- Streamlit-ready frontend with polished visual styling
- Test scaffolding, GitHub Actions CI, and deployment-friendly repo layout

## Project Structure

```text
web-scraper-studio/
├── .github/workflows/ci.yml
├── .streamlit/config.toml
├── app/
│   ├── models/
│   ├── services/
│   ├── ui/
│   ├── utils/
│   └── streamlit_app.py
├── assets/
│   └── theme.css
├── config/
│   ├── developer.toml
│   └── developer.toml.example
├── docs/
│   └── architecture.md
├── exporters/
│   ├── docx_exporter.py
│   ├── pdf_exporter.py
│   └── txt_exporter.py
├── scraper/
│   ├── crawler.py
│   ├── deduper.py
│   ├── extractor.py
│   ├── fetcher.py
│   ├── images.py
│   ├── parser.py
│   └── robots.py
├── tests/
│   ├── test_assembler.py
│   ├── test_deduper.py
│   ├── test_parser.py
│   └── test_url_utils.py
├── .env.example
├── .gitignore
├── Makefile
├── pyproject.toml
└── requirements.txt
```

## Architecture

The app uses a layered pipeline:

1. `app/streamlit_app.py` collects user input and renders progress/results.
2. `app/services/scrape_service.py` orchestrates the crawl, post-processing, and exports.
3. `scraper/crawler.py` performs breadth-first traversal and emits progress events.
4. `scraper/fetcher.py`, `scraper/robots.py`, `scraper/parser.py`, `scraper/extractor.py`, and `scraper/deduper.py` handle the core crawl mechanics.
5. `app/services/assembler.py` removes repeated cross-page boilerplate.
6. `exporters/` turns structured page content into TXT, DOCX, and PDF artifacts.

See [`docs/architecture.md`](docs/architecture.md) for a short visual overview.

## Requirements

- Python 3.12
- pip
- Optional for richer JS-heavy scraping:
  - Playwright browser binaries via `playwright install chromium`

## Setup

```bash
git clone <your-repo-url>
cd web-scraper-studio
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

If you do not install Playwright, the app still works for normal HTML pages. Only browser-render fallback is affected.

## Run Locally

```bash
streamlit run app/streamlit_app.py
```

Or use:

```bash
make run
```

## Developer Config

The standard UI intentionally does not expose `robots.txt` overrides.

Developer-only crawler settings live in:

- `config/developer.toml`
- `config/developer.toml.example`

This is where you can tune duplicate thresholds, sitemap limits, image caps, and, if you explicitly choose to do so for controlled internal work, robots behavior.

## Environment Variables

Sample values are included in `.env.example`.

Supported values:

- `SCRAPER_LOG_LEVEL`
- `SCRAPER_DEFAULT_TIMEOUT`
- `SCRAPER_MAX_CONCURRENCY`
- `SCRAPER_USER_AGENT`
- `SCRAPER_DEV_CONFIG`

## Running Tests

```bash
pytest
```

Lint:

```bash
ruff check .
```

Or run both:

```bash
make check
```

## Deployment

### Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create a new app and point it to:
   - Repository: your fork
   - Branch: `main`
   - Main file path: `app/streamlit_app.py`
3. Add any environment variables you need in the Streamlit app settings.
4. Deploy.

Notes:

- TXT, DOCX, and PDF generation work in a standard Python environment.
- Browser-render fallback requires Playwright plus browser binaries. That may need extra deployment setup depending on the host.
- If your host does not support Playwright easily, keep browser fallback off or treat it as an optional enhancement.

### Other simple options

- Render
- Railway
- Docker-based hosts
- Any VM or container platform that can run Streamlit

## Output Behavior

### TXT

- Preserves page ordering
- Adds title, URL, and scrape timestamp markers per page

### DOCX

- Adds cover and summary sections
- Uses Word heading styles for navigability
- Adds a TOC field that Word can update
- Organizes content page by page

### PDF

- Adds a cover page and table of contents
- Preserves heading hierarchy and whitespace
- Includes accessible content images when enabled
- Avoids decorative asset downloads where possible

## Limitations

- Some highly dynamic sites may need browser rendering to expose their readable content.
- Some anti-bot-protected sites will still refuse access, and this tool does not attempt to bypass them.
- Boilerplate cleanup is heuristic. It is designed to improve readability, but no extractor perfectly reconstructs every page.
- PDF quality depends on the structure and accessibility of the source content and images.
- DOCX tables of contents may need to be updated inside Microsoft Word after opening the file.

## Legal and Ethical Notes

- Respect site terms, copyright, and usage policies.
- Do not use this tool to bypass authentication, paywalls, captchas, or anti-bot protections.
- Keep crawl settings conservative on third-party sites.
- `robots.txt` is respected by default for a reason. If you override it in a developer config, do so only when you are authorized.

## Suggested Next Enhancements

- Persistent job history and export archive
- Background task execution for very large crawls
- Richer per-page preview with images
- Smarter semantic duplicate detection
- Optional authenticated scraping for first-party/internal sites where you control access

