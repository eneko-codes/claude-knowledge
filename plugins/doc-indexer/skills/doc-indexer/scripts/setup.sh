#!/bin/bash
# setup.sh — One-time environment setup for doc-indexer scripts.
#
# Creates an isolated Python virtual environment in .venv/, installs all
# dependencies from requirements.txt, and downloads the Chromium browser
# binary that Playwright needs for headless crawling.
#
# This script is idempotent — safe to run multiple times. If .venv/ already
# exists, pip will skip already-installed packages and only install missing ones.
#
# After running this script, activate the venv with:
#   source .venv/bin/activate
#
# Requirements:
#   - Python 3.8+ (tested with 3.9.6, 3.11, 3.12)
#   - ~200MB disk space for Chromium browser download
#   - Internet connection for pip install and Playwright browser download

# Exit immediately if any command fails (-e flag).
# This prevents silent failures where pip partially installs and we proceed
# with a broken environment.
set -e

# Change to the directory containing this script, regardless of where it's
# invoked from. This ensures .venv is always created next to the scripts.
cd "$(dirname "$0")"

# Create a Python virtual environment in .venv/ to isolate dependencies.
# This avoids polluting the system Python installation and ensures
# reproducible behavior across machines.
python3 -m venv .venv

# Activate the venv — all subsequent pip/python commands use this environment.
source .venv/bin/activate

# Install Python dependencies from requirements.txt:
#   - playwright:         Browser automation library (drives Chromium)
#   - playwright-stealth: Anti-fingerprint patches to bypass bot detection
#   - beautifulsoup4:     HTML parsing and DOM traversal
#   - markdownify:        HTML → markdown conversion
#   - pygments:           Code language guessing for unannotated blocks
#   - lxml:               Fast HTML parser backend for BeautifulSoup
pip install -r requirements.txt

# Download the Chromium browser binary that Playwright will use.
# This is a one-time ~200MB download stored in ~/.cache/ms-playwright/.
# Subsequent runs of this command are no-ops if the browser is already installed.
playwright install chromium

echo "Setup complete. Activate with: source .venv/bin/activate"
