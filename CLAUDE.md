# CLAUDE.md — SecVPN Project Rules

## Project Overview

SecVPN is a portfolio-grade WireGuard VPN application consisting of:
- **`client/`** — SwiftUI macOS menu bar application with a privileged XPC helper
- **`backend/`** — FastAPI service for auth, server registry, peer provisioning
- **`node-agent/`** — Lightweight FastAPI service deployed on each VPN node
- **`infra/`** — Terraform + Ansible for infrastructure provisioning

> **No Apple Developer account required.** The client uses the subprocess + wireguard-tools pattern (Option B) rather than the Network Extension framework. The app is self-signed for local use only and is not distributed via the App Store.

## Architecture Invariants

These decisions are fixed and must not be reversed without an ADR:

1. **Client-side key generation only.** WireGuard private keys are generated on the client and never transmitted. The backend receives and stores only public keys.
2. **Node agent pattern.** The backend never SSHes into VPN nodes. All node interaction goes through the node-agent REST API over mTLS.
3. **PostgreSQL in all environments.** No SQLite, even in local dev. Use Docker Compose.
4. **JWT + Keychain.** Access tokens (15 min TTL), rotating refresh tokens (30 days). Client stores all credentials in macOS Keychain, never UserDefaults.

## Repository Layout

```
sec-vpn/
├── client/          # SwiftUI macOS menu bar app + privileged XPC helper
├── backend/         # FastAPI backend
├── node-agent/      # Per-node WireGuard manager
├── infra/           # Terraform + Ansible
├── docs/            # Architecture docs, ADRs
└── docker-compose.yml
```

---

## Python (backend/ and node-agent/)

### Toolchain
- Python 3.12+
- `pyproject.toml` with `[build-system]` using `hatchling`
- **Formatter/linter**: `ruff` (replaces black + isort + flake8)
- **Type checker**: `mypy --strict`
- **Test runner**: `pytest` with `pytest-asyncio`
- **HTTP framework**: FastAPI with Pydantic v2
- **ORM**: SQLAlchemy 2.0 async (`AsyncSession`)
- **Migrations**: Alembic

### Code Standards
- All functions must have type annotations. No `Any` unless unavoidable and commented.
- Use `pydantic.BaseModel` for all request/response schemas. Never return raw dicts from endpoints.
- Business logic lives in `services/`, not in route handlers. Route handlers validate input and call services.
- Database models live in `models/`, Pydantic schemas in `schemas/`. Keep them separate.
- Use `async def` throughout. No synchronous database calls.
- Environment config via `pydantic_settings.BaseSettings` in `core/config.py`. No `os.getenv()` scattered through code.
- Secrets (database URL, JWT secret, mTLS certs) come from environment variables or mounted secrets. Never hardcode.

### Error Handling
- Raise `HTTPException` with explicit status codes from route handlers.
- Define custom exception classes in `core/exceptions.py` for domain errors.
- All exceptions must be logged before being re-raised or converted to HTTP responses.

### Testing
- Minimum 80% coverage on `services/` layer.
- Use `pytest-asyncio` with `asyncio_mode = "auto"` in `pyproject.toml`.
- Use `httpx.AsyncClient` with `app` dependency for integration tests.
- Do not mock the database in integration tests — use a test PostgreSQL instance via Docker.
- Unit tests may mock external calls (node agent HTTP, email).

### File Naming
- All Python files: `snake_case.py`
- One module per file. No `utils.py` dumping grounds — name files by what they contain.

---

## Swift (client/)

### Toolchain
- Swift 5.10+, Xcode 15+
- SwiftLint (enforced in CI)
- Swift Package Manager for dependencies
- Key dependencies: `KeychainAccess`
- System dependency: `wireguard-tools` installed via Homebrew (`brew install wireguard-tools`)
- No Apple Developer account required. App is self-signed with a local development certificate.

### Project Structure
Two targets:
- **`SecVPN`** — SwiftUI menu bar app (`MenuBarExtra`). All UI, API calls, and tunnel state live here.
- **`SecVPNHelper`** — Privileged XPC LaunchDaemon helper. The only process that runs as root. Executes `wg-quick up/down` and `wg show`. Registered via `SMAppService` (macOS 13+).

The helper is the **only** entry point for privileged operations. The main app communicates exclusively via a typed XPC protocol (`HelperToolProtocol`). No `AuthorizationExecuteWithPrivileges` — that API is deprecated.

Feature folders under `SecVPN/Features/` follow the pattern: `FeatureName/FeatureNameView.swift`, `FeatureNameViewModel.swift`, `FeatureNameModel.swift`.

### WireGuard Key Generation
Without `WireGuardKit`, generate keys using `wg genkey` / `wg pubkey` via the helper tool, or use CryptoKit's Curve25519 directly:
```swift
import CryptoKit
let privateKey = Curve25519.KeyAgreement.PrivateKey()
let publicKey = privateKey.publicKey
```
Store the private key in Keychain immediately. Never hold it in a plain `String`.

### Code Standards
- MVVM architecture. Views are dumb — no business logic, no direct network calls.
- `@Observable` macro (macOS 14+) for view models. No `ObservableObject` unless targeting older OS.
- All network requests go through `Networking/APIClient.swift`. No `URLSession` calls scattered through view models.
- All Keychain access goes through `Keychain/KeychainService.swift`.
- All privileged tunnel operations go through `Helper/HelperClient.swift` (the XPC client wrapper). Never call the helper directly from views or view models.
- Use `async/await` for all async operations. No callbacks or Combine unless integrating with system APIs that require it.
- `struct` by default. Use `class` only when reference semantics are required.
- No force-unwraps (`!`) except in test code.

### Security Rules (Swift)
- WireGuard private key generated via CryptoKit and stored in Keychain before the key variable goes out of scope.
- JWT tokens stored in Keychain with `kSecAttrAccessibleAfterFirstUnlock` accessibility.
- The XPC helper must validate every incoming command against an allowlist before executing any subprocess. Never pass raw user input to a shell command.
- All API calls must go over HTTPS. Certificate pinning is required before Milestone 7.

### Testing
- Unit test ViewModels with mocked API client and mocked `HelperClient`.
- UI tests for the critical flows: login, server selection, connect/disconnect.

---

## Infrastructure (infra/)

### Toolchain
- Terraform >= 1.7 with OpenTofu compatibility in mind
- Ansible >= 2.16
- Target cloud: Hetzner Cloud (primary), with modules designed to be provider-agnostic

### Standards
- All Terraform resources must be tagged with `project = "sec-vpn"` and `environment`.
- Remote state in Terraform Cloud or S3-compatible backend. Never commit `.tfstate`.
- Ansible roles must be idempotent. Running a playbook twice must produce no changes on the second run.
- All secrets (WireGuard node API keys, mTLS certs) are managed via Ansible Vault or passed as environment variables. Never committed to the repo.

---

## Development Workflow

| Concern | Tooling | Who |
|---|---|---|
| Backend (`backend/`, `node-agent/`) | VS Code / Claude Code CLI | Assistant commits directly |
| Infrastructure (`infra/`) | VS Code / Claude Code CLI | Assistant commits directly |
| Swift client (`client/`) | Xcode | User commits; assistant provides the commit message |

**Rule:** Backend and Swift changes are never mixed in the same commit. When the assistant finishes a backend task it commits immediately and reports what was committed. When the user completes a Swift task in Xcode, the assistant will say exactly what to commit and with what message.

---

## Git Conventions

### Branch Naming
```
feat/short-description
fix/short-description
chore/short-description
docs/short-description
```

### Commit Messages
Follow Conventional Commits:
```
feat(backend): add peer provisioning endpoint
fix(client): resolve keychain read race on launch
chore(infra): upgrade terraform provider to 3.x
```

- Subject line: imperative mood, max 72 chars, no period.
- Body: explain *why*, not *what*. Reference issue numbers.

### Pull Requests
- Every PR requires a description with: what changed, why, how to test.
- No PR merges without passing CI.
- Squash merge for feature branches. Merge commit for release branches.

---

## Security Baseline

- **No secrets in code or git history.** Use `git-secrets` or `gitleaks` pre-commit hook.
- **Dependency scanning**: `pip-audit` in backend CI, `swift package audit` equivalent in Swift CI.
- **All inter-service communication is authenticated.** Backend→node-agent uses mTLS client certificates.
- **Input validation**: All user-facing inputs validated by Pydantic (backend) or custom validators (Swift) before processing.
- **Rate limiting**: Auth endpoints (`/auth/login`, `/auth/register`) rate-limited to 10 req/min per IP via `slowapi`.
- **CORS**: Restricted to known origins. No wildcard `*` in production.
- **SQL injection**: Use SQLAlchemy ORM or parameterized queries exclusively. No string-formatted SQL.

---

## CI/CD (GitHub Actions)

### Backend pipeline (`.github/workflows/backend-ci.yml`)
1. `ruff check` + `ruff format --check`
2. `mypy --strict`
3. `pytest` with coverage report
4. `pip-audit` for known vulnerabilities

### Swift pipeline (`.github/workflows/swift-ci.yml`)
1. `swiftlint`
2. `xcodebuild test` for unit + UI tests

### Rules
- CI must pass on every PR before merge.
- Main branch is protected. No direct pushes.
- Secrets stored in GitHub Actions secrets, never in workflow files.

---

## Development Roadmap

### Milestone 1 — Foundation (Week 1)
- [ ] Repo scaffold: all directories, `.gitignore`, `pyproject.toml`s, `docker-compose.yml`
- [ ] Docker Compose: PostgreSQL + Redis + backend skeleton
- [ ] FastAPI app: health endpoint, structured logging, Pydantic Settings config
- [ ] Alembic setup with initial migration
- [ ] GitHub Actions: ruff, mypy, pytest on backend

### Milestone 2 — Auth & User API (Week 2)
- [ ] User registration, login, JWT access + refresh tokens
- [ ] Password hashing (bcrypt), rate limiting (slowapi)
- [ ] Token refresh and logout endpoints
- [ ] Full test coverage for auth flows

### Milestone 3 — Server Registry & Node Agent (Week 3)
- [ ] Server model: id, name, country, city, public_key, endpoint, status
- [ ] Admin-only CRUD API for servers
- [ ] Node agent: add/remove WireGuard peers via `wg` subprocess
- [ ] mTLS between backend and node agents
- [ ] Health check polling from backend to nodes

### Milestone 4 — Peer Provisioning API (Week 4)
- [ ] `POST /v1/peers` — receives client pubkey, assigns IP, calls node agent, returns WireGuard config
- [ ] `DELETE /v1/peers/{id}` — removes peer from node
- [ ] `GET /v1/peers/config` — returns active WireGuard config block
- [ ] IP pool management (assign from CIDR, reclaim on disconnect)

### Milestone 5 — macOS Client Skeleton (Week 5–6)
- [ ] Xcode project with two targets: `SecVPN` (menu bar app) + `SecVPNHelper` (XPC daemon)
- [ ] `MenuBarExtra` SwiftUI popup: login screen, server list, connect/disconnect toggle, status indicator
- [ ] `KeychainService` for JWT + WireGuard private key storage
- [ ] `APIClient` with URLSession, token refresh middleware
- [ ] `HelperToolProtocol` XPC interface defined and both targets wired up

### Milestone 6 — Privileged Helper & Tunnel (Week 7–8)
- [ ] `SecVPNHelper` daemon: registers via `SMAppService`, runs as root
- [ ] Helper executes `wg-quick up/down` with a validated config file path (no raw user input to shell)
- [ ] Helper exposes `wg show` output back to main app for status polling
- [ ] WireGuard private key generated via CryptoKit, public key sent to backend
- [ ] Full connect/disconnect flow end-to-end
- [ ] Error propagation from helper → main app via XPC reply

### Milestone 7 — Multi-Server & Production Hardening (Week 9–10)
- [ ] Server picker UI (by country/latency)
- [ ] Terraform module for VPN node provisioning (Hetzner Cloud)
- [ ] Ansible playbook: WireGuard install + node agent deploy
- [ ] Sentry error reporting in backend and client
- [ ] Certificate pinning in `APIClient`
- [ ] README with architecture diagram, screenshots, setup guide

---

## Definition of Done

A feature is "done" when:
1. Code is merged to `main` with passing CI.
2. New endpoints have integration tests.
3. New UI flows have at least a unit-tested ViewModel.
4. Any new environment variable is documented in `.env.example`.
5. Breaking API changes bump the version in `docs/api/`.
