from pathlib import Path
import re

import yaml


SPEC_PATH = Path(__file__).resolve().parents[2] / "docs" / "openapi.yaml"

FEDRAMP_SLICE = {
    ("post", "/api/v1/auth/login"): "auth",
    ("post", "/api/v1/auth/verify-mfa"): "auth",
    ("get", "/api/v1/users/profile"): "users",
    ("get", "/api/v1/saas/tenants/{tenant_id}/projects"): "tenants",
    ("get", "/api/v1/healthcare/records/{record_id}"): "healthcare",
    ("get", "/api/v1/banking/accounts/{account_id}"): "banking",
    ("post", "/api/v1/ecommerce/checkout/submit"): "ecommerce",
    ("post", "/api/v1/payments/capture"): "payments",
    ("get", "/api/compliance/status"): "compliance",
    ("get", "/api/v1/admin/security-config"): "admin/config",
    ("post", "/api/v1/admin/audit/suspend"): "audit",
    ("post", "/api/v1/integrations/ws/simulate-frame"): "integrations",
}

ALLOWED_BASELINES = {"low", "moderate", "high", "li-saas"}
ALLOWED_EVIDENCE_TYPES = {
    "request-response",
    "audit-log",
    "auth-token",
    "session-cookie",
    "tenant-fixture",
    "seeded-resource",
    "config-state",
    "runner-artifact",
    "tls-handshake",
    "openapi-operation",
}
ALLOWED_REQUIRED_SIGNALS = {
    "audit-event",
    "authentication-decision",
    "authorization-decision",
    "boundary-decision",
    "business-rule-decision",
    "config-change-event",
    "input-validation-decision",
    "rate-limit-event",
}
CONTROL_ID_PATTERN = re.compile(r"^[A-Z]{2}-\d+(?:[a-z]|\(\d+\)|\([a-z]\))*$")


def load_openapi_spec():
    with SPEC_PATH.open() as spec_file:
        return yaml.safe_load(spec_file)


def test_initial_fedramp_slice_operations_are_machine_annotated():
    spec = load_openapi_spec()
    annotated_domains = set()

    for operation_key, domain in FEDRAMP_SLICE.items():
        method, path = operation_key
        operation = spec["paths"][path][method]
        annotated_domains.add(domain)

        assert operation["x-fedramp-controls"]
        assert operation["x-vulnerability-class"]
        assert operation["x-expected-defense"]["mode"] in {"strict", "external"}
        assert operation["x-expected-defense"]["behavior"]
        assert (
            set(operation["x-expected-defense"].get("requiredSignals", []))
            <= ALLOWED_REQUIRED_SIGNALS
        )
        assert operation["x-evidence-types"]

        for evidence_type in operation["x-evidence-types"]:
            assert evidence_type in ALLOWED_EVIDENCE_TYPES

    assert annotated_domains == set(FEDRAMP_SLICE.values())


def test_fedramp_control_annotations_follow_consumer_contract():
    spec = load_openapi_spec()

    for method, path in FEDRAMP_SLICE:
        controls = spec["paths"][path][method]["x-fedramp-controls"]

        for control in controls:
            assert control["framework"] == "fedramp"
            assert control["revision"] == "rev5"
            assert control["role"] in {"primary", "supporting", "manual"}
            assert control["baselines"]
            assert set(control["baselines"]) <= ALLOWED_BASELINES
            assert CONTROL_ID_PATTERN.match(control["controlId"])
            assert control["controlId"].startswith(f"{control['family']}-")
            assert re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", control["assertion"])
            assert control["rationale"]


def test_cross_tenant_operation_exposes_crucible_scenario_assertion():
    spec = load_openapi_spec()
    operation = spec["paths"]["/api/v1/saas/tenants/{tenant_id}/projects"]["get"]
    assertions = {control["assertion"] for control in operation["x-fedramp-controls"]}
    control_ids = {control["controlId"] for control in operation["x-fedramp-controls"]}

    assert "tenant-project-access-is-enforced" in assertions
    assert "AC-3" in control_ids
    assert set(operation["x-evidence-types"]) >= {"request-response", "tenant-fixture"}
