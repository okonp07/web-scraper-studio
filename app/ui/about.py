"""About page content."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.utils.files import image_data_uri


def render_about(project_root: Path) -> None:
    """Render the About page with project and author information."""

    author_image = image_data_uri(project_root / "assets" / "okon-prince.png")

    st.markdown(
        """
        <section class="hero-panel about-hero">
          <div class="hero-content">
            <p class="eyebrow">About</p>
            <h1 class="about-title">About Web Scraper Studio</h1>
            <p class="about-subtitle">
              A responsible web extraction studio that turns noisy public web pages into
              readable, structured, portable knowledge assets.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    overview_col, use_case_col = st.columns(2, gap="large")
    with overview_col:
        st.markdown(
            """
            <div class="about-card">
              <h2>What the Solution Does</h2>
              <p>
                Web Scraper Studio helps people turn website content into clean,
                structured outputs that are easier to read, archive, analyze,
                share, and reuse. Instead of copying fragmented text from a page
                full of menus, cookie notices, footers, promotional banners, and
                repeated calls to action, the app focuses on the meaningful body
                content and preserves its structure for downstream use.
              </p>
              <p>
                It supports two practical workflows. <strong>Page Only</strong>
                extracts the readable content from one exact URL. <strong>Full
                Scrape</strong> crawls in breadth-first order within the selected
                scope, discovers additional internal pages through links and
                sitemaps, avoids obvious non-content routes where possible, and
                assembles the results into polished deliverables.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with use_case_col:
        st.markdown(
            """
            <div class="about-card">
              <h2>The Problem It Solves</h2>
              <p>
                Valuable public information is often trapped inside noisy web
                experiences. Researchers, students, analysts, journalists,
                compliance teams, product teams, and institutions frequently need
                accurate website content in a format that can be read offline,
                cited, reviewed, indexed, or shared internally.
              </p>
              <p>
                Without a tool like this, teams waste time manually copying pages,
                cleaning formatting by hand, chasing internal links one by one,
                and rebuilding documents from scratch. Web Scraper Studio reduces
                that friction and makes high-quality web content capture far more
                consistent and repeatable.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="about-card">
          <h2>How the Solution Works</h2>
          <ol>
            <li><strong>Input and validation.</strong> The app validates the user URL, normalizes it, and lets the user choose between a single-page scrape or a controlled full-site crawl.</li>
            <li><strong>Responsible acquisition.</strong> Requests use a clear user agent, conservative defaults, request delays, retries, robots.txt compliance, timeout limits, page-size safeguards, and domain restrictions.</li>
            <li><strong>Content extraction.</strong> The backend fetches pages with <code>httpx</code>, parses HTML with <code>BeautifulSoup</code> and <code>lxml</code>, extracts readable content with <code>readability-lxml</code> and <code>trafilatura</code>, and can fall back to <code>Playwright</code> when a page needs browser rendering.</li>
            <li><strong>Cleanup and structure preservation.</strong> The pipeline removes repetitive clutter where possible, preserves headings and lists, tracks metadata, normalizes URLs, skips duplicates, and keeps page ordering natural with breadth-first traversal.</li>
            <li><strong>Export generation.</strong> Results can be downloaded as raw TXT, a human-friendly DOCX, a polished PDF, and an IMAGES package that stores content images alongside the labels or alt text that give them context.</li>
          </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

    impact_col, ethics_col = st.columns(2, gap="large")
    with impact_col:
        st.markdown(
            """
            <div class="about-card">
              <h2>Why It Is Useful to Humanity</h2>
              <p>
                Better access to clean information makes better decisions possible.
                This tool can support education, research, journalism, knowledge
                preservation, accessibility workflows, policy review, digital
                archiving, legal and compliance analysis, and organizational memory.
              </p>
              <p>
                When web knowledge is converted into readable, portable, structured
                documents, it becomes easier to study, compare, summarize, audit,
                translate, store, and share. That is especially useful for teams
                working across limited bandwidth, mixed devices, or environments
                where dependable offline references matter.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with ethics_col:
        st.markdown(
            """
            <div class="about-card">
              <h2>Responsible by Design</h2>
              <p>
                Web Scraper Studio is built for legitimate, ethical content
                extraction. It respects robots.txt by default, stays inside the
                chosen crawl boundary, and does not attempt to bypass
                authentication, paywalls, captchas, or anti-bot protections.
              </p>
              <p>
                That makes the app useful for responsible public-web capture while
                still acknowledging the rights, policies, and technical boundaries
                that website owners put in place.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="author-layout">
          <div class="about-card author-copy-card">
            <h2>About the Author</h2>
            <h3 class="author-name">Okon Prince</h3>
            <p class="author-role">AI Engineer &amp; Data Scientist | Senior Data Scientist at MIVA Open University</p>
            <p>
              I design and deploy end-to-end data systems that turn raw data
              into production-ready intelligence.
            </p>
            <p>
              My core stack includes Python, Streamlit, BigQuery, Supabase,
              Hugging Face, PySpark, SQL, Machine Learning, LLMs, and
              Transformers.
            </p>
            <p>
              My work spans risk scoring systems, A/B testing, Traditional and
              AI-powered dashboards, RAG pipelines, predictive analytics,
              LLM-based solutions and AI research.
            </p>
            <p>
              Currently, I work as a Senior Data Scientist in the department of
              Research and Development at MIVA Open University, where I carry
              out AI / ML Research and build intelligent systems that drive
              analytics, decision support and scalable AI innovation.
            </p>
            <p>
              I believe: models are trained, systems are engineered and impact
              is delivered.
            </p>
          </div>
          <div class="about-card author-photo-card">
            <img src="{author_image}" alt="Portrait of Okon Prince" class="author-photo"/>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
