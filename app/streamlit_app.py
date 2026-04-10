"""Streamlit frontend for Web Scraper Studio."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.models import BoilerplateMode, CrawlScope, OutputFormat, ScrapeMode, ScrapeRequest
from app.services.feedback_service import FeedbackService
from app.services.scrape_service import ScrapeService
from app.ui.about import render_about
from app.ui.feedback import render_feedback
from app.ui.components import (
    render_downloads,
    render_footer,
    render_hero,
    render_info_panel,
    render_issues,
    render_log_panel,
    render_previews,
    render_status_card,
    render_summary,
)
from app.ui.theme import apply_theme_class, inject_theme

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@st.cache_resource
def get_scrape_service() -> ScrapeService:
    """Create and cache the scrape service."""

    return ScrapeService(PROJECT_ROOT)


@st.cache_resource
def get_feedback_service() -> FeedbackService:
    """Create and cache the feedback service."""

    return FeedbackService(PROJECT_ROOT)


def main() -> None:
    """Render and run the Streamlit app."""

    st.set_page_config(
        page_title="Web Scraper Studio",
        page_icon=":material/travel_explore:",
        layout="wide",
    )
    inject_theme(PROJECT_ROOT / "assets" / "theme.css")

    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None

    with st.sidebar:
        nav_col, theme_col = st.columns([3, 2])
        with nav_col:
            page = st.radio(
                "Navigate",
                options=["Scraper", "About", "Feedback"],
                horizontal=True,
                label_visibility="collapsed",
                help="Switch between the main scraper workflow, the project overview, and the feedback form.",
            )
        with theme_col:
            dark_mode = st.toggle(
                "Dark mode",
                value=st.session_state.get("dark_mode", False),
                key="dark_mode",
                help="Switch the interface between light mode and dark mode.",
            )
        apply_theme_class(dark_mode)
        st.markdown("---")

    if page == "About":
        render_about(PROJECT_ROOT)
        render_footer()
        return

    if page == "Feedback":
        render_feedback(get_feedback_service())
        render_footer()
        return

    render_hero(PROJECT_ROOT, dark_mode)
    service = get_scrape_service()

    with st.sidebar:
        st.markdown("## Controls")
        mode_label = st.radio(
            "Scrape mode",
            options=["Page Only", "Full Scrape"],
            horizontal=False,
            help="Page Only extracts one exact URL. Full Scrape follows in-scope internal links and builds a multi-page result.",
        )
        st.markdown("### Crawl boundaries")
        page_only = mode_label == "Page Only"
        max_pages = st.slider(
            "Max pages", min_value=1, max_value=2000,
            value=30, disabled=page_only,
            help="Sets the maximum number of pages Full Scrape may visit. Keep it lower for faster runs and raise it for broader site coverage.",
        )
        max_depth = st.slider(
            "Max depth", min_value=0, max_value=6,
            value=2, disabled=page_only,
            help="Controls how many link levels away from the starting page the crawler may go during Full Scrape.",
        )
        delay_seconds = st.slider(
            "Delay between requests",
            min_value=0.0, max_value=5.0, value=0.8, step=0.1,
            help="Adds a pause between requests to reduce load on the target website and lower the chance of rate limiting.",
        )
        concurrency = st.slider(
            "Concurrency", min_value=1, max_value=4, value=1,
            help="Sets how many pages may be fetched in parallel. Conservative values are safer and easier on target sites.",
        )
        timeout_seconds = st.slider(
            "Request timeout (seconds)",
            min_value=5, max_value=60, value=20,
            help="Defines how long the app waits for each page request before treating it as a timeout.",
        )
        max_file_size_mb = st.slider(
            "Max page size (MB)",
            min_value=1,
            max_value=25,
            value=6,
            help="Skips unusually large HTML responses so exports stay manageable and the crawler avoids oversized pages.",
        )

        include_query_params = st.toggle(
            "Include query parameters",
            value=False,
            help="Treats URLs with different query strings as separate pages. Leave this off to avoid duplicates on most sites.",
        )
        scope_label = st.radio(
            "Scope",
            options=["Same subdomain only", "Entire root domain"],
            horizontal=False,
            disabled=mode_label == "Page Only",
            help="Choose whether Full Scrape stays on the exact subdomain or can follow links across the wider root domain.",
        )
        include_sitemap = st.toggle(
            "Use sitemap discovery",
            value=True,
            disabled=page_only,
            help="Checks sitemap.xml when available so the crawler can discover in-scope pages more efficiently.",
        )
        use_browser_fallback = st.toggle(
            "Use browser fallback",
            value=True,
            help="Uses browser rendering for JS-heavy pages when standard HTML fetching is not enough.",
        )

        st.markdown("### Output")
        selected_outputs = st.multiselect(
            "Formats",
            options=["TXT", "DOCX", "PDF", "IMAGES"],
            default=["TXT", "DOCX", "PDF", "IMAGES"],
            help="Choose which downloadable outputs to generate after the scrape finishes.",
        )
        include_images = st.toggle(
            "Include images in PDF",
            value=True,
            help="Adds relevant content images to the PDF export when they can be accessed and processed cleanly.",
        )
        include_metadata = st.toggle(
            "Include metadata",
            value=True,
            help="Includes useful source details such as URLs, timestamps, and page metadata in generated exports.",
        )
        boilerplate_label = st.radio(
            "Boilerplate cleanup",
            options=["Conservative", "Aggressive"],
            horizontal=False,
            help="Conservative cleanup keeps more original page material. Aggressive cleanup removes more repeated clutter and promo content.",
        )

        st.markdown("### Notes")
        st.caption(
            "Robots.txt is respected by default. Developers can "
            "override that in `config/developer.toml`, "
            "but the default interface does not expose it."
        )
        st.caption(
            "Do not use this tool to bypass authentication, "
            "paywalls, captchas, or anti-bot controls."
        )

    input_col, info_col = st.columns([1.4, 0.8], gap="large")
    with input_col:
        st.markdown("### Start a scrape")
        start_url = st.text_input(
            "Website URL",
            placeholder="https://example.com/articles/welcome",
            help="Paste a single page URL or a homepage for a full-site scrape.",
        )
        start_scrape = st.button("Start scrape", type="primary", use_container_width=True)

    with info_col:
        st.markdown("### What you get")
        render_info_panel(
            "Page Only extracts the readable body from the exact URL you enter. "
            "Full Scrape walks the site breadth-first, stays in scope, deduplicates content, "
            "and prepares export-ready documents. The IMAGES format downloads all content "
            "images with their website labels into a zip archive."
        )

    status_container = st.container()
    result_container = st.container()

    if start_scrape:
        if not selected_outputs:
            st.error("Select at least one export format before starting.")
        elif not start_url or not start_url.strip():
            st.error("Please enter a website URL before starting.")
        else:
            mode = ScrapeMode.PAGE_ONLY if mode_label == "Page Only" else ScrapeMode.FULL_SCRAPE
            scope = (
                CrawlScope.SAME_SUBDOMAIN
                if scope_label == "Same subdomain only"
                else CrawlScope.ROOT_DOMAIN
            )
            try:
                request = ScrapeRequest(
                    start_url=start_url,
                    mode=mode,
                    max_pages=max_pages,
                    max_depth=max_depth,
                    delay_seconds=delay_seconds,
                    timeout_seconds=timeout_seconds,
                    max_file_size_mb=max_file_size_mb,
                    concurrency=concurrency,
                    include_query_params=include_query_params,
                    scope=scope,
                    include_sitemap=include_sitemap,
                    use_browser_fallback=use_browser_fallback,
                    include_images_in_pdf=include_images,
                    include_metadata=include_metadata,
                    boilerplate_mode=(
                        BoilerplateMode.CONSERVATIVE
                        if boilerplate_label == "Conservative"
                        else BoilerplateMode.AGGRESSIVE
                    ),
                    output_formats=[
                        OutputFormat[item]
                        for item in selected_outputs
                    ],
                )
            except Exception as exc:
                st.error(f"Invalid settings: {exc}")
                st.stop()

            progress_bar = status_container.progress(0.0, text="Preparing scrape...")
            status_placeholder = status_container.empty()
            logs_placeholder = status_container.empty()
            live_logs: list[str] = []
            snapshot: dict[str, object] = {
                "message": "Preparing scrape...",
                "current_url": request.start_url,
            }

            def emit(event: dict[str, object]) -> None:
                snapshot.update(event)
                message = str(event.get("message", "Working..."))
                if message:
                    live_logs.append(message)
                discovered = int(snapshot.get("discovered", 0) or 0)
                scraped = int(snapshot.get("scraped", 0) or 0)
                ratio = min(scraped / max(discovered, 1), 0.99) if discovered else 0.05
                progress_bar.progress(ratio, text=message)
                with status_placeholder:
                    render_status_card(snapshot)
                with logs_placeholder:
                    render_log_panel(live_logs)

            try:
                result = service.run(request, emit=emit)
                st.session_state["last_result"] = result
                progress_bar.progress(1.0, text="Scrape complete")
                with status_placeholder:
                    render_status_card(
                        {
                            "message": "Scrape complete",
                            "current_url": request.start_url,
                            "discovered": result.summary.discovered_pages,
                            "scraped": result.summary.pages_scraped,
                            "skipped": result.summary.pages_skipped,
                            "errors": result.summary.error_count,
                        }
                    )
                with logs_placeholder:
                    render_log_panel(result.logs)
            except Exception as exc:
                progress_bar.progress(1.0, text="Scrape failed")
                st.session_state["last_result"] = None
                st.error(f"The scrape failed: {exc}")

    result = st.session_state.get("last_result")
    if result:
        with result_container:
            st.markdown("---")
            render_summary(result.summary)
            render_downloads(result)
            render_previews(result)
            render_issues("Skipped pages", result.skipped_pages)
            render_issues("Errors", result.errors)

    render_footer()


if __name__ == "__main__":
    main()
