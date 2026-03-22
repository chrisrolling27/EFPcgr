#!/usr/bin/env bash
# Install deps from public PyPI only (no corporate extra index). If pip still hits an
# unreachable mirror, check ~/.pip/pip.conf or ~/.config/pip/pip.conf for extra-index-url.
python3 -m venv venv --clear --upgrade-deps
# shellcheck source=/dev/null
. venv/bin/activate

# Drop inherited pip index env vars so a corporate shell profile cannot add an unreachable mirror.
unset PIP_EXTRA_INDEX_URL 2>/dev/null || true

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt \
  --index-url https://pypi.org/simple \
  --trusted-host pypi.org \
  --trusted-host files.pythonhosted.org
