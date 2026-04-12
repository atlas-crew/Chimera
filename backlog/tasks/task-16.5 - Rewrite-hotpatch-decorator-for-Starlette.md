---
id: TASK-16.5
title: Rewrite hotpatch decorator for Starlette
status: To Do
assignee: []
created_date: '2026-04-12 04:08'
labels:
  - refactor
dependencies: []
parent_task_id: TASK-16
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The hotpatch decorator (app/utils/hotpatch.py, 94 lines) is the most architecturally sensitive piece of the migration. It dynamically toggles between vulnerable and secure route implementations based on app/utils/security_config.py state, and injects X-Chimera-* educational headers into responses.

## Current Flask-specific APIs in use
- `make_response(result)` — wraps dict/tuple returns into a Response
- `response.get_json()` — reads JSON body
- `response.set_data(new_body)` — replaces body (mutable response)
- `response.headers['X-Chimera-*'] = ...` — header injection
- `request.path` for endpoint heuristic matching
- `request.headers.get('X-Chimera-Education')` for opt-in verbose metadata

## Starlette rewrite strategy
Route handlers now return `JSONResponse` objects directly (immutable). The decorator needs to:
1. Intercept the return value (which will be a JSONResponse)
2. Parse the body via `json.loads(response.body)`
3. Add X-Chimera-* headers by calling `response.headers.update(...)` (Starlette MutableHeaders)
4. For opt-in education metadata: construct a new JSONResponse with the mutated body

The decorator signature must change to accept `request: Request` since Starlette has no thread-local proxy:
```python
@hotpatch('sqli', 'VULN-SQLI-001')
async def my_handler(request: Request, is_secure: bool = False):
    ...
```

The decorator wrapper must also be `async def`.

## Reference implementation sketch
```python
def hotpatch(vuln_type, vuln_id=None):
    def decorator(f):
        @wraps(f)
        async def wrapper(request, *args, **kwargs):
            is_secure = getattr(security_config, f'{vuln_type}_protection', False)
            response = await f(request, *args, is_secure=is_secure, **kwargs)

            # ... meta lookup same as before, using request.url.path ...

            response.headers['X-Chimera-Patched'] = str(is_secure).lower()
            if meta:
                response.headers['X-Chimera-Vuln-ID'] = vid
                # ... rest of headers ...

            if request.headers.get('X-Chimera-Education') == 'true' and meta:
                # Parse body, inject _chimera, construct new JSONResponse
                body = json.loads(response.body)
                if isinstance(body, dict):
                    body['_chimera'] = {...}
                    return JSONResponse(body, status_code=response.status_code, headers=dict(response.headers))

            return response
        return wrapper
    return decorator
```

## Dependencies
- Blocks: TASK-16.3 (Tier 4 has most hotpatch-using routes)
- Independent of: Tier 1-2 migrations (they don't use hotpatch)

## Testing
- Unit tests in tests/unit/test_*.py exercise the X-Chimera-* headers
- Must verify both vulnerable and secure modes produce correct behavior
- Opt-in X-Chimera-Education header must inject _chimera metadata into JSON response
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 hotpatch decorator is async-compatible
- [ ] #2 X-Chimera-Patched, Vuln-ID, Vuln-Type, OWASP, CWE, Severity headers injected correctly
- [ ] #3 X-Chimera-Hint header injected when vulnerable
- [ ] #4 X-Chimera-Education: true opt-in injects _chimera metadata into JSON body
- [ ] #5 Existing vulnerability tests that assert on X-Chimera-* headers still pass
- [ ] #6 Decorator works with VULN_REGISTRY heuristic fallback lookup
<!-- AC:END -->
