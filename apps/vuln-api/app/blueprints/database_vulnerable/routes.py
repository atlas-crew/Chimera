"""
Intentionally vulnerable SQL injection endpoints.

SECURITY WARNING: These endpoints demonstrate SQL injection vulnerabilities.
Never use these patterns in production code.

Sync handlers (def, not async def) are deliberate: SQLAlchemy is sync and
SQLite gains nothing from async. The DecoratorRouter awaits results only
when handlers return coroutines, so plain ``def`` handlers run inline on
the event loop. POST handlers stay ``async def`` because they need to
``await safe_json(request)`` to read the request body.
"""

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.database import get_session, is_database_enabled
from app.routing import safe_json

from . import db_vuln_router


def _disabled_response() -> JSONResponse:
    return JSONResponse(
        {"error": "Database mode not enabled. Set USE_DATABASE=true"},
        status_code=503,
    )


def _raw_cursor():
    """Open a session and return ``(session, cursor)`` for raw SQL.

    Callers MUST close the session in a ``finally`` block. The DB-API
    cursor is borrowed from the underlying SQLite connection; closing
    the session releases the connection back to the pool.
    """
    session = get_session()
    cursor = session.connection().connection.cursor()
    return session, cursor


@db_vuln_router.route("/api/v1/patients/search", methods=["GET"])
def search_patients_vulnerable(request: Request):
    """
    VULNERABLE: Patient search by SSN with SQL injection.

    Attack: /api/v1/patients/search?ssn=' OR '1'='1
    """
    if not is_database_enabled():
        return _disabled_response()

    ssn = request.query_params.get("ssn", "")
    query = ""
    session = None
    try:
        session, cursor = _raw_cursor()
        # VULNERABLE: direct string interpolation
        query = f"SELECT * FROM patients WHERE ssn = '{ssn}'"
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        patients = [dict(zip(columns, row)) for row in results]

        return JSONResponse({"success": True, "count": len(patients), "patients": patients})
    except Exception as exc:
        return JSONResponse({"error": str(exc), "query": query}, status_code=500)
    finally:
        if session is not None:
            session.close()


@db_vuln_router.route("/api/v1/auth/login-vulnerable", methods=["POST"])
async def login_vulnerable(request: Request):
    """
    VULNERABLE: Authentication bypass via SQL injection.

    Attack: {"email": "admin@example.com' OR '1'='1' --", "password": "anything"}
    """
    if not is_database_enabled():
        return _disabled_response()

    data = await safe_json(request)
    email = data.get("email", "")
    password = data.get("password", "")

    query = ""
    session = None
    try:
        session, cursor = _raw_cursor()
        # VULNERABLE: SQL injection in authentication
        query = (
            "SELECT id, email, role, full_name FROM users "
            f"WHERE email = '{email}' AND password = '{password}'"
        )
        cursor.execute(query)

        user = cursor.fetchone()
        if user:
            columns = [description[0] for description in cursor.description]
            user_data = dict(zip(columns, user))
            return JSONResponse(
                {
                    "success": True,
                    "message": "Login successful",
                    "user": user_data,
                    "token": "fake-jwt-token-12345",
                }
            )
        return JSONResponse(
            {"success": False, "message": "Invalid credentials"},
            status_code=401,
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc), "query": query}, status_code=500)
    finally:
        if session is not None:
            session.close()


@db_vuln_router.route("/api/v1/banking/accounts/search", methods=["GET"])
def search_accounts_vulnerable(request: Request):
    """
    VULNERABLE: Bank account search with UNION-based SQLi.

    Attack: /api/v1/banking/accounts/search?account_number=ACC-1001'
            UNION SELECT id,email,password,role,1,2,3,4 FROM users --
    """
    if not is_database_enabled():
        return _disabled_response()

    account_number = request.query_params.get("account_number", "")
    query = ""
    session = None
    try:
        session, cursor = _raw_cursor()
        # VULNERABLE: allows UNION attacks
        query = (
            "SELECT id, account_number, account_type, balance, currency, status, "
            f"routing_number, created_at FROM bank_accounts WHERE account_number = '{account_number}'"
        )
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        accounts = [dict(zip(columns, row)) for row in results]

        return JSONResponse({"success": True, "count": len(accounts), "accounts": accounts})
    except Exception as exc:
        return JSONResponse({"error": str(exc), "query": query}, status_code=500)
    finally:
        if session is not None:
            session.close()


@db_vuln_router.route("/api/v1/insurance/policies/lookup", methods=["GET"])
def lookup_policy_vulnerable(request: Request):
    """
    VULNERABLE: Policy lookup with blind boolean-based SQLi.

    Attack: /api/v1/insurance/policies/lookup?policy_number=POL-10001' AND 1=1 --
    """
    if not is_database_enabled():
        return _disabled_response()

    policy_number = request.query_params.get("policy_number", "")
    session = None
    try:
        session, cursor = _raw_cursor()
        # VULNERABLE: blind SQLi - returns different responses based on condition
        query = (
            "SELECT policy_number, policy_type, premium, coverage_amount, status "
            f"FROM insurance_policies WHERE policy_number = '{policy_number}'"
        )
        cursor.execute(query)

        policy = cursor.fetchone()
        if policy:
            columns = [description[0] for description in cursor.description]
            policy_data = dict(zip(columns, policy))
            return JSONResponse({"success": True, "policy": policy_data})
        return JSONResponse(
            {"success": False, "message": "Policy not found"},
            status_code=404,
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        if session is not None:
            session.close()


@db_vuln_router.route("/api/v1/transactions/history", methods=["GET"])
def transaction_history_vulnerable(request: Request):
    """
    VULNERABLE: Transaction history with time-based blind SQLi.
    """
    if not is_database_enabled():
        return _disabled_response()

    account_id = request.query_params.get("account_id", "")
    session = None
    try:
        session, cursor = _raw_cursor()
        # VULNERABLE: integer field interpolation, allows time-based blind SQLi
        query = (
            "SELECT transaction_id, from_account_id, to_account_id, amount, "
            "transaction_type, status, timestamp FROM transactions "
            f"WHERE from_account_id = {account_id}"
        )
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        transactions = [dict(zip(columns, row)) for row in results]

        return JSONResponse(
            {"success": True, "count": len(transactions), "transactions": transactions}
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        if session is not None:
            session.close()


@db_vuln_router.route("/api/v1/claims/search", methods=["GET"])
def search_claims_vulnerable(request: Request):
    """
    VULNERABLE: Claims search with ORDER BY injection.
    """
    if not is_database_enabled():
        return _disabled_response()

    policy_id = request.query_params.get("policy_id", "")
    order_by = request.query_params.get("order_by", "submitted_date")

    query = ""
    session = None
    try:
        session, cursor = _raw_cursor()
        # VULNERABLE: ORDER BY injection
        query = (
            "SELECT claim_number, claim_amount, claim_type, status, fraud_flag, "
            f"submitted_date FROM claims WHERE policy_id = {policy_id} ORDER BY {order_by}"
        )
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        claims = [dict(zip(columns, row)) for row in results]

        return JSONResponse({"success": True, "count": len(claims), "claims": claims})
    except Exception as exc:
        return JSONResponse({"error": str(exc), "query": query}, status_code=500)
    finally:
        if session is not None:
            session.close()


@db_vuln_router.route("/api/v1/users/profile", methods=["GET"])
def get_user_profile_vulnerable(request: Request):
    """
    VULNERABLE: User profile lookup with error-based SQLi.
    """
    if not is_database_enabled():
        return _disabled_response()

    user_id = request.query_params.get("user_id", "")
    query = ""
    session = None
    try:
        session, cursor = _raw_cursor()
        # VULNERABLE: error-based SQLi with detailed error messages
        query = (
            "SELECT id, email, role, full_name, created_at, is_active "
            f"FROM users WHERE id = {user_id}"
        )
        cursor.execute(query)

        user = cursor.fetchone()
        if user:
            columns = [description[0] for description in cursor.description]
            user_data = dict(zip(columns, user))
            return JSONResponse({"success": True, "user": user_data})
        return JSONResponse(
            {"success": False, "message": "User not found"},
            status_code=404,
        )
    except Exception as exc:
        # VULNERABLE: detailed error messages (info leak)
        return JSONResponse(
            {
                "error": str(exc),
                "error_type": type(exc).__name__,
                "query": query,
                "hint": "Check your SQL syntax",
            },
            status_code=500,
        )
    finally:
        if session is not None:
            session.close()


@db_vuln_router.route("/api/v1/healthcare/records", methods=["POST"])
async def search_medical_records_vulnerable(request: Request):
    """
    VULNERABLE: Medical records search with second-order SQLi.

    This endpoint stores user input in database, which could be exploited
    in subsequent queries.
    """
    if not is_database_enabled():
        return _disabled_response()

    data = await safe_json(request)
    search_term = data.get("diagnosis", "")

    query = ""
    session = None
    try:
        session, cursor = _raw_cursor()
        # VULNERABLE: stores unsanitized input that could be used in other queries
        query = (
            "SELECT patient_id, full_name, diagnosis, doctor_name, last_visit "
            f"FROM patients WHERE diagnosis LIKE '%{search_term}%'"
        )
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        records = [dict(zip(columns, row)) for row in results]

        return JSONResponse({"success": True, "count": len(records), "records": records})
    except Exception as exc:
        return JSONResponse({"error": str(exc), "query": query}, status_code=500)
    finally:
        if session is not None:
            session.close()
