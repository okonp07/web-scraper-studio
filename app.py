"""Repository-root Streamlit entrypoint.

This file exists to make local runs and Streamlit Community Cloud setup simpler:

    streamlit run app.py

It bootstraps the existing ``app/`` package in-place so internal imports such as
``from app.models ...`` keep working even though this root file is also named
``app.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT_DIR / "app"
PACKAGE_INIT = PACKAGE_DIR / "__init__.py"


def _bootstrap_app_package() -> None:
    """Expose the ``app/`` directory as the importable ``app`` package."""

    package_module = sys.modules.setdefault("app", sys.modules[__name__])
    package_module.__file__ = str(PACKAGE_INIT)
    package_module.__package__ = "app"
    package_module.__path__ = [str(PACKAGE_DIR)]

    if getattr(package_module, "_shim_bootstrapped", False):
        return

    init_code = PACKAGE_INIT.read_text(encoding="utf-8")
    exec(compile(init_code, str(PACKAGE_INIT), "exec"), package_module.__dict__)
    package_module._shim_bootstrapped = True


_bootstrap_app_package()


def main() -> None:
    """Launch the internal Streamlit app."""

    from app.streamlit_app import main as streamlit_main

    streamlit_main()


if __name__ == "__main__":
    main()

