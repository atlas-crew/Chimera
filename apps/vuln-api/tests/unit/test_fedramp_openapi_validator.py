from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
import yaml


API_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(API_ROOT / "scripts"))

from check_fedramp_openapi_annotations import (  # noqa: E402
    format_text_report,
    main,
    normalize_openapi_path,
    validate_spec,
)


def valid_operation():
    return {
        "x-fedramp-controls": [
            {
                "framework": "fedramp",
                "revision": "rev5",
                "baselines": ["moderate", "high"],
                "family": "AC",
                "controlId": "AC-3",
                "assertion": "tenant-project-access-is-enforced",
                "role": "primary",
                "rationale": "Cross-tenant project reads should be denied and audited.",
            }
        ],
        "x-vulnerability-class": "cross-tenant-access",
        "x-expected-defense": {
            "mode": "strict",
            "behavior": "deny-cross-tenant-project-read",
            "successStatus": 403,
            "requiredSignals": ["authorization-decision", "audit-event"],
        },
        "x-evidence-types": ["request-response", "tenant-fixture", "audit-log"],
        "responses": {"200": {"description": "OK"}},
    }


def spec_with_operation(
    operation=None, path="/api/v1/saas/tenants/{tenant_id}/projects", method="get"
):
    return {
        "openapi": "3.0.3",
        "paths": {
            path: {
                method: deepcopy(
                    operation if operation is not None else valid_operation()
                ),
            }
        },
    }


def live_operations_for(path="/api/v1/saas/tenants/{tenant_id}/projects", method="GET"):
    return {(normalize_openapi_path(path), method)}


def error_codes(report):
    return {error["code"] for error in report["errors"]}


def test_current_openapi_fedramp_annotations_are_valid():
    spec_path = API_ROOT / "docs" / "openapi.yaml"
    with spec_path.open() as spec_file:
        spec = yaml.safe_load(spec_file)

    report = validate_spec(spec, live_operations=None)

    assert report["annotated_count"] >= 12
    assert report["errors"] == []


def test_validator_accepts_valid_annotated_operation():
    report = validate_spec(spec_with_operation(), live_operations_for())

    assert report["annotated_count"] == 1
    assert report["errors"] == []


def test_validator_skips_unannotated_operations():
    spec = spec_with_operation()
    spec["paths"]["/api/v1/unannotated"] = {
        "get": {"responses": {"200": {"description": "OK"}}},
        "trace": {"x-fedramp-controls": []},
    }

    report = validate_spec(spec, live_operations_for())

    assert report["annotated_count"] == 1
    assert report["errors"] == []


def test_validator_detects_malformed_control_id():
    operation = valid_operation()
    operation["x-fedramp-controls"][0]["controlId"] = "AC3"

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    assert "invalid-control-id" in error_codes(report)


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("framework", "nist", "invalid-framework"),
        ("revision", "rev4", "invalid-revision"),
        ("family", "AU", "family-mismatch"),
        ("assertion", "Not A Valid Slug!", "invalid-assertion"),
        ("rationale", "", "missing-rationale"),
    ],
)
def test_validator_detects_invalid_control_properties(field, value, expected_code):
    operation = valid_operation()
    operation["x-fedramp-controls"][0][field] = value

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    assert expected_code in error_codes(report)


def test_validator_does_not_duplicate_errors_for_missing_control_fields():
    operation = valid_operation()
    del operation["x-fedramp-controls"][0]["baselines"]
    del operation["x-fedramp-controls"][0]["role"]

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    codes = error_codes(report)
    assert "missing-control-field" in codes
    assert "invalid-baselines" not in codes
    assert "invalid-role" not in codes


def test_validator_does_not_report_family_mismatch_for_invalid_family_type():
    operation = valid_operation()
    operation["x-fedramp-controls"][0]["family"] = None

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    codes = error_codes(report)
    assert "invalid-family" in codes
    assert "family-mismatch" not in codes


def test_validator_detects_missing_expected_defense_text():
    operation = valid_operation()
    operation["x-expected-defense"]["behavior"] = ""

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    assert "missing-expected-defense-text" in error_codes(report)


def test_validator_detects_invalid_expected_defense_behavior_slug():
    operation = valid_operation()
    operation["x-expected-defense"]["behavior"] = "Not A Valid Slug!"

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    assert "missing-expected-defense-text" in error_codes(report)


def test_validator_detects_invalid_expected_defense_optional_fields():
    operation = valid_operation()
    operation["x-expected-defense"]["successStatus"] = True
    operation["x-expected-defense"]["notes"] = ["not", "a", "string"]

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    codes = error_codes(report)
    assert "invalid-success-status" in codes
    assert "invalid-defense-notes" in codes


def test_validator_accepts_omitted_expected_defense_optional_fields():
    operation = valid_operation()
    del operation["x-expected-defense"]["successStatus"]
    operation["x-expected-defense"]["requiredSignals"] = []

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    assert report["errors"] == []


def test_validator_detects_missing_evidence_types():
    operation = valid_operation()
    del operation["x-evidence-types"]

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    assert "missing-extension" in error_codes(report)


def test_validator_detects_empty_evidence_types():
    operation = valid_operation()
    operation["x-evidence-types"] = []

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    assert "missing-evidence-types" in error_codes(report)


def test_validator_reports_unhashable_yaml_values_without_crashing():
    operation = valid_operation()
    operation["x-fedramp-controls"][0]["baselines"] = ["moderate", {"bad": "shape"}]
    operation["x-fedramp-controls"][0]["role"] = ["primary"]
    operation["x-vulnerability-class"] = {"bad": "shape"}
    operation["x-expected-defense"]["mode"] = ["strict"]
    operation["x-expected-defense"]["requiredSignals"] = [
        "audit-event",
        {"bad": "shape"},
    ]
    operation["x-evidence-types"] = ["request-response", {"bad": "shape"}]

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    codes = error_codes(report)
    assert "invalid-baselines" in codes
    assert "invalid-role" in codes
    assert "invalid-vulnerability-class" in codes
    assert "invalid-defense-mode" in codes
    assert "invalid-required-signals" in codes
    assert "invalid-evidence-types" in codes


@pytest.mark.parametrize(
    ("mutate_operation", "expected_code"),
    [
        (
            lambda operation: operation["x-fedramp-controls"][0].update(
                {"baselines": ["moderete"]}
            ),
            "invalid-baselines",
        ),
        (
            lambda operation: operation["x-fedramp-controls"][0].update(
                {"role": "almost-primary"}
            ),
            "invalid-role",
        ),
        (
            lambda operation: operation.update(
                {"x-vulnerability-class": "cross-tennant-access"}
            ),
            "invalid-vulnerability-class",
        ),
        (
            lambda operation: operation["x-expected-defense"].update(
                {"mode": "secure"}
            ),
            "invalid-defense-mode",
        ),
        (
            lambda operation: operation["x-expected-defense"].update(
                {"requiredSignals": ["audit-signal"]}
            ),
            "invalid-required-signals",
        ),
        (
            lambda operation: operation.update({"x-evidence-types": ["request-log"]}),
            "invalid-evidence-types",
        ),
    ],
)
def test_validator_detects_invalid_string_enum_values(mutate_operation, expected_code):
    operation = valid_operation()
    mutate_operation(operation)

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    assert expected_code in error_codes(report)


def test_validator_formats_unserializable_invalid_values_without_crashing():
    operation = valid_operation()
    operation["x-fedramp-controls"][0]["baselines"] = [{"bad"}]

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    baseline_error = next(
        error for error in report["errors"] if error["code"] == "invalid-baselines"
    )
    assert "{'bad'}" in baseline_error["message"]


@pytest.mark.parametrize(
    ("mutate_operation", "expected_code"),
    [
        (
            lambda operation: operation.update({"x-fedramp-controls": "not-a-list"}),
            "missing-controls",
        ),
        (
            lambda operation: operation.update(
                {"x-fedramp-controls": ["not-an-object"]}
            ),
            "invalid-control",
        ),
        (
            lambda operation: operation.update({"x-expected-defense": "not-an-object"}),
            "missing-expected-defense",
        ),
        (
            lambda operation: operation["x-fedramp-controls"][0].update(
                {"baselines": "moderate"}
            ),
            "invalid-baselines",
        ),
        (
            lambda operation: operation["x-fedramp-controls"][0].update(
                {"baselines": []}
            ),
            "invalid-baselines",
        ),
    ],
)
def test_validator_detects_invalid_extension_structures(
    mutate_operation, expected_code
):
    operation = valid_operation()
    mutate_operation(operation)

    report = validate_spec(spec_with_operation(operation), live_operations_for())

    assert expected_code in error_codes(report)


def test_validator_detects_annotations_on_removed_paths():
    report = validate_spec(
        spec_with_operation(path="/api/v1/removed/{resource_id}"),
        live_operations_for(),
    )

    assert "stale-openapi-path" in error_codes(report)


def test_live_operation_matching_normalizes_method_case():
    report = validate_spec(spec_with_operation(), live_operations_for(method="get"))

    assert "stale-openapi-path" not in error_codes(report)


def test_empty_spec_is_handled_gracefully():
    report = validate_spec(None, live_operations_for())

    assert report == {"annotated_count": 0, "annotated_operations": [], "errors": []}


def test_validation_errors_are_sorted_deterministically():
    first_operation = valid_operation()
    first_operation["x-evidence-types"] = ["request-log"]
    second_operation = valid_operation()
    second_operation["x-fedramp-controls"][0]["controlId"] = "AC3"
    spec = {
        "openapi": "3.0.3",
        "paths": {
            "/z/path": {"get": second_operation},
            "/a/path": {"post": first_operation},
        },
    }

    report = validate_spec(spec, live_operations=None)

    assert [
        (error["path"], error["method"], error["code"]) for error in report["errors"]
    ] == [
        ("/a/path", "POST", "invalid-evidence-types"),
        ("/z/path", "GET", "invalid-control-id"),
    ]


def test_text_report_is_stable_for_ci_logs():
    report = validate_spec(
        spec_with_operation(path="/api/v1/removed/{resource_id}"), live_operations_for()
    )

    text = format_text_report(report)

    assert text.startswith("FedRAMP OpenAPI annotation validation\n")
    assert "Annotated operations: 1\n" in text
    assert "Errors: 1\n" in text
    assert (
        "ERROR stale-openapi-path GET /api/v1/removed/{resource_id}: "
        "annotated operation is not present in live routes"
    ) in text


def write_spec(tmp_path, spec):
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(yaml.safe_dump(spec), encoding="utf-8")
    return spec_path


def test_cli_returns_zero_for_valid_spec(tmp_path, monkeypatch, capsys):
    spec_path = write_spec(tmp_path, spec_with_operation())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_fedramp_openapi_annotations.py",
            "--spec",
            str(spec_path),
            "--skip-live-routes",
        ],
    )

    assert main() == 0
    captured = capsys.readouterr()
    assert "Annotated operations: 1" in captured.out
    assert "Errors: 0" in captured.out
    assert captured.err == ""


def test_cli_returns_one_for_validation_errors(tmp_path, monkeypatch, capsys):
    operation = valid_operation()
    operation["x-fedramp-controls"][0]["controlId"] = "AC3"
    spec_path = write_spec(tmp_path, spec_with_operation(operation))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_fedramp_openapi_annotations.py",
            "--spec",
            str(spec_path),
            "--skip-live-routes",
        ],
    )

    assert main() == 1
    captured = capsys.readouterr()
    assert "Errors: 1" in captured.out
    assert "invalid-control-id" in captured.out
    assert captured.err == ""


def test_cli_returns_two_for_missing_spec(tmp_path, monkeypatch, capsys):
    missing_spec = tmp_path / "missing-openapi.yaml"
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_fedramp_openapi_annotations.py", "--spec", str(missing_spec)],
    )

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "openapi spec not found" in captured.err


def test_cli_emits_json_report(tmp_path, monkeypatch, capsys):
    spec_path = write_spec(tmp_path, spec_with_operation())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_fedramp_openapi_annotations.py",
            "--spec",
            str(spec_path),
            "--skip-live-routes",
            "--json",
        ],
    )

    assert main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["annotated_count"] == 1
    assert report["errors"] == []


def test_cli_uses_live_route_verification_by_default(tmp_path, monkeypatch, capsys):
    spec_path = write_spec(tmp_path, spec_with_operation())
    monkeypatch.setitem(
        sys.modules,
        "check_openapi_drift",
        SimpleNamespace(
            load_live_routes=lambda: {
                (
                    "/api/v1/saas/tenants/{}/projects",
                    "get",
                ): "/api/v1/saas/tenants/{tenant_id}/projects"
            }
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_fedramp_openapi_annotations.py",
            "--spec",
            str(spec_path),
        ],
    )

    assert main() == 0
    captured = capsys.readouterr()
    assert "Errors: 0" in captured.out
    assert captured.err == ""


def test_cli_returns_two_for_malformed_yaml(tmp_path, monkeypatch, capsys):
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text("invalid: [yaml: content", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_fedramp_openapi_annotations.py",
            "--spec",
            str(spec_path),
            "--skip-live-routes",
        ],
    )

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "failed to validate FedRAMP OpenAPI annotations" in captured.err
