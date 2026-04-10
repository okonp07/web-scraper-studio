.PHONY: install install-dev playwright-install run test lint check

install:
	python3 -m pip install -r requirements.txt

install-dev: install
	python3 -m pip install -e .[dev]

playwright-install:
	playwright install chromium

run:
	streamlit run app.py

test:
	pytest

lint:
	ruff check .

check: lint test
