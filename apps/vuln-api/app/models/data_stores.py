"""
Shared in-memory data stores for demo purposes.
In production, these would be replaced with proper database models.
"""

from gevent.lock import BoundedSemaphore as Lock

# User and authentication stores
users_db = {}
username_to_id_map = {}
email_to_id_map = {}
users_db_lock = Lock()
password_reset_requests = {}
password_reset_requests_lock = Lock()
refresh_tokens_db = {}
refresh_tokens_db_lock = Lock()
mfa_challenges_db = {}
mfa_challenges_db_lock = Lock()
registered_devices_db = {}
registered_devices_db_lock = Lock()
api_keys_db = {}
api_keys_db_lock = Lock()


def _index_user_unlocked(user_id, user):
    username = user.get('username')
    if username:
        username_to_id_map[username] = user_id
    email = user.get('email')
    if email:
        email_to_id_map[email] = user_id


def clear_user_indexes():
    with users_db_lock:
        username_to_id_map.clear()
        email_to_id_map.clear()


def rebuild_user_indexes():
    with users_db_lock:
        username_to_id_map.clear()
        email_to_id_map.clear()
        for user_id, user in users_db.items():
            _index_user_unlocked(user_id, user)


def add_user(user_id, user):
    with users_db_lock:
        existing = users_db.get(user_id)
        if existing:
            old_username = existing.get('username')
            old_email = existing.get('email')
            if old_username:
                username_to_id_map.pop(old_username, None)
            if old_email:
                email_to_id_map.pop(old_email, None)
        users_db[user_id] = user
        _index_user_unlocked(user_id, user)


def update_user(user_id, updates):
    if not user_id:
        return False
    with users_db_lock:
        user = users_db.get(user_id)
        if not user:
            return False
        old_username = user.get('username')
        old_email = user.get('email')
        user.update(updates)
        new_username = user.get('username')
        new_email = user.get('email')
        if old_username != new_username:
            if old_username:
                username_to_id_map.pop(old_username, None)
            if new_username:
                username_to_id_map[new_username] = user_id
        if old_email != new_email:
            if old_email:
                email_to_id_map.pop(old_email, None)
            if new_email:
                email_to_id_map[new_email] = user_id
        return True


def get_user_by_id(user_id):
    if not user_id:
        return None
    with users_db_lock:
        return users_db.get(user_id)


def get_user_by_username(username):
    if not username:
        return None
    with users_db_lock:
        user_id = username_to_id_map.get(username)
        return users_db.get(user_id) if user_id else None


def get_user_by_email(email):
    if not email:
        return None
    with users_db_lock:
        user_id = email_to_id_map.get(email)
        return users_db.get(user_id) if user_id else None


def get_user_by_identifier(identifier):
    if not identifier:
        return None
    with users_db_lock:
        user_id = username_to_id_map.get(identifier) or email_to_id_map.get(identifier)
        if not user_id and identifier in users_db:
            user_id = identifier
        return users_db.get(user_id) if user_id else None


def user_exists_by_username(username):
    if not username:
        return False
    with users_db_lock:
        return username in username_to_id_map


def user_exists_by_email(email):
    if not email:
        return False
    with users_db_lock:
        return email in email_to_id_map

# Banking stores
accounts_db = {}
transactions_db = {}

# Payment stores
payment_methods_db = {}
card_profiles_db = {}
merchant_applications_db = {}
bin_range_catalog = []
payment_test_events = []
customer_payment_methods_db = {}
fraudulent_methods_db = []
currency_rates_db = {}

# E-commerce stores
products_db = {}
cart_sessions = {}
orders_db = {}
reviews_db = []
ratings_db = []
shipping_addresses_db = {}
shipping_zones_db = {}
promotions_db = {}
discounts_db = {}
tax_calculations_db = []

# Vendor stores
vendor_registry_db = {}
vendor_documents_db = {}
vendor_inventory_events = []

# Loyalty stores
loyalty_accounts_db = {}
loyalty_redemptions_db = {}

# Mobile stores
mobile_devices_db = {}

# Healthcare stores
medical_records_db = {}
providers_db = {}
telehealth_sessions_db = {}
prior_auth_db = {}
eligibility_checks_db = {}

# Insurance stores
claims_db = {}
customers_db = {}
policies_db = {}
claims_evidence_db = {}
underwriting_rules_db = []
actuarial_models_db = {}
insurance_brokers_db = {}
insurance_commissions_db = {}
insurance_broker_clients_db = {}

# Compliance stores
compliance_logs_db = {}
audit_suppressions_db = []

# Infrastructure stores
cloud_service_registry = {}
apt_operations_log = []

# Export/transaction stores
transaction_exports_db = []

# SaaS stores
saas_tenants_db = {}
saas_projects_db = {}
saas_users_db = {}
saas_users_db_lock = Lock()
saas_users_by_tenant = {}
saas_shared_links_db = []
saas_billing_invoices_db = {}
saas_billing_usage_db = {}
saas_workspace_settings_db = {}
saas_coupons_db = {}
saas_refresh_tokens_db = {}
saas_audit_logs_db = []
saas_api_keys_db = {}
saas_webhooks_db = {}
saas_scim_groups_db = {}
saas_scim_users_db = {}
saas_org_invites_db = {}
saas_saml_configs_db = {}
saas_session_revocations_db = {}


def _rebuild_saas_user_index_unlocked():
    saas_users_by_tenant.clear()
    for user_id, user in saas_users_db.items():
        tenant_id = user.get('tenant_id')
        if tenant_id:
            saas_users_by_tenant.setdefault(tenant_id, []).append(user_id)


def rebuild_saas_user_index():
    with saas_users_db_lock:
        _rebuild_saas_user_index_unlocked()


def add_saas_user(user_id, user):
    with saas_users_db_lock:
        existing = saas_users_db.get(user_id)
        if existing:
            old_tenant = existing.get('tenant_id')
            if old_tenant:
                tenant_users = saas_users_by_tenant.get(old_tenant, [])
                if user_id in tenant_users:
                    tenant_users.remove(user_id)
                if not tenant_users and old_tenant in saas_users_by_tenant:
                    saas_users_by_tenant.pop(old_tenant, None)
        saas_users_db[user_id] = user
        tenant_id = user.get('tenant_id')
        if tenant_id:
            tenant_users = saas_users_by_tenant.setdefault(tenant_id, [])
            if user_id not in tenant_users:
                tenant_users.append(user_id)


def update_saas_user(user_id, updates):
    if not user_id:
        return None
    with saas_users_db_lock:
        user = saas_users_db.get(user_id)
        if not user:
            user = {'user_id': user_id}
            saas_users_db[user_id] = user
        old_tenant = user.get('tenant_id')
        user.update(updates)
        new_tenant = user.get('tenant_id')
        if old_tenant != new_tenant:
            if old_tenant:
                tenant_users = saas_users_by_tenant.get(old_tenant, [])
                if user_id in tenant_users:
                    tenant_users.remove(user_id)
                if not tenant_users and old_tenant in saas_users_by_tenant:
                    saas_users_by_tenant.pop(old_tenant, None)
            if new_tenant:
                tenant_users = saas_users_by_tenant.setdefault(new_tenant, [])
                if user_id not in tenant_users:
                    tenant_users.append(user_id)
        return user


def get_saas_users_for_tenant(tenant_id):
    if not tenant_id:
        return []
    with saas_users_db_lock:
        if tenant_id not in saas_users_by_tenant and saas_users_db:
            _rebuild_saas_user_index_unlocked()
        user_ids = saas_users_by_tenant.get(tenant_id, [])
        return [dict(saas_users_db[user_id]) for user_id in user_ids if user_id in saas_users_db]

# Government stores
gov_cases_db = {}
gov_records_db = {}
gov_users_db = {}
gov_access_cards_db = {}
gov_service_requests_db = {}
gov_audit_logs_db = {}
gov_credentials_db = {}
gov_benefits_applications_db = {}
gov_classifications_db = {}
gov_permits_db = {}
gov_licenses_db = {}
gov_grants_db = {}
gov_foia_requests_db = {}
gov_alerts_db = {}

# Banking expansion stores
banking_recovery_requests_db = {}
banking_device_trust_db = {}
banking_sessions_db = {}
banking_loan_applications_db = {}
banking_credit_limits_db = {}
banking_consents_db = {}
open_banking_tokens_db = {}
banking_wire_transfers_db = {}
banking_beneficiaries_db = {}
banking_kyc_documents_db = {}

# Ecommerce expansion stores
ecommerce_returns_db = {}
ecommerce_chargebacks_db = {}
ecommerce_vendor_payouts_db = {}
ecommerce_gift_cards_db = {}
ecommerce_order_exports_db = {}

# Telecom stores
telecom_subscribers_db = {}
telecom_sim_swaps_db = {}
telecom_plan_changes_db = {}
telecom_network_towers_db = {}
telecom_provisioning_db = {}
telecom_throttle_events_db = {}
telecom_cdr_exports_db = {}
telecom_invoices_db = {}
telecom_billing_adjustments_db = {}
telecom_payment_methods_db = {}
telecom_refunds_db = {}
telecom_porting_requests_db = {}
telecom_api_keys_db = {}
telecom_webhooks_db = {}
telecom_cdr_streams_db = {}
telecom_device_activations_db = {}
telecom_device_bindings_db = {}
telecom_imei_blacklist_db = {}
telecom_roaming_overrides_db = {}

# Energy & utilities stores
energy_dispatch_db = {}
energy_load_shed_db = {}
energy_breakers_db = {}
energy_outages_db = {}
energy_outage_dispatches_db = {}
energy_outage_restores_db = {}
energy_meter_readings_db = {}
energy_meter_disconnects_db = {}
energy_meter_firmware_db = {}
energy_billing_adjustments_db = {}
energy_autopay_db = {}
energy_refunds_db = {}
energy_customers_db = {}
energy_asset_maintenance_db = {}
energy_asset_calibration_db = {}
energy_assets_db = {}
energy_demand_response_db = {}
energy_tariff_overrides_db = {}
energy_der_interconnections_db = {}
