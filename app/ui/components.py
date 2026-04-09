"""Reusable Streamlit UI components."""

from __future__ import annotations

import html

import streamlit as st

from app.models import ScrapeIssue, ScrapeResult, ScrapeSummary
from app.utils.text import truncate


def render_hero() -> None:
    """Render the page hero."""

    st.markdown(
        """
        <section class="hero-panel">
          <div class="hero-content">
            <p class="eyebrow">Production-ready website extraction</p>
            <h1 class="hero-title">Web Scraper Studio</h1>
            <p class="hero-copy">
              Crawl a single page or a whole site, clean the readable content, and export
              polished TXT, DOCX, and PDF deliverables with source-aware structure.
            </p>
            <div class="hero-pills">
              <span>Robots-respecting by default</span>
              <span>Breadth-first full-site mode</span>
              <span>Readable document exports</span>
            </div>
          </div>
        </section>
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
            st.download_button(
                label=f"Download {artifact.format.value.upper()}",
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

