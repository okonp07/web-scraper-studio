"""Theme helpers for Streamlit."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def inject_theme(css_path: Path) -> None:
    """Inject the shared stylesheet."""

    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

