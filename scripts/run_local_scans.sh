#!/usr/bin/env bash
# Run all security scans locally before pushing.
# Mirrors the CI pipeline so you can catch failures early.
#
# Usage: ./scripts/run_local_scans.sh
# (Run from the repository root. On Windows, use Git Bash or WSL.)

set -uo pipefail

FAILED=0

section() { printf "\n\033[1;34m==> %s\033[0m\n" "$1"; }
pass()    { printf "\033[1;32m    PASS\033[0m\n"; }
fail()    { printf "\033[1;31m    FAIL\033[0m\n"; FAILED=1; }
skip()    { printf "\033[1;33m    SKIPPED: %s\033[0m\n" "$1"; }

section "1/5 Unit tests (pytest)"
if pytest -q; then pass; else fail; fi

section "2/5 SAST (Bandit, medium+ severity)"
if bandit -r app -ll -ii -q; then pass; else fail; fi

section "3/5 Dependency scan (pip-audit)"
if pip-audit -r requirements.txt; then pass; else fail; fi

section "4/5 Secrets scan (Gitleaks)"
if command -v gitleaks >/dev/null 2>&1; then
    if gitleaks detect --source . --config .gitleaks.toml -v; then pass; else fail; fi
else
    skip "gitleaks not installed (https://github.com/gitleaks/gitleaks#installing)"
fi

section "5/5 Container scan (Trivy)"
if command -v trivy >/dev/null 2>&1 && command -v docker >/dev/null 2>&1; then
    docker build -f docker/Dockerfile -t devsecops-pipeline:local . || fail
    if trivy image --severity CRITICAL,HIGH --ignore-unfixed \
        --exit-code 1 devsecops-pipeline:local; then pass; else fail; fi
else
    skip "trivy and/or docker not installed"
fi

echo
if [ "$FAILED" -eq 0 ]; then
    printf "\033[1;32mAll scans passed. Safe to push.\033[0m\n"
else
    printf "\033[1;31mOne or more scans failed. Fix before pushing.\033[0m\n"
    exit 1
fi
