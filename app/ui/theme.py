"""Theme helpers for Streamlit."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


def inject_theme(css_path: Path) -> None:
    """Inject the shared stylesheet."""

    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


def apply_theme_class(dark: bool) -> None:
    """Apply ws-dark or ws-light class to the root HTML element."""

    cls = "ws-dark" if dark else "ws-light"
    components.html(
        f"""
        <script>
        const root = window.parent.document.documentElement;
        root.classList.remove('ws-dark', 'ws-light');
        root.classList.add('{cls}');
        </script>
        """,
        height=0,
        width=0,
    )
