# SecVPN

A portfolio-grade WireGuard VPN application built with a SwiftUI macOS menu bar client, a FastAPI backend, and a per-node agent architecture. Designed to demonstrate production-quality full-stack and systems engineering across Swift, Python, and infrastructure-as-code.

> **Status:** Active development — Milestone 2 complete, working towards a fully functional VPN client by Milestone 7.

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

## Built With

![Swift](https://img.shields.io/badge/Swift_5.10-F54A2A?style=flat-square&logo=swift&logoColor=white)
![SwiftUI](https://img.shields.io/badge/SwiftUI-007AFF?style=flat-square&logo=swift&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic_v2-E92063?style=flat-square&logo=pydantic&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-6BA81E?style=flat-square&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis_7-DC382D?style=flat-square&logo=redis&logoColor=white)
![WireGuard](https://img.shields.io/badge/WireGuard-88171A?style=flat-square&logo=wireguard&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat-square&logo=terraform&logoColor=white)
![Ansible](https://img.shields.io/badge/Ansible-EE0000?style=flat-square&logo=ansible&logoColor=white)
![Hetzner](https://img.shields.io/badge/Hetzner-D50C2D?style=flat-square&logo=hetzner&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)
![ruff](https://img.shields.io/badge/ruff-D7FF64?style=flat-square&logo=ruff&logoColor=black)
![mypy](https://img.shields.io/badge/mypy-2A6DB2?style=flat-square&logoColor=white)
![GitHub Copilot](https://img.shields.io/badge/GitHub_Copilot-000000?style=flat-square&logo=github-copilot&logoColor=white)
![Claude Code](https://img.shields.io/badge/Claude_Code-D97757?style=flat-square&logo=anthropic&logoColor=white)

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

# Apply database migrations
alembic upgrade head

# Run tests
pytest -v

# Start dev server (http://localhost:8000)
uvicorn app.main:app --reload
```

With `DEBUG=true` in `.env`, the Swagger UI is available at `http://localhost:8000/docs`.

## Roadmap

- [x] Milestone 1 — Repo scaffold, Docker Compose, FastAPI skeleton, CI pipeline
- [x] Milestone 2 — Auth: user registration, JWT access + refresh tokens, `GET /auth/me`
- [ ] Milestone 3 — Server registry, node agent, mTLS
- [ ] Milestone 4 — Peer provisioning API, IP pool management
- [ ] Milestone 5 — macOS client skeleton (menu bar UI grouped by country, Keychain, API client)
- [ ] Milestone 6 — Privileged XPC helper, WireGuard tunnel, end-to-end connect flow
- [ ] Milestone 7 — Multi-country server picker, Terraform/Ansible, production hardening

## Planned Extensions

Once the core VPN is complete, the architecture is designed to support a next-generation security layer, including DNS-level threat filtering, traffic anomaly detection, and smart server selection powered by threat intelligence feeds.
