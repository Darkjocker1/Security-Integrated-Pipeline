# Security Policy

## Supported Versions

Only the latest commit on `main` is supported. Every push to `main` must pass
the full security pipeline (SAST, secrets scan, dependency scan, container
scan) before an image is published.

## Reporting a Vulnerability

This is a personal portfolio project, but responsible disclosure is still
welcome:

1. **Do not** open a public issue for security vulnerabilities.
2. Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guided-security-advisory-creation-and-triage/privately-reporting-a-security-vulnerability)
   on this repository.
3. Include steps to reproduce, affected endpoints/files, and impact.

You can expect an acknowledgement within 7 days.

## Scope

In scope: the Flask application (`app/`), Dockerfile, and CI/CD workflows.
Out of scope: vulnerabilities in third-party dependencies already flagged by
`pip-audit`/Trivy (these are remediated by version bumps as fixes are released).
