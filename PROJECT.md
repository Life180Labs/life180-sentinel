# Life180 Sentinel

## Vision

Life180 Sentinel is an AI-powered Repository Evaluation Platform.

The application should allow a user to paste a GitHub repository URL or select a connected repository.

The system will clone the repository, understand its structure, evaluate the codebase using AI, and generate a human-readable engineering report.

---

# Phase 1 Scope (MVP)

Only build the following features.

## Repository

- Paste GitHub Repository URL
- Clone Repository
- Store Repository Metadata

## Repository Intelligence

- Scan folders
- Scan files
- Detect programming languages
- Detect frameworks
- Detect package managers
- Detect databases
- Detect Docker usage
- Detect CI/CD
- Detect AI frameworks
- Build repository tree
- Build repository summary

## AI Evaluation

Evaluate:

- Architecture
- Backend
- Frontend
- Database
- Security
- Performance
- Testing
- Documentation

Generate:

- Overall Score
- Category Scores
- Findings
- Recommendations

## Report

Generate a human-readable report.

Display report inside the dashboard.

---

# Out of Scope

Do NOT build:

- Auto Fixes
- Pull Requests
- Code Injection
- Continuous Monitoring
- GitHub Webhooks
- Notifications
- Multi-Organization
- Billing

---

# Technology Stack

Frontend

- Next.js
- TypeScript
- TailwindCSS
- ShadCN UI

Backend

- FastAPI
- Python

Database

- PostgreSQL

ORM

- SQLAlchemy

Queue

- Redis

---

# Development Philosophy

Always keep the project runnable.

Never leave broken code.

Every feature must work before starting the next feature.

Build production-quality software.