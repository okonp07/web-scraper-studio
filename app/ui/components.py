"""Reusable Streamlit UI components."""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from app.models import ScrapeIssue, ScrapeResult, ScrapeSummary
from app.utils.files import image_data_uri
from app.utils.text import truncate


def render_hero(project_root: Path, dark_mode: bool) -> None:
    """Render the page hero."""

    hero_path = project_root / "assets" / ("hero-dark.png" if dark_mode else "hero-light.png")
    hero_src = image_data_uri(hero_path)
    st.markdown(
        f"""
        <section class="hero-panel hero-panel-image">
          <div class="hero-image-shell">
            <img src="{hero_src}" alt="Web Scraper Studio hero artwork" class="hero-image"/>
          </div>
          <div class="hero-caption-row">
            <div class="hero-content">
              <p class="eyebrow">Production-ready website extraction</p>
              <p class="hero-copy">
                Crawl a single page or an in-scope site, extract the readable content,
                and export polished, source-aware deliverables.
              </p>
            </div>
            <div class="hero-pills">
              <span>TXT, DOCX, PDF, and Images</span>
              <span>Robots-respecting by default</span>
              <span>Human-readable exports</span>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the shared app footer."""

    st.markdown(
        """
        <footer class="app-footer">
          <p>&copy; Okon Prince, 2026</p>
          <p>
            This project is powered with httpx + BeautifulSoup/lxml + readability-lxml +
            trafilatura, with Playwright as the rendering fallback.
          </p>
          <p>enquiries; <a href="mailto:okonp07@gmail.com">okonp07@gmail.com</a></p>
        </footer>
        """,
        unsafe_allow_html=True,
    )


def render_info_panel(text: str) -> None:
    """Render a polished informational panel."""

    safe_text = html.escape(text)
    st.markdown(
        f"""
        <div class="info-panel">
          <div class="section-kicker">Quick summary</div>
          <p>{safe_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(snapshot: dict[str, object]) -> None:
    """Render the live progress summary."""

    current_url = html.escape(str(snapshot.get("current_url", "Waiting to start")))
    message = html.escape(str(snapshot.get("message", "Ready")))
    discovered = snapshot.get("discovered", 0)
    scraped = snapshot.get("scraped", 0)
    skipped = snapshot.get("skipped", 0)
    errors = snapshot.get("errors", 0)

    st.markdown(
        f"""
        <div class="status-card">
          <div class="section-kicker">Live status</div>
          <h3 class="card-title">{message}</h3>
          <p class="card-subtle">{current_url}</p>
          <div class="metric-grid compact">
            <div class="metric-card">
              <span class="metric-label">Discovered</span>
              <strong class="metric-value">{discovered}</strong>
            </div>
            <div class="metric-card">
              <span class="metric-label">Scraped</span>
              <strong class="metric-value">{scraped}</strong>
            </div>
            <div class="metric-card">
              <span class="metric-label">Skipped</span>
              <strong class="metric-value">{skipped}</strong>
            </div>
            <div class="metric-card">
              <span class="metric-label">Errors</span>
              <strong class="metric-value">{errors}</strong>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_log_panel(logs: list[str]) -> None:
    """Render the live log entries."""

    items = "".join(f"<li>{html.escape(line)}</li>" for line in logs[-14:])
    st.markdown(
        f"""
        <div class="log-card">
          <div class="section-kicker">Status log</div>
          <ul class="log-list">{items or "<li>Waiting for activity...</li>"}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary(summary: ScrapeSummary) -> None:
    """Render the scrape result summary cards."""

    metrics = [
        ("Mode", summary.mode.value.replace("_", " ").title()),
        ("Pages scraped", f"{summary.pages_scraped}"),
        ("Pages skipped", f"{summary.pages_skipped}"),
        ("Words", f"{summary.total_words:,}"),
        ("Images", f"{summary.total_images}"),
        ("Runtime", f"{summary.runtime_seconds:.1f}s"),
    ]
    cards = "".join(
        f"""
        <div class="metric-card">
          <span class="metric-label">{label}</span>
          <strong class="metric-value">{value}</strong>
        </div>
        """
        for label, value in metrics
    )

    st.markdown(
        f"""
        <div class="result-card">
          <div class="section-kicker">Scrape summary</div>
          <h3 class="card-title">{html.escape(summary.start_url)}</h3>
          <div class="metric-grid">{cards}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_downloads(result: ScrapeResult) -> None:
    """Render download buttons for generated artifacts."""

    if not result.artifacts:
        st.warning("The scrape completed, but no downloadable artifacts were generated.")
        return

    columns = st.columns(len(result.artifacts))
    for column, artifact in zip(columns, result.artifacts, strict=False):
        with column:
            if artifact.format.value == "images":
                label = "Download Images (ZIP)"
            else:
                label = f"Download {artifact.format.value.upper()}"
            st.download_button(
                label=label,
                data=artifact.bytes_data,
                file_name=artifact.filename,
                mime=artifact.mime_type,
                use_container_width=True,
            )


def render_previews(result: ScrapeResult) -> None:
    """Render first-page previews."""

    st.markdown("### Preview snippets")
    for page in result.pages[:3]:
        st.markdown(
            f"""
            <div class="preview-card">
              <div class="preview-header">
                <span class="preview-index">Page {page.order}</span>
                <span class="preview-url">{html.escape(page.final_url)}</span>
              </div>
              <h4 class="preview-title">{html.escape(page.title)}</h4>
              <p class="preview-copy">{html.escape(truncate(page.text_content, limit=420))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_issues(title: str, issues: list[ScrapeIssue]) -> None:
    """Render skipped/error issue cards."""

    with st.expander(f"{title} ({len(issues)})", expanded=False):
        if not issues:
            st.caption("No items to show.")
            return
        for issue in issues:
            st.markdown(
                f"""
                <div class="issue-card">
                  <strong>{html.escape(issue.reason)}</strong><br/>
                  <span>{html.escape(issue.url)}</span>
                  {"<br/><small>" + html.escape(issue.detail) + "</small>" if issue.detail else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )
