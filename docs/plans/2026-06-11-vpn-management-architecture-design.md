# VPN Management System Architecture Design

## 1. Goal

Build a secure web-based VPN management platform that centralizes VPN administration, user provisioning, monitoring, and security observability.

The first version should support a strong demo and remain realistic to extend into a production-grade platform.

## 2. Scope

### In scope
- Web authentication and authorization
- Role-based access control for Admin, User, and Auditor
- VPN user lifecycle management
- VPN configuration generation for WireGuard
- Session visibility and basic connection tracking
- Audit logging and security event logging
- Simple threat detection rules for suspicious behavior
- Admin dashboard for operational visibility
- Deployment with Docker Compose

### Out of scope for the first version
- Multi-region VPN routing
- Mobile applications
- Advanced machine learning detection
- Full SIEM replacement
- Complex enterprise SSO integrations

## 3. Recommended Architecture

### Recommendation
Use a modular monolith backend with clearly separated domains, plus a dedicated VPN controller integration layer and a separate monitoring stack.

This is the best balance for a student project because it:
- is easier to build and debug than microservices
- keeps the codebase organized by domain
- still allows clear separation between auth, VPN control, monitoring, and auditing
- makes demo and deployment simpler

### High-level components

- `frontend`: Next.js or React dashboard
- `backend`: FastAPI application for auth, API, RBAC, business logic, and audit logging
- `vpn-controller`: internal service/module for WireGuard config generation and lifecycle operations
- `monitoring-stack`: Prometheus, Grafana, and optional log aggregation
- `database`: PostgreSQL for users, roles, sessions, configs, logs, and alerts
- `infra`: Docker Compose, environment templates, TLS setup, and deployment scripts

## 4. Core Domain Modules

### 4.1 Authentication and Authorization
Responsibilities:
- login and logout
- JWT issuance and validation
- MFA enrollment and verification
- RBAC enforcement

Key roles:
- `Admin`: full control over users, policies, logs, and system settings
- `User`: manage own VPN access and config
- `Auditor`: read-only access to logs, sessions, and security reports

### 4.2 VPN User Management
Responsibilities:
- create, disable, re-enable, and delete VPN users
- manage expiration windows and access status
- track assigned keys and certificates
- regenerate WireGuard configuration

### 4.3 VPN Session Monitoring
Responsibilities:
- show currently online users
- display source IP, device, session start time, and traffic totals
- expose connection history for auditing

### 4.4 Security Logging
Responsibilities:
- record login attempts and failures
- store privileged admin actions
- capture suspicious activity events
- record VPN configuration generation and revocation events

### 4.5 Threat Detection
Responsibilities:
- detect brute-force login attempts
- detect abnormal login frequency or location changes
- detect unusual traffic spikes
- generate alerts for audit review

## 5. Proposed Repository Structure

```text
vpn-management-system/
├── frontend/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   ├── users/
│   │   │   ├── vpn/
│   │   │   ├── sessions/
│   │   │   ├── audit/
│   │   │   └── threats/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   └── main.py
├── vpn-controller/
├── monitoring/
├── infra/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── security/
│   └── plans/
└── README.md
```

## 6. Data Model Overview

Core entities:
- `users`
- `roles`
- `permissions`
- `vpn_profiles`
- `vpn_keys`
- `vpn_sessions`
- `audit_logs`
- `security_events`
- `alerts`
- `mfa_factors`

Relationships:
- one user can have one or more roles
- one user can own one or more VPN profiles
- one profile can generate one or more keys over time
- one session belongs to one user and one VPN profile
- one audit log entry records one system event

## 7. API Design Principles

The backend should expose RESTful endpoints grouped by domain:
- `/api/auth`
- `/api/users`
- `/api/vpn`
- `/api/sessions`
- `/api/audit`
- `/api/threats`
- `/api/admin`

API requirements:
- HTTPS only
- JWT validation on protected routes
- role checks on every sensitive endpoint
- rate limiting for authentication endpoints
- consistent error response format

## 8. Security Requirements

### Web security
- secure password hashing
- CSRF protection where applicable
- input validation and output encoding
- secure session and token handling
- strict CORS policy

### Network security
- TLS for web traffic
- WireGuard for VPN traffic
- firewall rules for management interfaces
- least-privilege network access

### Application security
- RBAC enforcement
- MFA for privileged accounts
- audit logging for privileged operations
- revocation support for users and keys
- rate limiting and lockout policy for brute-force defense

## 9. Monitoring and Logging

Monitoring should be split into two layers:

### Operational metrics
- API request latency
- authentication success/failure counts
- VPN session counts
- config generation counts
- active user counts

### Security telemetry
- failed login bursts
- suspicious IP or device changes
- unusual traffic spikes
- repeated revoked-account access attempts

Recommended stack:
- Prometheus for metrics
- Grafana for dashboards
- optional Loki or ELK for logs

## 10. Key User Flows

### Admin flow
1. Admin logs in
2. Admin completes MFA
3. Admin creates a VPN user
4. System generates WireGuard configuration
5. Admin reviews active sessions and alerts
6. Admin disables or revokes access if needed

### User flow
1. User logs in
2. User downloads own VPN configuration
3. User connects to VPN
4. User checks connection status and usage history

### Auditor flow
1. Auditor logs in
2. Auditor reviews audit logs and suspicious events
3. Auditor exports reports for review

## 11. Deployment Architecture

Recommended deployment setup:
- `frontend` and `backend` in separate containers
- `postgres` as dedicated database container
- `prometheus` and `grafana` as observability containers
- `wireguard` or a controller container with host access where necessary
- reverse proxy such as Nginx or Traefik for TLS termination

Use Docker Compose for development and demo environments.

## 12. Milestone Plan

### Phase 1: Foundation
- repository structure
- backend skeleton
- frontend skeleton
- database schema
- authentication flow

### Phase 2: VPN Control
- user provisioning
- WireGuard config generation
- access revocation
- basic admin operations

### Phase 3: Monitoring and Audit
- session tracking
- audit logs
- dashboard metrics
- alerts for suspicious behavior

### Phase 4: Hardening
- MFA
- rate limiting
- permission refinement
- security test cases

## 13. Risks and Trade-offs

### Main risks
- WireGuard integration may require careful host-level setup
- monitoring scope can expand beyond the time available
- threat detection can become too ambitious if ML is included too early

### Mitigations
- keep detection rules simple for the first version
- avoid microservices until the product proves itself
- prioritize demo stability over feature breadth

## 14. Final Recommendation

Build the project as a secure modular monolith with a separate VPN controller integration layer and a lightweight monitoring stack.

This architecture is the most practical choice for a GitHub-based academic project because it is:
- easy to explain
- easy to demo
- secure enough to be credible
- structured enough to grow later
