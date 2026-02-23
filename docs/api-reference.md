# API Reference

Complete endpoint catalog for the Chimera API. All endpoints are prefixed as shown, and most return JSON.

> **Interactive docs**: Start the server and visit `/swagger` for Swagger UI or `/apidocs` for Flasgger's auto-generated docs.

## Authentication

Most endpoints accept requests without authentication (intentionally). Endpoints that check auth use:

- **Bearer token**: `Authorization: Bearer <jwt>`
- **API key header**: `X-API-Key: <key>`
- **Session cookie**: Set after login via `/api/v1/auth/login`

---

## System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health check (always returns `{"status": "healthy"}`) |
| GET | `/` | Web portal (SPA mode) or demo template (API-only mode) |
| GET | `/swagger` | Swagger UI |
| GET | `/openapi.yaml` | OpenAPI spec |

## Auth (30 routes)

Authentication, authorization, JWT, MFA, API keys, and session management.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/auth/methods` | Authentication methods discovery |
| POST | `/api/v1/auth/login` | Login (JWT algorithm confusion, SQLi) |
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/forgot-password` | Password reset request |
| POST | `/api/v1/auth/reset-password` | Password reset with token |
| POST | `/api/v1/auth/refresh` | Token refresh |
| POST | `/api/v1/auth/verify-mfa` | MFA verification |
| POST | `/api/v1/auth/enroll-mfa` | MFA enrollment |
| POST | `/api/v1/auth/api-keys` | Create API key |
| DELETE | `/api/v1/auth/api-keys/<key_id>` | Revoke API key |
| POST | `/api/v1/device/register` | Device registration |
| POST | `/api/v1/auth/verify` | Email/code verification |
| GET | `/api/v1/auth/sessions` | List active sessions |
| POST | `/api/v1/auth/logout` | Logout |
| POST | `/api/v1/auth/token/forge` | Token forgery endpoint |

## Banking (29 routes)

Account management, wire transfers, KYC, and mobile banking operations.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/accounts/balance` | Account balance inquiry |
| GET | `/api/v1/accounts/list` | Account enumeration |
| POST | `/api/v1/transfers/wire` | Wire transfer |
| POST | `/api/v1/transfers/initiate` | Transfer initiation |
| PUT | `/api/v1/transactions/<id>/modify` | Transaction modification |
| GET | `/api/v1/customers/export` | Customer data export |
| POST | `/api/v1/banking/kyc/documents` | KYC document upload |
| GET | `/api/v1/banking/kyc/documents/<id>` | KYC document retrieval |
| POST | `/api/v1/banking/beneficiaries` | Add beneficiary |
| GET | `/api/v1/banking/beneficiaries` | List beneficiaries |

## Healthcare (31 routes)

HIPAA records, PHI/PII exposure, medical claims, and provider operations.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/healthcare/records` | List medical records |
| GET | `/api/v1/healthcare/records/<id>` | Get medical record (PHI exposure) |
| POST | `/api/v1/healthcare/records` | Create medical record |
| PUT | `/api/v1/healthcare/records/<id>` | Update medical record |
| GET | `/api/hipaa/records/patient` | Patient lookup (IDOR) |
| POST | `/api/hipaa/records/bulk-export` | Bulk PHI export |
| POST | `/api/v1/healthcare/claims/submit` | Submit insurance claim |
| GET | `/api/v1/healthcare/claims/<id>` | Claim details |
| GET | `/api/v1/healthcare/providers/<id>` | Provider info |

## E-commerce (48 routes)

Cart manipulation, checkout flow, gift cards, product management, and order exports.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/ecommerce/products` | Product listing |
| POST | `/api/cart/add` | Add to cart |
| PUT | `/api/cart/update` | Update cart (negative quantity) |
| POST | `/api/checkout/process` | Process checkout |
| POST | `/api/v1/ecommerce/gift-cards/create` | Create gift card |
| POST | `/api/v1/ecommerce/gift-cards/redeem` | Redeem gift card |
| GET | `/api/v1/ecommerce/gift-cards/<code>/balance` | Check gift card balance |
| POST | `/api/v1/ecommerce/orders/export` | Order data export |
| GET | `/api/v1/ecommerce/orders/<id>` | Order details |

## Insurance (42 routes)

Policy management, claims processing, underwriting rules, and actuarial models.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/insurance/policies` | List policies |
| POST | `/api/v1/insurance/policies` | Create policy |
| GET | `/api/v1/insurance/policies/<id>` | Policy details |
| POST | `/api/v1/insurance/claims` | Submit claim |
| GET | `/api/v1/insurance/claims/<id>` | Claim details |
| POST | `/api/v1/insurance/claims/<id>/evidence` | Upload evidence |
| GET | `/api/v1/insurance/underwriting/rules` | Underwriting rules |
| POST | `/api/v1/insurance/underwriting/rules` | Create underwriting rule |
| GET | `/api/v1/insurance/actuarial/models` | Actuarial models |

## SaaS (30 routes)

Multi-tenant operations, SAML SSO, billing, workspace settings, and audit logs.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/saas/tenants` | Create tenant |
| GET | `/api/v1/saas/tenants/<id>` | Tenant details |
| POST | `/api/v1/saas/projects` | Create project |
| GET | `/api/v1/saas/projects/<id>` | Project details |
| POST | `/api/v1/saas/shared-links` | Create shared link |
| POST | `/api/v1/saas/billing/invoices` | Generate invoice |
| GET | `/api/v1/saas/billing/usage` | Usage metrics |
| PUT | `/api/v1/saas/workspace/settings` | Update workspace settings |
| POST | `/api/v1/saas/auth/saml/config` | Configure SAML SSO |
| GET | `/api/v1/saas/audit-logs` | Audit log retrieval |

## Government (28 routes)

Citizen services, identity access, benefits applications, and classified data.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/gov/cases` | Create case |
| GET | `/api/v1/gov/cases/<id>` | Case details |
| GET | `/api/v1/gov/records` | Public records search |
| POST | `/api/v1/gov/benefits/apply` | Benefits application |
| GET | `/api/v1/gov/benefits/search` | Benefits search (SQLi) |
| POST | `/api/v1/gov/access-cards` | Issue access card |
| GET | `/api/v1/gov/classifications/<id>` | Classification lookup |
| POST | `/api/v1/gov/permits` | Permit application |
| GET | `/api/v1/gov/service-requests` | Service requests |

## Telecom (23 routes)

SIM swap, CDR exports, number porting, device bindings, and roaming.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/telecom/sim-swap` | SIM swap request |
| GET | `/api/v1/telecom/subscribers/<id>` | Subscriber details |
| POST | `/api/v1/telecom/cdr/export` | CDR export |
| POST | `/api/v1/telecom/porting` | Number porting request |
| POST | `/api/v1/telecom/device/activate` | Device activation |
| POST | `/api/v1/telecom/device/bind` | Device binding |
| PUT | `/api/v1/telecom/roaming/override` | Roaming override |
| GET | `/api/v1/telecom/network/towers` | Network tower listing |

## Energy & Utilities (23 routes)

SCADA dispatch, meter management, grid control, and demand response.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/energy-utilities/dispatch` | SCADA dispatch command |
| POST | `/api/v1/energy-utilities/load-shed` | Load shedding |
| POST | `/api/v1/energy-utilities/breakers/trip` | Circuit breaker control |
| GET | `/api/v1/energy-utilities/meters/<id>/readings` | Meter readings |
| POST | `/api/v1/energy-utilities/meters/<id>/disconnect` | Remote disconnect |
| POST | `/api/v1/energy-utilities/meters/<id>/firmware` | Firmware update |
| POST | `/api/v1/energy-utilities/demand-response` | Demand response event |
| PUT | `/api/v1/energy-utilities/tariffs/override` | Tariff override |

## Payments (18 routes)

Card processing, refunds, merchant management, and fraud rules.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/payments/process` | Process payment |
| POST | `/api/payments/authorize` | Authorize payment |
| POST | `/api/payments/capture` | Capture payment |
| POST | `/api/payments/refund` | Issue refund |
| POST | `/api/cards/validate` | Card validation |
| POST | `/api/merchant/onboard` | Merchant onboarding |
| GET | `/api/payments/fraud-rules` | Fraud detection rules |
| POST | `/api/payments/bulk-process` | Bulk payment processing |

## Mobile (15 routes)

Biometric bypass, certificate pinning, device trust, and session transfer.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/mobile/v2/config/app-settings` | App configuration |
| GET | `/api/mobile/v2/auth/biometric/supported-methods` | Biometric methods |
| POST | `/api/mobile/v2/auth/biometric/verify` | Biometric verification |
| POST | `/api/mobile/v2/auth/session/transfer` | Session hijacking |
| POST | `/api/mobile/v2/security/integrity-check` | Root/jailbreak detection |
| POST | `/api/mobile/device/fingerprint` | Device fingerprinting |
| POST | `/api/mobile/device/trust/permanent` | Persistent device trust |

## Attack Simulation (25 routes)

Red team simulation endpoints for various attack vectors.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/admin/system/execute` | Command injection |
| POST | `/api/v1/admin/files/read` | Path traversal |
| POST | `/api/integrations/webhook/register` | SSRF via webhook |
| POST | `/api/v1/admin/config/import` | XXE injection |
| POST | `/api/v1/admin/data/deserialize` | Insecure deserialization |

## Compliance (16 routes)

AML monitoring, sanctions screening, audit trails, and regulatory reporting.

## Loyalty (14 routes)

Points management, rewards, and redemption.

## Integrations (13 routes)

Webhook registration, SSRF targets, and third-party connectors.

## Infrastructure (18 routes)

Cloud configuration, secrets management, and deployment.

## ICS/OT (10 routes)

Industrial control system and operational technology endpoints.

## Security Ops (8 routes)

Blue team tools and defensive operations.

## GenAI (4 routes)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/genai/chat` | AI chat (prompt injection) |
| POST | `/api/v1/genai/complete` | Text completion |
| GET | `/api/v1/genai/models` | List available models |
| POST | `/api/v1/genai/embeddings` | Generate embeddings |

## Diagnostics (2 routes)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/diagnostics/ping` | Network diagnostic (command injection) |
| POST | `/api/v1/diagnostics/resolve` | DNS resolution |

## Recorder (3 routes)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/recorder/traffic` | Retrieve recorded traffic |
| GET | `/api/recorder/stats` | Traffic statistics |
| DELETE | `/api/recorder/clear` | Clear recorded traffic |

## Testing (7 routes)

Test utility endpoints for the testing framework.

## Throughput (2 routes)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/fast/ping` | Fast throughput ping |
| GET | `/fast/payload` | Throughput payload test |

---

## Error Responses

All API errors return JSON with a consistent structure:

```json
{
  "error": "Not found",
  "status": 404,
  "timestamp": "2026-02-20T12:00:00.000Z",
  "path": "/api/v1/nonexistent"
}
```

## Testing Headers

Common headers for vulnerability testing:

| Header | Purpose |
|--------|---------|
| `Authorization: Bearer <jwt>` | JWT authentication |
| `X-JWT-Algorithm: none` | Algorithm confusion attack |
| `X-Forwarded-For: 127.0.0.1` | IP spoofing |
| `X-User-Role: admin` | Role manipulation |
| `Content-Type: application/xml` | XXE injection trigger |
