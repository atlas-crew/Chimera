#!/usr/bin/env python3
"""Validate FedRAMP OpenAPI annotations in docs/openapi.yaml.

Exit codes:
  0 - annotations are valid
  1 - validation errors detected
  2 - failed to load routes or spec
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_DIR = Path(__file__).resolve().parent.parent

DOCUMENTED_METHODS = {"get", "post", "put", "patch", "delete"}
FEDRAMP_EXTENSIONS = (
    "x-fedramp-controls",
    "x-vulnerability-class",
    "x-expected-defense",
    "x-evidence-types",
)
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
ALLOWED_ROLES = {"primary", "supporting", "manual"}
ALLOWED_DEFENSE_MODES = {"strict", "external"}
ALLOWED_VULNERABILITY_CLASSES = {
    "auth-bypass",
    "idor",
    "cross-tenant-access",
    "privilege-escalation",
    "audit-suppression",
    "insecure-configuration",
    "business-logic-abuse",
    "input-validation",
    "ssrf",
    "service-trust-abuse",
    "cryptographic-weakness",
    "sensitive-data-exposure",
}
CONTROL_ID_PATTERN = re.compile(r"^[A-Z]{2}-\d+(?:[a-z]|\(\d+\)|\([a-z]\))*$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OAS_PARAM_PATTERN = re.compile(r"\{[^}]+\}")


def normalize_openapi_path(path: str) -> str:
    return OAS_PARAM_PATTERN.sub("{}", path)


def has_fedramp_annotation(operation: Any) -> bool:
    return isinstance(operation, dict) and any(
        extension in operation for extension in FEDRAMP_EXTENSIONS
    )


def operation_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def describe_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return repr(value)


def invalid_string_values(values: list[Any], allowed_values: set[str]) -> list[str]:
    return sorted(
        describe_value(value)
        for value in values
        if not isinstance(value, str) or value not in allowed_values
    )


def normalize_live_operation_keys(
    live_operations: set[tuple[str, str]]
) -> set[tuple[str, str]]:
    return {
        (normalize_openapi_path(live_path), live_method.upper())
        for live_path, live_method in live_operations
    }


def add_error(
    errors: list[dict[str, str]], code: str, method: str, path: str, message: str
) -> None:
    errors.append(
        {
            "code": code,
            "method": method.upper(),
            "path": path,
            "message": message,
        }
    )


def validate_control(
    control: Any,
    *,
    index: int,
    method: str,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    prefix = f"x-fedramp-controls[{index}]"
    if not isinstance(control, dict):
        add_error(
            errors, "invalid-control", method, path, f"{prefix} must be an object"
        )
        return

    for field in (
        "framework",
        "revision",
        "baselines",
        "family",
        "controlId",
        "assertion",
        "role",
        "rationale",
    ):
        if field not in control:
            add_error(
                errors,
                "missing-control-field",
                method,
                path,
                f"{prefix}.{field} is required",
            )

    if "framework" in control and control.get("framework") != "fedramp":
        add_error(
            errors,
            "invalid-framework",
            method,
            path,
            f"{prefix}.framework must be fedramp",
        )
    if "revision" in control and control.get("revision") != "rev5":
        add_error(
            errors, "invalid-revision", method, path, f"{prefix}.revision must be rev5"
        )

    baselines = control.get("baselines")
    if "baselines" not in control:
        pass
    elif not isinstance(baselines, list) or not baselines:
        add_error(
            errors,
            "invalid-baselines",
            method,
            path,
            f"{prefix}.baselines must be a non-empty array",
        )
    elif invalid_baselines := invalid_string_values(baselines, ALLOWED_BASELINES):
        add_error(
            errors,
            "invalid-baselines",
            method,
            path,
            f"{prefix}.baselines contains unsupported values: {', '.join(invalid_baselines)}",
        )

    control_id = control.get("controlId")
    family = control.get("family")
    if "controlId" not in control:
        pass
    elif not isinstance(control_id, str) or not CONTROL_ID_PATTERN.match(control_id):
        add_error(
            errors,
            "invalid-control-id",
            method,
            path,
            f"{prefix}.controlId is malformed",
        )
    if "family" not in control:
        pass
    elif not isinstance(family, str) or not family:
        add_error(
            errors,
            "invalid-family",
            method,
            path,
            f"{prefix}.family must be a non-empty string",
        )
    elif (
        "controlId" in control
        and "family" in control
        and isinstance(control_id, str)
        and isinstance(family, str)
        and CONTROL_ID_PATTERN.match(control_id)
        and not control_id.startswith(f"{family}-")
    ):
        add_error(
            errors,
            "family-mismatch",
            method,
            path,
            f"{prefix}.family does not match controlId",
        )

    assertion = control.get("assertion")
    if "assertion" in control and (
        not isinstance(assertion, str) or not SLUG_PATTERN.match(assertion)
    ):
        add_error(
            errors,
            "invalid-assertion",
            method,
            path,
            f"{prefix}.assertion must be a lower-kebab slug",
        )

    role = control.get("role")
    if "role" in control and (not isinstance(role, str) or role not in ALLOWED_ROLES):
        add_error(
            errors,
            "invalid-role",
            method,
            path,
            f"{prefix}.role must be primary, supporting, or manual",
        )

    rationale = control.get("rationale")
    if "rationale" in control and (
        not isinstance(rationale, str) or not rationale.strip()
    ):
        add_error(
            errors,
            "missing-rationale",
            method,
            path,
            f"{prefix}.rationale must be non-empty",
        )


def validate_expected_defense(
    expected_defense: Any,
    *,
    method: str,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    if not isinstance(expected_defense, dict):
        add_error(
            errors,
            "missing-expected-defense",
            method,
            path,
            "x-expected-defense must be an object",
        )
        return

    mode = expected_defense.get("mode")
    if not isinstance(mode, str) or mode not in ALLOWED_DEFENSE_MODES:
        add_error(
            errors,
            "invalid-defense-mode",
            method,
            path,
            "x-expected-defense.mode is unsupported",
        )

    behavior = expected_defense.get("behavior")
    if not isinstance(behavior, str) or not SLUG_PATTERN.match(behavior):
        add_error(
            errors,
            "missing-expected-defense-text",
            method,
            path,
            "x-expected-defense.behavior must be a non-empty lower-kebab slug",
        )

    if "requiredSignals" in expected_defense:
        signals = expected_defense["requiredSignals"]
        if not isinstance(signals, list):
            add_error(
                errors,
                "invalid-required-signals",
                method,
                path,
                "requiredSignals must be an array",
            )
        elif invalid_signals := invalid_string_values(
            signals, ALLOWED_REQUIRED_SIGNALS
        ):
            add_error(
                errors,
                "invalid-required-signals",
                method,
                path,
                f"requiredSignals contains unsupported values: {', '.join(invalid_signals)}",
            )

    success_status = expected_defense.get("successStatus")
    if "successStatus" in expected_defense and (
        isinstance(success_status, bool) or not isinstance(success_status, (int, str))
    ):
        add_error(
            errors,
            "invalid-success-status",
            method,
            path,
            "x-expected-defense.successStatus must be an integer or string",
        )

    if "notes" in expected_defense and not isinstance(expected_defense["notes"], str):
        add_error(
            errors,
            "invalid-defense-notes",
            method,
            path,
            "x-expected-defense.notes must be a string",
        )


def validate_operation(
    method: str,
    path: str,
    operation: dict[str, Any],
    live_operations: set[tuple[str, str]] | None,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    normalized_key = (normalize_openapi_path(path), method.upper())
    if live_operations is not None and normalized_key not in live_operations:
        add_error(
            errors,
            "stale-openapi-path",
            method,
            path,
            "annotated operation is not present in live routes",
        )

    for extension in FEDRAMP_EXTENSIONS:
        if extension not in operation:
            add_error(
                errors, "missing-extension", method, path, f"{extension} is required"
            )

    controls = operation.get("x-fedramp-controls")
    if "x-fedramp-controls" not in operation:
        pass
    elif not isinstance(controls, list) or not controls:
        add_error(
            errors,
            "missing-controls",
            method,
            path,
            "x-fedramp-controls must be a non-empty array",
        )
    else:
        for index, control in enumerate(controls):
            validate_control(
                control, index=index, method=method, path=path, errors=errors
            )

    vulnerability_class = operation.get("x-vulnerability-class")
    if "x-vulnerability-class" in operation and (
        not isinstance(vulnerability_class, str)
        or vulnerability_class not in ALLOWED_VULNERABILITY_CLASSES
    ):
        add_error(
            errors,
            "invalid-vulnerability-class",
            method,
            path,
            "x-vulnerability-class is unsupported",
        )

    if "x-expected-defense" in operation:
        validate_expected_defense(
            operation.get("x-expected-defense"),
            method=method,
            path=path,
            errors=errors,
        )

    evidence_types = operation.get("x-evidence-types")
    if "x-evidence-types" not in operation:
        pass
    elif not isinstance(evidence_types, list) or not evidence_types:
        add_error(
            errors,
            "missing-evidence-types",
            method,
            path,
            "x-evidence-types must be a non-empty array",
        )
    elif invalid_evidence := invalid_string_values(
        evidence_types, ALLOWED_EVIDENCE_TYPES
    ):
        add_error(
            errors,
            "invalid-evidence-types",
            method,
            path,
            f"x-evidence-types contains unsupported values: {', '.join(invalid_evidence)}",
        )

    return errors


def validate_spec(
    spec: Any,
    live_operations: set[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    if isinstance(spec, dict):
        paths = spec.get("paths") or {}
    else:
        paths = {}
    errors: list[dict[str, str]] = []
    annotated_operations: list[dict[str, str]] = []
    live_operation_keys = (
        normalize_live_operation_keys(live_operations)
        if live_operations is not None
        else None
    )

    for path, methods in paths.items():
        if not isinstance(path, str) or not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method not in DOCUMENTED_METHODS or not has_fedramp_annotation(
                operation
            ):
                continue
            annotated_operations.append({"method": method.upper(), "path": path})
            errors.extend(
                validate_operation(method, path, operation, live_operation_keys)
            )

    errors.sort(
        key=lambda error: (
            error["path"],
            error["method"],
            error["code"],
            error["message"],
        )
    )
    annotated_operations.sort(key=lambda item: (item["path"], item["method"]))
    return {
        "annotated_count": len(annotated_operations),
        "annotated_operations": annotated_operations,
        "errors": errors,
    }


def load_live_operation_keys() -> set[tuple[str, str]]:
    from check_openapi_drift import load_live_routes

    return set(load_live_routes())


def format_text_report(report: dict[str, Any]) -> str:
    lines = [
        "FedRAMP OpenAPI annotation validation",
        f"Annotated operations: {report['annotated_count']}",
        f"Errors: {len(report['errors'])}",
    ]
    for error in report["errors"]:
        lines.append(
            f"ERROR {error['code']} {operation_key(error['method'], error['path'])}: {error['message']}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON"
    )
    parser.add_argument("--spec", default=str(REPO_DIR / "docs" / "openapi.yaml"))
    parser.add_argument(
        "--skip-live-routes",
        action="store_true",
        help="Skip live-route stale path validation",
    )
    args = parser.parse_args()

    spec_file = Path(args.spec)
    if not spec_file.is_file():
        print(f"openapi spec not found: {spec_file}", file=sys.stderr)
        return 2

    try:
        with spec_file.open() as file:
            spec = yaml.safe_load(file)
        live_operations = None if args.skip_live_routes else load_live_operation_keys()
        report = validate_spec(spec, live_operations)
    except Exception as exc:
        print(f"failed to validate FedRAMP OpenAPI annotations: {exc}", file=sys.stderr)
        return 2

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(format_text_report(report))

    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
