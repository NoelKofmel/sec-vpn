# SecVPN

A portfolio-grade WireGuard VPN application built with a SwiftUI macOS menu bar client, a FastAPI backend, and a per-node agent architecture. Designed to demonstrate production-quality full-stack and systems engineering across Swift, Python, and infrastructure-as-code.

> **Status:** Active development — Milestone 1 (foundation) complete, working towards a fully functional VPN client by Milestone 7.

## Architecture

```
macOS Client (SwiftUI + XPC Helper)
        │ HTTPS / JWT
        ▼
FastAPI Backend (auth, server registry, peer provisioning)
        │ mTLS
        ▼
Node Agents (per VPN server, manages WireGuard peers)
```

- **Client:** SwiftUI `MenuBarExtra` app with a privileged XPC helper that runs `wg-quick`. No Apple Developer account required — self-signed for local use.
- **Backend:** FastAPI + SQLAlchemy 2.0 async + PostgreSQL. JWT auth with rotating refresh tokens.
- **Node agent:** Lightweight FastAPI service on each VPN node, managing WireGuard peers via subprocess.
- **Infrastructure:** Terraform (Hetzner Cloud) + Ansible.

## Tech Stack

| Layer | Technology |
|---|---|
| macOS client | Swift 5.10, SwiftUI, CryptoKit, XPC |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis |
| Node agent | Python 3.12, FastAPI |
| Infrastructure | Terraform, Ansible, Hetzner Cloud |
| CI/CD | GitHub Actions |

## Local Development

### Prerequisites

- Docker Desktop
- Python 3.12 (`brew install python@3.12`)
- Xcode 15+ (for the Swift client)

### Backend

```bash
# Start PostgreSQL + Redis
docker compose up postgres redis -d

# Set up Python environment
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copy and configure environment
cp .env.example .env

# Run tests
pytest -v

# Start dev server (http://localhost:8000)
uvicorn app.main:app --reload
```

With `DEBUG=true` in `.env`, the Swagger UI is available at `http://localhost:8000/docs`.

## Roadmap

- [x] Milestone 1 — Repo scaffold, Docker Compose, FastAPI skeleton, CI pipeline
- [ ] Milestone 2 — Auth: user registration, JWT access + refresh tokens
- [ ] Milestone 3 — Server registry, node agent, mTLS
- [ ] Milestone 4 — Peer provisioning API, IP pool management
- [ ] Milestone 5 — macOS client skeleton (menu bar UI, Keychain, API client)
- [ ] Milestone 6 — Privileged XPC helper, WireGuard tunnel, end-to-end connect flow
- [ ] Milestone 7 — Multi-server UI, Terraform/Ansible, production hardening
