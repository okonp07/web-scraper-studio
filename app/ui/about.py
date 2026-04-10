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
            <li><strong>TXT</strong> &mdash; Plain text with
                page separators, headings, and lists.</li>
            <li><strong>DOCX</strong> &mdash; A formatted Word doc
                with cover page, TOC, headings, and tables.</li>
            <li><strong>PDF</strong> &mdash; A polished PDF with
                cover, bookmarks, images, and page numbers.</li>
            <li><strong>IMAGES</strong> &mdash; A ZIP of all
                content images with descriptive labels and a
                <code>_image_labels.txt</code> manifest.</li>
          </ul>

          <h2>How to Use</h2>
          <ul>
            <li><strong>1. Choose a mode</strong> &mdash;
                "Page Only" or "Full Scrape".</li>
            <li><strong>2. Configure boundaries</strong> &mdash;
                Set pages, depth, delay, and scope.</li>
            <li><strong>3. Pick export formats</strong> &mdash;
                TXT, DOCX, PDF, IMAGES (any combo).</li>
            <li><strong>4. Paste a URL and scrape</strong> &mdash;
                Enter the URL and click "Start scrape".</li>
            <li><strong>5. Download results</strong> &mdash;
                Download buttons and previews appear.</li>
          </ul>

          <h2>Key Features</h2>
          <ul>
            <li><strong>Robots.txt compliance</strong> &mdash;
                Respects robots.txt by default.</li>
            <li><strong>Breadth-first crawling</strong> &mdash;
                Discovers pages level by level in scope.</li>
            <li><strong>Sitemap discovery</strong> &mdash;
                Checks sitemaps for faster coverage.</li>
            <li><strong>Boilerplate removal</strong> &mdash;
                Conservative or Aggressive cleanup.</li>
            <li><strong>Near-duplicate detection</strong> &mdash;
                Fingerprinting skips duplicate pages.</li>
            <li><strong>Browser fallback</strong> &mdash;
                Headless rendering for JS-heavy sites.</li>
            <li><strong>Rate limiting</strong> &mdash;
                Built-in delay between requests.</li>
            <li><strong>Image extraction</strong> &mdash;
                Finds content images, skips decorative.</li>
          </ul>

          <h2>Configuration</h2>
          <ul>
            <li><strong>Max pages</strong> &mdash;
                Upper limit on pages (1&ndash;120).</li>
            <li><strong>Max depth</strong> &mdash;
                Link levels to follow (0&ndash;6).</li>
            <li><strong>Delay</strong> &mdash;
                Wait between requests (0&ndash;5s).</li>
            <li><strong>Concurrency</strong> &mdash;
                Parallel fetch threads (1&ndash;4).</li>
            <li><strong>Timeout</strong> &mdash;
                Per-request timeout (5&ndash;60s).</li>
            <li><strong>Max page size</strong> &mdash;
                Skip large responses (1&ndash;25 MB).</li>
            <li><strong>Scope</strong> &mdash;
                Subdomain or full root domain.</li>
            <li><strong>Query params</strong> &mdash;
                Treat query variants as distinct.</li>
          </ul>

          <h2>Developer Settings</h2>
          <p>
            Advanced settings live in
            <code>config/developer.toml</code>:
            duplicate threshold, max images per page,
            min text length, debug logging, and
            robots.txt override. Not exposed in the UI.
          </p>

          <h2>Ethical Use</h2>
          <p>
            Designed for legitimate content extraction.
            Respect website terms of service. Do not
            bypass authentication, paywalls, CAPTCHAs,
            or anti-bot controls.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
