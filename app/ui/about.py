"""About page content."""

from __future__ import annotations

import streamlit as st


def render_about() -> None:
    """Render the About page with documentation on the app."""

    st.markdown(
        """
        <section class="hero-panel">
          <div class="hero-content">
            <p class="eyebrow">Documentation</p>
            <h1 class="about-title">About Web Scraper Studio</h1>
            <p class="about-subtitle">
              A production-ready web scraping toolkit that extracts readable content
              from websites and delivers polished, structured exports.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="about-card">
          <h2>What It Does</h2>
          <p>
            Web Scraper Studio crawls websites, extracts their readable content,
            strips away clutter like ads, navigation bars, and cookie banners,
            and then exports clean, structured documents. It works in two modes:
          </p>
          <ul>
            <li><strong>Page Only</strong> &mdash; Scrape a single page. Paste any URL
                and get a clean extract of the readable body content.</li>
            <li><strong>Full Scrape</strong> &mdash; Crawl an entire site breadth-first.
                The scraper discovers pages via links and sitemaps, deduplicates
                content, and produces multi-page documents.</li>
          </ul>

          <h2>Export Formats</h2>
          <ul>
            <li><strong>TXT</strong> &mdash; Plain text with page separators, headings, and lists preserved.</li>
            <li><strong>DOCX</strong> &mdash; A formatted Word document with cover page, table of contents,
                semantic headings, styled tables, and proper fonts.</li>
            <li><strong>PDF</strong> &mdash; A polished PDF with cover page, bookmarked table of contents,
                embedded images (optional), styled typography, and page numbers.</li>
            <li><strong>IMAGES</strong> &mdash; A ZIP archive containing all content images found on the
                scraped pages, saved with descriptive labels matching their captions
                or alt text as they appear on the website. Includes a
                <code>_image_labels.txt</code> manifest file.</li>
          </ul>

          <h2>How to Use</h2>
          <ul>
            <li><strong>1. Choose a mode</strong> &mdash; Select "Page Only" for a single page or
                "Full Scrape" to crawl the whole site.</li>
            <li><strong>2. Configure boundaries</strong> &mdash; Set max pages, depth, delay,
                concurrency, and scope limits in the sidebar.</li>
            <li><strong>3. Pick export formats</strong> &mdash; Select which output formats you want
                (TXT, DOCX, PDF, IMAGES). All can be selected at once.</li>
            <li><strong>4. Paste a URL and scrape</strong> &mdash; Enter the target website URL and
                click "Start scrape". Watch real-time progress in the status panel.</li>
            <li><strong>5. Download results</strong> &mdash; When complete, download buttons appear
                for each selected format. Preview snippets show the first few pages.</li>
          </ul>

          <h2>Key Features</h2>
          <ul>
            <li><strong>Robots.txt compliance</strong> &mdash; Respects robots.txt by default.
                The scraper will not crawl pages that the site owner has disallowed.</li>
            <li><strong>Breadth-first crawling</strong> &mdash; Discovers pages level by level,
                staying within the configured scope (subdomain or root domain).</li>
            <li><strong>Sitemap discovery</strong> &mdash; Automatically checks for sitemaps to
                seed the crawl queue for faster, more complete coverage.</li>
            <li><strong>Boilerplate removal</strong> &mdash; Two modes: Conservative (removes scripts,
                nav, footer) and Aggressive (also strips headers, forms, and noisy elements).</li>
            <li><strong>Near-duplicate detection</strong> &mdash; Uses text fingerprinting and
                similarity matching to skip pages with duplicate content.</li>
            <li><strong>Browser fallback</strong> &mdash; Falls back to headless browser rendering
                for JavaScript-heavy sites when standard HTTP fetching yields insufficient content.</li>
            <li><strong>Rate limiting</strong> &mdash; Built-in delay between requests prevents
                overwhelming target servers.</li>
            <li><strong>Image extraction</strong> &mdash; Identifies meaningful content images,
                filters out decorative elements (logos, icons, avatars), downloads
                and optimizes images for export.</li>
          </ul>

          <h2>Configuration</h2>
          <ul>
            <li><strong>Max pages</strong> &mdash; Upper limit on pages to scrape (1&ndash;120).</li>
            <li><strong>Max depth</strong> &mdash; How many link levels deep to follow (0&ndash;6).</li>
            <li><strong>Delay</strong> &mdash; Seconds to wait between requests (0&ndash;5).</li>
            <li><strong>Concurrency</strong> &mdash; Number of parallel fetch threads (1&ndash;4).</li>
            <li><strong>Timeout</strong> &mdash; Per-request timeout in seconds (5&ndash;60).</li>
            <li><strong>Max page size</strong> &mdash; Skip responses larger than this (1&ndash;25 MB).</li>
            <li><strong>Scope</strong> &mdash; Stay on the same subdomain or allow the full root domain.</li>
            <li><strong>Query params</strong> &mdash; Whether to treat URLs with different query
                parameters as distinct pages.</li>
          </ul>

          <h2>Developer Settings</h2>
          <p>
            Advanced settings are available in <code>config/developer.toml</code>.
            These include the duplicate similarity threshold, maximum images per page,
            minimum text length, debug logging, and the option to disable robots.txt
            compliance. These settings are not exposed in the UI to keep the interface
            focused on the most common use cases.
          </p>

          <h2>Ethical Use</h2>
          <p>
            This tool is designed for legitimate content extraction. Please respect
            website terms of service. Do not use it to bypass authentication, paywalls,
            CAPTCHAs, or anti-bot controls. The default configuration respects robots.txt
            and uses polite rate limiting.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
