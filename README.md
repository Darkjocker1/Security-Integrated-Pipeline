# DevSecOps Security Pipeline

[![Security Pipeline](https://github.com/markchen118/devsecops-pipeline/actions/workflows/security-pipeline.yml/badge.svg)](https://github.com/markchen118/devsecops-pipeline/actions/workflows/security-pipeline.yml)
[![PR Checks](https://github.com/markchen118/devsecops-pipeline/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/markchen118/devsecops-pipeline/actions/workflows/pr-checks.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A Flask REST API wrapped in a GitHub Actions CI/CD pipeline that gates every
deployment behind four security scans. If any scan finds a critical issue, the
pipeline fails and nothing ships. The application itself, a JWT-authenticated
notes API, is intentionally simple: it exists as realistic scan surface for
the security tooling.

## Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Security Gates](#security-gates)
- [Security Design Decisions](#security-design-decisions)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
- [Running the Security Scans Locally](#running-the-security-scans-locally)
- [Docker Deployment](#docker-deployment)
- [CI/CD Setup](#cicd-setup)
- [Project Structure](#project-structure)
- [What I Learned](#what-i-learned)
- [Roadmap](#roadmap)
- [License](#license)

## Overview

This project demonstrates the four core DevSecOps practices integrated into a
single automated pipeline:

| Practice | Meaning | Tool |
|----------|---------|------|
| SAST | Static analysis of application source code | Bandit |
| SCA | Scanning dependencies for known CVEs | pip-audit |
| Secrets detection | Catching credentials committed to git | Gitleaks |
| Container scanning | Scanning the built Docker image | Trivy |

Every push to `main` triggers the full pipeline. A finding at or above the
configured severity threshold in any stage fails the build and blocks the
image from being published.

## Pipeline Architecture

```
Push to main
     |
     +-- Lint and unit tests (flake8, black, pytest) --+
     +-- SAST (Bandit) --------------------------------+
     +-- Secrets scan (Gitleaks, full git history) ----+   run in parallel
     +-- SCA (pip-audit, PyPI Advisory DB) ------------+
     |
     v   (only if all four gates pass)
Build Docker image (multi-stage, non-root, python:3.11-slim)
     |
     v
Container scan (Trivy, fails on CRITICAL/HIGH)
     |
     v
Push image to Docker Hub (optional, gated behind a repository variable)
```

A second, lightweight workflow (`pr-checks.yml`) runs on every pull request:
lint, format check, unit tests, and a high-severity-only Bandit pass. This
gives reviewers fast feedback without running the full pipeline.

## Security Gates

| Stage | Tool | What it catches | Fail condition |
|-------|------|-----------------|----------------|
| SAST | [Bandit](https://bandit.readthedocs.io/) | Insecure code patterns such as `eval()`, SQL string building, weak crypto, debug mode | Medium+ severity |
| Secrets | [Gitleaks](https://github.com/gitleaks/gitleaks) | API keys, tokens, and passwords anywhere in git history | Any leak |
| SCA | [pip-audit](https://github.com/pypa/pip-audit) | Known CVEs in pinned Python dependencies | Any known CVE |
| Container | [Trivy](https://github.com/aquasecurity/trivy) | OS and library vulnerabilities in the built image | CRITICAL/HIGH with an available fix |

## Security Design Decisions

The application follows secure defaults, independent of the pipeline:

- No hardcoded secrets. All configuration is read from environment variables
  (python-dotenv locally, GitHub Secrets in CI). Production refuses to start
  if any required secret is missing.
- bcrypt password hashing with a per-password salt and adaptive work factor.
  Plaintext passwords are never stored.
- Generic authentication errors. Login returns an identical message for an
  unknown username and a wrong password, preventing username enumeration.
- IDOR protection. Every note query is scoped to the authenticated user's ID,
  so one user's notes return 404 for everyone else. A dedicated test proves
  this behaviour.
- Short-lived JWTs. Access tokens expire after 15 minutes; a 7-day refresh
  token allows silent renewal.
- Hardened container. Multi-stage build, slim base image, non-root runtime
  user, and a healthcheck. The development server binds to localhost only;
  Gunicorn serves production traffic inside the container.
- Input validation on every endpoint: username format, minimum password
  length, and size limits on note titles and content.

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | None | Create an account, returns a JWT pair |
| POST | `/api/auth/login` | None | Authenticate, returns a JWT pair |
| POST | `/api/auth/refresh` | Refresh token | Issue a new access token |
| GET | `/api/notes` | JWT | List the current user's notes |
| POST | `/api/notes` | JWT | Create a note |
| GET | `/api/notes/<id>` | JWT | Retrieve one note |
| PUT | `/api/notes/<id>` | JWT | Update a note |
| DELETE | `/api/notes/<id>` | JWT | Delete a note |
| GET | `/health` | None | Health check for orchestrators |
| GET | `/api/version` | None | Application version |

Protected endpoints expect an `Authorization: Bearer <access_token>` header.

## Getting Started

### Prerequisites

- Python 3.11 or later
- Git
- Docker Desktop (only for the containerised setup)

### Local development (SQLite, no database setup required)

```bash
git clone https://github.com/markchen118/devsecops-pipeline.git
cd devsecops-pipeline

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

python -m app.main               # serves on http://127.0.0.1:5000
```

### Smoke test

```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "averylongpassword"}'
```

### Run the test suite

```bash
pytest
```

## Running the Security Scans Locally

Each scan can be run individually, exactly as CI runs it:

```bash
bandit -r app -ll -ii            # SAST
pip-audit -r requirements.txt    # dependency CVEs
```

Or run everything (tests, Bandit, pip-audit, Gitleaks, and Trivy if
installed) with one script from Git Bash or WSL:

```bash
./scripts/run_local_scans.sh
```

## Docker Deployment

The containerised setup runs the app in production mode under Gunicorn,
backed by PostgreSQL.

```bash
cp .env.example docker/.env      # then fill in real values
cd docker
docker compose up --build        # API on http://localhost:8000
```

Generate strong secret values with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The `.env` file is excluded by `.gitignore` and must never be committed.

## CI/CD Setup

1. Push the repository to GitHub. The security pipeline runs automatically on
   every push to `main`; the PR workflow runs on every pull request.
2. Optional image publishing: under Settings, Secrets and variables, Actions,
   add the secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`, then create a
   repository variable `DOCKERHUB_ENABLED` with the value `true`. On the next
   push, the pipeline tags and pushes the image to Docker Hub.

## Project Structure

```
devsecops-pipeline/
|-- .github/workflows/
|   |-- security-pipeline.yml    Main pipeline (push to main)
|   `-- pr-checks.yml            Fast checks (pull requests)
|-- app/
|   |-- __init__.py              Application factory (create_app)
|   |-- main.py                  Entry point
|   |-- routes.py                Notes CRUD, health, version endpoints
|   |-- auth.py                  JWT auth and bcrypt password hashing
|   |-- models.py                User and Note models (SQLAlchemy)
|   |-- config.py                Environment-driven configuration
|   `-- extensions.py            Shared db and jwt instances
|-- tests/
|   |-- conftest.py              Pytest fixtures
|   |-- test_auth.py             Auth tests
|   `-- test_routes.py           CRUD, validation, and IDOR tests
|-- docker/
|   |-- Dockerfile               Multi-stage, non-root image
|   `-- docker-compose.yml       App plus PostgreSQL for local use
|-- scripts/
|   `-- run_local_scans.sh       Run every scan locally
|-- .bandit                      SAST configuration
|-- .gitleaks.toml               Secrets scan rules
|-- requirements.txt             Pinned runtime dependencies
`-- requirements-dev.txt         Test and scan tooling
```

## What I Learned

- Shift-left security: catching vulnerabilities in CI costs minutes, while
  catching them in production costs incidents. Running the same scans locally
  shortens the feedback loop even further.
- Each tool covers a different layer. Bandit sees the source code, pip-audit
  sees the dependencies, Gitleaks sees the git history, and Trivy sees the
  operating system layer underneath. No single scanner covers the full attack
  surface.
- Tuning matters. Raw scanner output is noisy, so meaningful gates required
  choosing severity thresholds (Bandit medium and above, Trivy CRITICAL/HIGH
  with unfixed findings ignored) and allowlisting test fixtures in Gitleaks.
  A permanently red pipeline just teaches a team to ignore it.
- Supply-chain hygiene. Pinning exact dependency versions makes pip-audit
  results reproducible, and pip-audit caught two real CVEs in this project's
  initial pins during development. A slim multi-stage image also sharply
  reduces the CVE count Trivy reports.

## Roadmap

- [ ] DAST stage with OWASP ZAP against a staging deployment
- [ ] Deployment to Render.com with a manual approval gate
- [ ] SBOM generation (CycloneDX) published as a pipeline artifact
- [ ] Rate limiting on auth endpoints (Flask-Limiter)

## License

MIT
