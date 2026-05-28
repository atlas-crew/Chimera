# FedRAMP OpenAPI Extensions

Chimera exposes intentionally vulnerable endpoints for assessment tooling. FedRAMP
metadata is an annotation layer on top of that API surface: it describes why an
endpoint is relevant to a control assertion, what secure behavior would look like,
and which evidence a tool such as Crucible should collect. It does not mean the
endpoint is FedRAMP compliant.

Use official FedRAMP and NIST sources as the authority for control content. Chimera
stores only stable identifiers, short rationale text, and test-facing expectations.
The initial contract is grounded in FedRAMP Rev. 5 and should be revisited as the
2026 machine-readable package and continuous-monitoring rules settle.

## Operation Extensions

Add these fields to OpenAPI operations under `apps/vuln-api/docs/openapi.yaml`.

| Extension | Type | Required | Purpose |
| --- | --- | --- | --- |
| `x-fedramp-controls` | array of objects | yes for FedRAMP-relevant operations | Lists FedRAMP Rev. 5 controls this endpoint can exercise. |
| `x-vulnerability-class` | string | yes for FedRAMP-relevant operations | Machine-safe vulnerability or failure-mode family. |
| `x-expected-defense` | object | yes for FedRAMP-relevant operations | Describes the secure-mode behavior Crucible should expect. |
| `x-evidence-types` | array of strings | yes for FedRAMP-relevant operations | Names the evidence artifacts an assessment can collect. |

### `x-fedramp-controls`

Each entry maps one endpoint behavior to one FedRAMP control assertion.

```yaml
x-fedramp-controls:
  - framework: fedramp
    revision: rev5
    baselines: [moderate, high]
    family: AC
    controlId: AC-3
    assertion: tenant-resource-access-is-enforced
    role: primary
    rationale: Cross-tenant object access should be denied and logged.
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `framework` | string | yes | Use `fedramp`. |
| `revision` | string | yes | Use `rev5` until a later task adds other frameworks. |
| `baselines` | array | yes | Allowed values: `low`, `moderate`, `high`, `li-saas`. |
| `family` | string | yes | Uppercase NIST control family, such as `AC`, `AU`, `IA`, `SC`, `SI`, `CM`, or `RA`. |
| `controlId` | string | yes | Control ID such as `AC-3`, `IA-2`, or `AU-9(4)`. |
| `assertion` | string | yes | Machine-safe assertion slug used by Crucible scenario metadata. |
| `role` | string | yes | `primary`, `supporting`, or `manual`. |
| `rationale` | string | yes | One sentence explaining endpoint relevance. |

### `x-vulnerability-class`

Use one lower-kebab-case value per operation. Prefer stable technical classes over
framework language:

- `auth-bypass`
- `idor`
- `cross-tenant-access`
- `privilege-escalation`
- `audit-suppression`
- `insecure-configuration`
- `business-logic-abuse`
- `input-validation`
- `ssrf`
- `service-trust-abuse`
- `cryptographic-weakness`
- `sensitive-data-exposure`

### `x-expected-defense`

This object defines the secure behavior that contrasts with Chimera's vulnerable
mode. It should be specific enough for Crucible to assert the expected result.

```yaml
x-expected-defense:
  mode: strict
  behavior: deny-cross-tenant-resource
  successStatus: 403
  requiredSignals:
    - authorization-decision
    - audit-event
  notes: Full demo mode may intentionally return 200 with another tenant's resource.
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `mode` | string | yes | Usually `strict`; use `external` for evidence that must come from a proxy, TLS probe, or other system. |
| `behavior` | string | yes | Machine-safe expected-defense slug. |
| `successStatus` | integer or string | no | Expected status or status family such as `4xx`. |
| `requiredSignals` | array | no | Supporting signals from the allowed list below. |
| `notes` | string | no | Keep short and test-oriented. |

Allowed `requiredSignals` values for the first FedRAMP slice:

- `audit-event`
- `authentication-decision`
- `authorization-decision`
- `boundary-decision`
- `business-rule-decision`
- `config-change-event`
- `input-validation-decision`
- `rate-limit-event`

### `x-evidence-types`

Allowed values for the first FedRAMP slice:

- `request-response`
- `audit-log`
- `auth-token`
- `session-cookie`
- `tenant-fixture`
- `seeded-resource`
- `config-state`
- `runner-artifact`
- `tls-handshake`
- `openapi-operation`

## Example Operation

```yaml
/api/v1/saas/tenants/{tenant_id}/projects:
  get:
    tags: [SaaS]
    summary: List tenant projects
    x-fedramp-controls:
      - framework: fedramp
        revision: rev5
        baselines: [moderate, high]
        family: AC
        controlId: AC-3
        assertion: tenant-project-access-is-enforced
        role: primary
        rationale: Cross-tenant project reads should be denied and audited.
      - framework: fedramp
        revision: rev5
        baselines: [moderate, high]
        family: AU
        controlId: AU-2
        assertion: denied-tenant-access-is-auditable
        role: supporting
        rationale: Authorization failures should leave auditable request context.
    x-vulnerability-class: cross-tenant-access
    x-expected-defense:
      mode: strict
      behavior: deny-cross-tenant-project-read
      successStatus: 403
      requiredSignals: [authorization-decision, audit-event]
    x-evidence-types: [request-response, audit-log, tenant-fixture]
    responses:
      "200":
        description: OK
```

## Seed Endpoint-Control Map

This seed map defines the first high-value OpenAPI operations to annotate. Later
tasks should add the annotations directly to `apps/vuln-api/docs/openapi.yaml`.

| Domain | Method | Path | Vulnerability class | FedRAMP controls | Evidence types |
| --- | --- | --- | --- | --- | --- |
| auth | `POST` | `/api/v1/auth/login` | `auth-bypass` | `IA-2`, `IA-5`, `AC-7`, `AU-2` | `request-response`, `auth-token`, `audit-log` |
| auth | `POST` | `/api/v1/auth/verify-mfa` | `auth-bypass` | `IA-2`, `IA-2(1)`, `IA-5`, `AU-2` | `request-response`, `session-cookie`, `audit-log` |
| users | `GET` | `/api/v1/users/profile` | `idor` | `AC-3`, `AC-6`, `IA-4`, `AU-2` | `request-response`, `auth-token`, `seeded-resource` |
| tenants | `GET` | `/api/v1/saas/tenants/{tenant_id}/projects` | `cross-tenant-access` | `AC-3`, `AC-4`, `AC-6`, `AU-2` | `request-response`, `tenant-fixture`, `audit-log` |
| healthcare | `GET` | `/api/v1/healthcare/records/{record_id}` | `sensitive-data-exposure` | `AC-3`, `AU-2`, `SI-10`, `RA-5` | `request-response`, `seeded-resource`, `audit-log` |
| banking | `GET` | `/api/v1/banking/accounts/{account_id}` | `idor` | `AC-3`, `AC-6`, `AU-2`, `RA-5` | `request-response`, `seeded-resource`, `audit-log` |
| ecommerce | `POST` | `/api/v1/ecommerce/checkout/submit` | `business-logic-abuse` | `AC-3`, `CM-5`, `SI-10`, `AU-2` | `request-response`, `seeded-resource`, `audit-log` |
| payments | `POST` | `/api/v1/payments/capture` | `business-logic-abuse` | `AC-3`, `SC-13`, `SI-10`, `AU-2` | `request-response`, `seeded-resource`, `audit-log` |
| compliance | `GET` | `/api/compliance/status` | `insecure-configuration` | `RA-5`, `CA-7`, `CM-6`, `AU-6` | `request-response`, `config-state`, `openapi-operation` |
| admin/config | `GET` | `/api/v1/admin/security-config` | `insecure-configuration` | `CM-2`, `CM-3`, `CM-6`, `AC-6`, `AU-2` | `request-response`, `config-state`, `audit-log` |
| audit | `POST` | `/api/v1/admin/audit/suspend` | `audit-suppression` | `AU-2`, `AU-6`, `AU-9`, `AC-6`, `CM-5` | `request-response`, `audit-log`, `config-state` |
| integrations | `POST` | `/api/v1/integrations/ws/simulate-frame` | `service-trust-abuse` | `SC-7`, `SC-8`, `AC-4`, `SI-10` | `request-response`, `runner-artifact`, `openapi-operation` |

## Crucible Scenario References

Crucible scenarios should reference Chimera annotations by method, OpenAPI path,
and assertion slug:

```json
{
  "target": {
    "family": "chimera",
    "endpoint": {
      "method": "GET",
      "path": "/api/v1/saas/tenants/{tenant_id}/projects",
      "fedrampAssertion": "tenant-project-access-is-enforced"
    }
  }
}
```

Scenario metadata chooses the specific control assertion being assessed. Chimera
annotations list possible endpoint relevance; they are not themselves assessment
results.

## Drift Rules

Run the annotation validator before updating Crucible scenarios that reference
Chimera FedRAMP operations:

```bash
cd apps/vuln-api
just docs-check-fedramp
uv run python scripts/check_fedramp_openapi_annotations.py --json
```

The text output is intended for local and CI logs. The `--json` output is stable
for Crucible compatibility-matrix automation and includes `annotated_count`,
`annotated_operations`, and `errors`.

FedRAMP annotation validation should fail when:

- a FedRAMP-relevant operation lacks any required extension;
- `controlId` does not match a FedRAMP/NIST-style ID such as `AC-3` or `AU-9(4)`;
- `family` does not match the `controlId` prefix;
- `baselines` contains a value outside `low`, `moderate`, `high`, or `li-saas`;
- `role` is not `primary`, `supporting`, or `manual`;
- `requiredSignals` contains a value outside the documented allowed list;
- a Crucible scenario references an endpoint method/path that is no longer in OpenAPI;
- a Crucible scenario references a `fedrampAssertion` that is not present on that operation;
- a scenario claims a control that is not listed in the operation's `x-fedramp-controls`;
- the annotation uses FedRAMP language to claim authorization readiness instead of endpoint-level evidence relevance.

## References

- FedRAMP Rev. 5 baselines: https://www.fedramp.gov/archive/2023-05-30-rev-5-baselines-have-been-approved-and-released/
- FedRAMP Rev5 machine-readable packages RFC: https://www.fedramp.gov/rfcs/0024/
- FedRAMP machine-readable package outcome notice: https://www.fedramp.gov/notices/0009/
