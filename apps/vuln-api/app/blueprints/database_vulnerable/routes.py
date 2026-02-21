"""
Intentionally vulnerable SQL injection endpoints.

SECURITY WARNING: These endpoints demonstrate SQL injection vulnerabilities.
Never use these patterns in production code.
"""

import os
from flask import request, jsonify
from . import db_vuln_bp


def is_database_enabled():
    """Check if database mode is enabled."""
    return os.getenv('USE_DATABASE', 'false').lower() == 'true'


def get_db_connection():
    """Get raw database connection for vulnerable queries."""
    if not is_database_enabled():
        return None

    from app.models import db
    return db.session.connection().connection


@db_vuln_bp.route('/api/v1/patients/search', methods=['GET'])
def search_patients_vulnerable():
    """
    VULNERABLE: Patient search by SSN with SQL injection.

    Attack: /api/v1/patients/search?ssn=' OR '1'='1
    """
    if not is_database_enabled():
        return jsonify({"error": "Database mode not enabled. Set USE_DATABASE=true"}), 503

    ssn = request.args.get('ssn', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE: Direct string interpolation
        query = f"SELECT * FROM patients WHERE ssn = '{ssn}'"
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        patients = [dict(zip(columns, row)) for row in results]

        return jsonify({
            "success": True,
            "count": len(patients),
            "patients": patients
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "query": query  # VULNERABLE: Leaks query in error
        }), 500


@db_vuln_bp.route('/api/v1/auth/login-vulnerable', methods=['POST'])
def login_vulnerable():
    """
    VULNERABLE: Authentication bypass via SQL injection.

    Attack: {"email": "admin@example.com' OR '1'='1' --", "password": "anything"}
    """
    if not is_database_enabled():
        return jsonify({"error": "Database mode not enabled"}), 503

    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE: SQL injection in authentication
        query = f"SELECT id, email, role, full_name FROM users WHERE email = '{email}' AND password = '{password}'"
        cursor.execute(query)

        user = cursor.fetchone()

        if user:
            columns = [description[0] for description in cursor.description]
            user_data = dict(zip(columns, user))

            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": user_data,
                "token": "fake-jwt-token-12345"  # Simulated token
            })
        else:
            return jsonify({
                "success": False,
                "message": "Invalid credentials"
            }), 401

    except Exception as e:
        return jsonify({
            "error": str(e),
            "query": query
        }), 500


@db_vuln_bp.route('/api/v1/banking/accounts/search', methods=['GET'])
def search_accounts_vulnerable():
    """
    VULNERABLE: Bank account search with UNION-based SQLi.

    Attack: /api/v1/banking/accounts/search?account_number=ACC-1001' UNION SELECT id,email,password,role,1,2,3,4 FROM users --
    """
    if not is_database_enabled():
        return jsonify({"error": "Database mode not enabled"}), 503

    account_number = request.args.get('account_number', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE: Allows UNION attacks
        query = f"SELECT id, account_number, account_type, balance, currency, status, routing_number, created_at FROM bank_accounts WHERE account_number = '{account_number}'"
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        accounts = [dict(zip(columns, row)) for row in results]

        return jsonify({
            "success": True,
            "count": len(accounts),
            "accounts": accounts
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "query": query
        }), 500


@db_vuln_bp.route('/api/v1/insurance/policies/lookup', methods=['GET'])
def lookup_policy_vulnerable():
    """
    VULNERABLE: Policy lookup with blind boolean-based SQLi.

    Attack: /api/v1/insurance/policies/lookup?policy_number=POL-10001' AND 1=1 --
    """
    if not is_database_enabled():
        return jsonify({"error": "Database mode not enabled"}), 503

    policy_number = request.args.get('policy_number', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE: Blind SQLi - returns different responses based on condition
        query = f"SELECT policy_number, policy_type, premium, coverage_amount, status FROM insurance_policies WHERE policy_number = '{policy_number}'"
        cursor.execute(query)

        policy = cursor.fetchone()

        if policy:
            columns = [description[0] for description in cursor.description]
            policy_data = dict(zip(columns, policy))

            return jsonify({
                "success": True,
                "policy": policy_data
            })
        else:
            return jsonify({
                "success": False,
                "message": "Policy not found"
            }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@db_vuln_bp.route('/api/v1/transactions/history', methods=['GET'])
def transaction_history_vulnerable():
    """
    VULNERABLE: Transaction history with time-based blind SQLi.

    Attack: /api/v1/transactions/history?account_id=1' AND (SELECT CASE WHEN (1=1) THEN 1 ELSE (SELECT 1 UNION SELECT 2) END) --
    """
    if not is_database_enabled():
        return jsonify({"error": "Database mode not enabled"}), 503

    account_id = request.args.get('account_id', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE: Time-based blind SQLi possible
        query = f"SELECT transaction_id, from_account_id, to_account_id, amount, transaction_type, status, timestamp FROM transactions WHERE from_account_id = {account_id}"
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        transactions = [dict(zip(columns, row)) for row in results]

        return jsonify({
            "success": True,
            "count": len(transactions),
            "transactions": transactions
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@db_vuln_bp.route('/api/v1/claims/search', methods=['GET'])
def search_claims_vulnerable():
    """
    VULNERABLE: Claims search with ORDER BY injection.

    Attack: /api/v1/claims/search?policy_id=1&order_by=(SELECT CASE WHEN (1=1) THEN claim_amount ELSE id END)
    """
    if not is_database_enabled():
        return jsonify({"error": "Database mode not enabled"}), 503

    policy_id = request.args.get('policy_id', '')
    order_by = request.args.get('order_by', 'submitted_date')  # Default ordering

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE: ORDER BY injection
        query = f"SELECT claim_number, claim_amount, claim_type, status, fraud_flag, submitted_date FROM claims WHERE policy_id = {policy_id} ORDER BY {order_by}"
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        claims = [dict(zip(columns, row)) for row in results]

        return jsonify({
            "success": True,
            "count": len(claims),
            "claims": claims
        })

    except Exception as e:
        return jsonify({"error": str(e), "query": query}), 500


@db_vuln_bp.route('/api/v1/users/profile', methods=['GET'])
def get_user_profile_vulnerable():
    """
    VULNERABLE: User profile lookup with error-based SQLi.

    Attack: /api/v1/users/profile?user_id=1' AND extractvalue(1,concat(0x7e,(SELECT password FROM users LIMIT 1))) --
    """
    if not is_database_enabled():
        return jsonify({"error": "Database mode not enabled"}), 503

    user_id = request.args.get('user_id', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE: Error-based SQLi with detailed error messages
        query = f"SELECT id, email, role, full_name, created_at, is_active FROM users WHERE id = {user_id}"
        cursor.execute(query)

        user = cursor.fetchone()

        if user:
            columns = [description[0] for description in cursor.description]
            user_data = dict(zip(columns, user))

            return jsonify({
                "success": True,
                "user": user_data
            })
        else:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

    except Exception as e:
        # VULNERABLE: Detailed error messages
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "query": query,
            "hint": "Check your SQL syntax"
        }), 500


@db_vuln_bp.route('/api/v1/healthcare/records', methods=['POST'])
def search_medical_records_vulnerable():
    """
    VULNERABLE: Medical records search with second-order SQLi.

    This endpoint stores user input in database, which could be exploited
    in subsequent queries.
    """
    if not is_database_enabled():
        return jsonify({"error": "Database mode not enabled"}), 503

    data = request.get_json() or {}
    search_term = data.get('diagnosis', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE: Stores unsanitized input that could be used in other queries
        query = f"SELECT patient_id, full_name, diagnosis, doctor_name, last_visit FROM patients WHERE diagnosis LIKE '%{search_term}%'"
        cursor.execute(query)

        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        records = [dict(zip(columns, row)) for row in results]

        return jsonify({
            "success": True,
            "count": len(records),
            "records": records
        })

    except Exception as e:
        return jsonify({"error": str(e), "query": query}), 500
