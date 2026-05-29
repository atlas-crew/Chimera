# HIPAA Evidence Endpoints

Chimera exposes HIPAA-relevant healthcare routes for security testing and evidence
collection. These routes are intentionally vulnerable demo endpoints. They provide
technical evidence for tools such as Crucible, but they do not represent HIPAA
compliance, legal advice, audit readiness, or a covered-entity/business-associate
attestation.

Use HHS HIPAA Security Rule materials as the authority for safeguard content.
Chimera only documents endpoint behavior, seeded data expectations, and known
gaps for repeatable local testing.

## Current Evidence Routes

| Evidence area | Method | Path | Current behavior |
| --- | --- | --- | --- |
| Emergency access | `POST` | `/api/v1/healthcare/records/emergency-access` | Returns `400` when `justification` is missing and `200` with an emergency access token when justification is supplied. |
| Patient export | `POST` | `/api/v1/healthcare/records/export` | Returns export metadata for requested `patient_ids`; `X-Skip-Audit: true` makes `audit_logged` false. |
| Minimum necessary access | `GET` | `/api/v1/healthcare/records/{record_id}` | Returns full patient record details for seeded records without role filtering. |
| Audit suppression | `POST` | `/api/v1/admin/audit/suspend` | Returns `200` and records suppression evidence by default; `strict_mode: true` returns a `403` denial comparison. |

## Crucible Scenario Alignment

The initial Crucible HIPAA pack maps to these Chimera routes:

| Crucible scenario | Chimera route status | Notes |
| --- | --- | --- |
| `compliance-hipaa-emergency-access` | Route-compatible | The missing-justification step is deterministic; add audit-log side effects if consumers need a separate audit artifact. |
| `compliance-hipaa-patient-export` | Route-compatible | Current export output is metadata-only; stronger redaction evidence needs a deterministic payload with explicit note-exclusion metadata. |
| `compliance-hipaa-minimum-necessary` | Path-compatible, fixture gap | `P-88210`, `psychotherapy_notes`, `invoice_id`, and role-specific filtering are not yet deterministic in Chimera. |
| `compliance-hipaa-audit-suppression` | Route-compatible, behavior decision pending | Choose whether assessment evidence should rely on WAF/proxy blocking or Chimera's existing `strict_mode: true` denial behavior. |

## Deterministic Fixture Gaps

Before claiming a fully runnable HIPAA evidence slice, add or confirm:

- A stable healthcare record fixture for the minimum-necessary scenario, or a
  scenario rewrite to an existing seeded record such as `REC-FEDRAMP-A-001`.
- Role-aware response behavior for `clinical_token` and `billing_token`, including
  a billing payload that includes `invoice_id` and excludes `psychotherapy_notes`.
- Explicit export redaction metadata for psychotherapy notes and internal
  administrative notes if consumers need field-level proof rather than
  request/response metadata.
- An audit-log identifier or side effect on emergency and export flows if consumers
  need evidence beyond response bodies.

## Validation

The static OpenAPI spec documents the current route presence in
`apps/vuln-api/docs/openapi.yaml`. Validate behavior with the Starlette app factory:

```bash
cd apps/vuln-api
uv run python - <<'PY'
from starlette.testclient import TestClient
from app.asgi import create_app

client = TestClient(create_app())
checks = [
    (
        "POST",
        "/api/v1/healthcare/records/export",
        {"patient_ids": ["P-12345"], "format": "json"},
        {"X-Skip-Audit": "true"},
    ),
    ("POST", "/api/v1/healthcare/records/emergency-access", {"patient_id": "P-12345"}, {}),
    (
        "POST",
        "/api/v1/healthcare/records/emergency-access",
        {"patient_id": "P-12345", "justification": "Emergency life-saving procedure required."},
        {},
    ),
    ("GET", "/api/v1/healthcare/records/REC-FEDRAMP-A-001", None, {}),
    (
        "POST",
        "/api/v1/admin/audit/suspend",
        {"duration_minutes": 10, "reason": "Maintenance", "strict_mode": True},
        {},
    ),
]

for method, path, body, headers in checks:
    response = client.request(method, path, json=body, headers=headers)
    print(method, path, response.status_code)
PY
```

Run focused API tests after behavior changes:

```bash
cd apps/vuln-api
uv run pytest tests/unit/test_healthcare_routes.py tests/unit/test_admin_routes.py -q
```
