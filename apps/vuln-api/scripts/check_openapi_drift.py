#!/usr/bin/env python3
"""Detect drift between live routes and docs/openapi.yaml.

Walks the Flask app's url_map (which serves as the union of live routes during
the Flask->Starlette migration, since register_flask_compat_routes mirrors
ported Starlette routers back into Flask) and diffs it against the declared
paths in docs/openapi.yaml.

Exit codes:
  0 - no drift
  1 - drift detected
  2 - failed to load app or spec
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent

# Non-API plumbing that does not need to appear in the OpenAPI spec.
IGNORED_PATHS = {
    '/',
    '/healthz',
    '/openapi.yaml',
    '/swagger',
    '/static/<path:filename>',
    '/<path:path>',
    '/apidocs',
    '/apidocs/',
    '/apidocs/index.html',
    '/apidocs/<path:path>',
    '/apidocs/oauth2-redirect.html',
    '/apispec.json',
    '/apispec_1.json',
    '/flasgger_static/<path:filename>',
    '/oauth2-redirect.html',  # flasgger auto-registers this; not a real API
}

# Prefix filter for whole route families that belong to test scaffolding and
# should never appear in the public OpenAPI spec.
IGNORED_PATH_PREFIXES = (
    '/api/test/',  # testing blueprint -- intentional error-triggering scaffolding
)

IGNORED_METHODS = {'HEAD', 'OPTIONS'}
DOCUMENTED_METHODS = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}

_FLASK_PARAM = re.compile(r'<(?:[^:>]+:)?[^>]+>')
_OAS_PARAM = re.compile(r'\{[^}]+\}')


def _normalize_flask(path: str) -> str:
    return _FLASK_PARAM.sub('{}', path)


def _normalize_oas(path: str) -> str:
    return _OAS_PARAM.sub('{}', path)


def load_live_routes() -> dict[tuple[str, str], str]:
    import contextlib

    sys.path.insert(0, str(REPO_DIR))

    # Walk the Starlette app's route table. The drift checker only enumerates
    # route declarations, so we don't need a working SQLite engine — and we
    # manually pull in db_vuln_router below to cover the routes that are
    # normally gated behind USE_DATABASE=true.
    os.environ['USE_DATABASE'] = 'false'

    from starlette.routing import Route

    from app.asgi import create_app
    from app.blueprints.database_vulnerable import db_vuln_router

    # create_app() prints boot messages to stdout; redirect them to stderr
    # so --json output stays machine-readable.
    with contextlib.redirect_stdout(sys.stderr):
        app = create_app()
        live_routes = list(app.routes)
        # database_vulnerable is opt-in via USE_DATABASE; pull its routes in
        # so they appear in the drift inventory regardless of the env flag.
        # Dedup by (path, frozenset(methods)) — healthcare and database_vulnerable
        # both register /api/v1/healthcare/records but with different methods.
        existing = {
            (r.path, frozenset(r.methods or set()))
            for r in live_routes if isinstance(r, Route)
        }
        for route in db_vuln_router.routes:
            if not isinstance(route, Route):
                continue
            key = (route.path, frozenset(route.methods or set()))
            if key not in existing:
                live_routes.append(route)

    routes: dict[tuple[str, str], str] = {}
    for route in live_routes:
        if not isinstance(route, Route):
            continue
        # Starlette stores paths in {name} / {name:converter} form; convert
        # to the Flask <converter:name> shape used by the spec normalization.
        starlette_path = route.path
        flask_path = re.sub(
            r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<conv>[a-zA-Z_][a-zA-Z0-9_]*))?\}",
            lambda m: (
                f"<{m.group('conv')}:{m.group('name')}>" if m.group("conv")
                else f"<{m.group('name')}>"
            ),
            starlette_path,
        )
        if flask_path in IGNORED_PATHS:
            continue
        if any(flask_path.startswith(prefix) for prefix in IGNORED_PATH_PREFIXES):
            continue
        normalized = _normalize_flask(flask_path)
        methods = set(route.methods or set()) - IGNORED_METHODS
        for method in methods:
            routes[(normalized, method)] = flask_path
    return routes


def load_spec_paths(spec_file: Path) -> dict[tuple[str, str], str]:
    import yaml

    with spec_file.open() as f:
        spec = yaml.safe_load(f)
    paths = spec.get('paths') or {}
    results: dict[tuple[str, str], str] = {}
    for declared_path, operations in paths.items():
        if not isinstance(operations, dict):
            continue
        if not isinstance(declared_path, str) or not declared_path.startswith('/'):
            # OpenAPI requires paths to start with '/'. Skip any malformed
            # keys left behind by past manual edits so they don't inflate the
            # drift set; the prune tool will physically remove them.
            continue
        normalized = _normalize_oas(declared_path)
        for method_key in operations:
            method = method_key.upper()
            if method not in DOCUMENTED_METHODS:
                continue
            results[(normalized, method)] = declared_path
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Emit machine-readable JSON')
    parser.add_argument('--spec', default=str(REPO_DIR / 'docs' / 'openapi.yaml'))
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Max entries to show per section in text mode (0 = unlimited)',
    )
    args = parser.parse_args()

    spec_file = Path(args.spec)
    if not spec_file.is_file():
        print(f'openapi spec not found: {spec_file}', file=sys.stderr)
        return 2

    try:
        live = load_live_routes()
        spec = load_spec_paths(spec_file)
    except Exception as exc:
        print(f'failed to load routes or spec: {exc}', file=sys.stderr)
        return 2

    live_keys = set(live)
    spec_keys = set(spec)
    missing_from_spec = sorted(live_keys - spec_keys)
    missing_from_code = sorted(spec_keys - live_keys)

    report = {
        'live_count': len(live_keys),
        'spec_count': len(spec_keys),
        'missing_from_spec': [
            {'path': live[k], 'method': k[1]} for k in missing_from_spec
        ],
        'missing_from_code': [
            {'path': spec[k], 'method': k[1]} for k in missing_from_code
        ],
    }

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write('\n')
    else:
        def _dump(title: str, items: list[dict[str, str]]) -> None:
            print(f'{title} ({len(items)}):')
            shown = items if args.limit == 0 else items[: args.limit]
            for item in shown:
                print(f'  {item["method"]:<6} {item["path"]}')
            if args.limit and len(items) > args.limit:
                print(f'  ... {len(items) - args.limit} more (use --limit 0 to see all, or --json)')
            print()

        print(f'Live routes: {report["live_count"]}   OpenAPI operations: {report["spec_count"]}')
        print()
        _dump('Missing from OpenAPI spec', report['missing_from_spec'])
        _dump('Declared in OpenAPI but not in code', report['missing_from_code'])

    return 1 if (missing_from_spec or missing_from_code) else 0


if __name__ == '__main__':
    sys.exit(main())
