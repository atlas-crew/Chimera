"""
Demo data initialization for testing endpoints.
"""

from datetime import datetime
from app.models import *
from app.models import data_stores as _data_stores


def _add_user_record(user_id: str, user: dict) -> None:
    if users_db is _data_stores.users_db:
        add_user(user_id, user)
    else:
        users_db[user_id] = user


def init_demo_data():
    """Initialize demo data for testing endpoints"""
    global users_db, accounts_db, transactions_db, products_db, mobile_devices_db
    global medical_records_db, providers_db, password_reset_requests, refresh_tokens_db
    global mfa_challenges_db, registered_devices_db, api_keys_db, card_profiles_db
    global merchant_applications_db, bin_range_catalog, payment_test_events
    global customers_db, policies_db, claims_db, claims_evidence_db, loyalty_accounts_db
    global vendor_registry_db, vendor_documents_db, reviews_db, ratings_db
    global customer_payment_methods_db, shipping_zones_db, vendor_inventory_events
    global cloud_service_registry, apt_operations_log, underwriting_rules_db
    global actuarial_models_db, orders_db, payment_methods_db, tax_calculations_db
    global promotions_db, discounts_db, shipping_addresses_db, fraudulent_methods_db
    global transaction_exports_db, currency_rates_db, audit_suppressions_db
    global saas_tenants_db, saas_projects_db, saas_users_db, saas_shared_links_db
    global saas_billing_invoices_db, saas_billing_usage_db, saas_workspace_settings_db
    global saas_coupons_db, saas_refresh_tokens_db, saas_audit_logs_db
    global saas_org_invites_db, saas_saml_configs_db, saas_session_revocations_db
    global gov_cases_db, gov_records_db, gov_users_db, gov_access_cards_db
    global gov_service_requests_db, gov_audit_logs_db, gov_credentials_db
    global gov_benefits_applications_db, gov_classifications_db, gov_permits_db
    global banking_wire_transfers_db, banking_beneficiaries_db, banking_kyc_documents_db
    global ecommerce_gift_cards_db, ecommerce_order_exports_db
    global telecom_subscribers_db, telecom_sim_swaps_db, telecom_plan_changes_db
    global telecom_network_towers_db, telecom_provisioning_db, telecom_throttle_events_db
    global telecom_cdr_exports_db, telecom_invoices_db, telecom_billing_adjustments_db
    global telecom_payment_methods_db, telecom_refunds_db, telecom_porting_requests_db
    global telecom_api_keys_db, telecom_webhooks_db, telecom_cdr_streams_db
    global telecom_device_activations_db, telecom_device_bindings_db, telecom_imei_blacklist_db
    global telecom_roaming_overrides_db
    global energy_dispatch_db, energy_load_shed_db, energy_breakers_db, energy_outages_db
    global energy_outage_dispatches_db, energy_outage_restores_db, energy_meter_readings_db
    global energy_meter_disconnects_db, energy_meter_firmware_db, energy_billing_adjustments_db
    global energy_autopay_db, energy_refunds_db, energy_customers_db
    global energy_asset_maintenance_db, energy_asset_calibration_db, energy_assets_db
    global energy_demand_response_db, energy_tariff_overrides_db, energy_der_interconnections_db

    # Demo users
    _add_user_record('demo@chimera.com', {
        'id': 'user_123456',
        'email': 'demo@chimera.com',
        'password': 'demo123',  # Never do this in real apps
        'name': ' Demo User',
        'created': datetime.now().isoformat()
    })

    # Demo accounts
    accounts_db['user_123456'] = [
        {
            'account_id': 'ACC-001',
            'type': 'checking',
            'balance': 15420.50,
            'account_number': '****1234'
        },
        {
            'account_id': 'ACC-002',
            'type': 'savings',
            'balance': 52100.25,
            'account_number': '****5678'
        }
    ]

    banking_beneficiaries_db.clear()
    banking_beneficiaries_db.update({
        'BEN-1001': {
            'beneficiary_id': 'BEN-1001',
            'name': 'Trusted Recipient',
            'account_number': '****4455',
            'bank': 'Example Bank',
            'created_at': datetime.now().isoformat()
        }
    })
    banking_wire_transfers_db.clear()
    banking_wire_transfers_db.update({
        'WIRE-1001': {
            'wire_id': 'WIRE-1001',
            'amount': 250000.00,
            'beneficiary': 'Trusted Recipient',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
    })
    banking_kyc_documents_db.clear()
    banking_kyc_documents_db.update({
        'DOC-1001': {
            'document_id': 'DOC-1001',
            'customer_id': 'CUST-001',
            'doc_type': 'passport',
            'verified': False,
            'uploaded_at': datetime.now().isoformat()
        }
    })

    # Demo products
    products_db['PROD-001'] = {'name': 'Security Scanner Pro', 'price': 299.99}
    products_db['PROD-002'] = {'name': 'Threat Detection Module', 'price': 199.99}
    products_db['PROD-003'] = {'name': 'Compliance Package', 'price': 499.99}

    # Demo mobile devices
    mobile_devices_db['user_123456'] = [
        {
            'device_id': 'DEVICE-001',
            'device_name': 'iPhone 14 Pro',
            'fingerprint': 'sha256:a1b2c3d4e5f6...',
            'trusted': True,
            'registered_date': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat()
        }
    ]

    # Security/authentication supporting data
    password_reset_requests.clear()
    refresh_tokens_db.clear()
    mfa_challenges_db.clear()
    registered_devices_db['user_123456'] = [
        {
            'device_id': 'DEVICE-001',
            'device_name': 'iPhone 14 Pro',
            'fingerprint': 'sha256:a1b2c3d4e5f6...'
        }
    ]
    api_keys_db['user_123456'] = [
        {
            'key_id': 'API-PRIMARY',
            'api_key': 'tx_demo_primary_key',
            'scopes': ['payments', 'accounts'],
            'created_at': datetime.now().isoformat()
        }
    ]

    card_profiles_db.clear()
    card_profiles_db.update({
        '411111': {'brand': 'VISA', 'country': 'US', 'issuer': ' Demo Bank'},
        '550000': {'brand': 'MASTERCARD', 'country': 'US', 'issuer': ' Demo Bank'},
        '340000': {'brand': 'AMEX', 'country': 'US', 'issuer': ' Demo Bank'}
    })

    merchant_applications_db.clear()
    bin_range_catalog[:] = [
        {'bin': '411111', 'scheme': 'VISA', 'type': 'credit', 'country': 'US'},
        {'bin': '550000', 'scheme': 'MASTERCARD', 'type': 'debit', 'country': 'US'},
        {'bin': '601100', 'scheme': 'DISCOVER', 'type': 'credit', 'country': 'US'},
        {'bin': '352800', 'scheme': 'JCB', 'type': 'credit', 'country': 'JP'}
    ]
    payment_test_events.clear()

    # Customer and policy data
    customers_db.clear()
    customers_db.update({
        'CUST-001': {
            'customer_id': 'CUST-001',
            'name': 'John Smith',
            'segment': 'retail',
            'risk_score': 0.32,
            'policies': ['POL-123456789']
        },
        'CUST-002': {
            'customer_id': 'CUST-002',
            'name': 'Jane Doe',
            'segment': 'small_business',
            'risk_score': 0.58,
            'policies': ['POL-987654321']
        }
    })

    policies_db.clear()
    policies_db.update({
        'POL-123456789': {
            'policy_id': 'POL-123456789',
            'type': 'auto',
            'coverage_limit': 500000,
            'premium': 1200,
            'status': 'active',
            'overrides': []
        },
        'POL-987654321': {
            'policy_id': 'POL-987654321',
            'type': 'home',
            'coverage_limit': 750000,
            'premium': 1800,
            'status': 'active',
            'overrides': []
        }
    })

    claims_evidence_db.clear()

    loyalty_accounts_db.clear()
    loyalty_accounts_db.update({
        'CUST-001': {'points_balance': 12500, 'tier': 'gold'},
        'CUST-002': {'points_balance': 4200, 'tier': 'silver'}
    })

    customer_payment_methods_db.clear()
    customer_payment_methods_db.update({
        'CUST-001': [
            {'type': 'card', 'last4': '1234', 'brand': 'VISA', 'primary': True},
            {'type': 'bank_account', 'last4': '7890', 'primary': False}
        ],
        'CUST-002': [
            {'type': 'card', 'last4': '9876', 'brand': 'MASTERCARD', 'primary': True}
        ]
    })

    vendor_registry_db.clear()
    vendor_registry_db.update({
        'VEND-001': {
            'vendor_id': 'VEND-001',
            'name': 'SecureTech Solutions',
            'status': 'active',
            'privileges': ['standard'],
            'inventory_integrity': 'stable'
        }
    })
    vendor_documents_db.clear()
    reviews_db.clear()
    ratings_db.clear()
    shipping_zones_db.clear()
    shipping_zones_db.update({
        'domestic': {'base_rate': 5.99, 'surcharge_per_lb': 0.75},
        'international': {'base_rate': 24.99, 'surcharge_per_lb': 1.95},
        'express': {'base_rate': 14.99, 'surcharge_per_lb': 1.25}
    })
    vendor_inventory_events.clear()

    orders_db.clear()
    orders_db.update({
        'ORDER-1001': {
            'order_id': 'ORDER-1001',
            'status': 'processing',
            'customer_id': 'CUST-001',
            'total': 1299.99,
            'override_history': []
        }
    })

    ecommerce_gift_cards_db.clear()
    ecommerce_gift_cards_db.update({
        'GC-1001': {
            'code': 'GC-1001',
            'balance': 250.00,
            'active': True,
            'issued_at': datetime.now().isoformat()
        }
    })
    ecommerce_order_exports_db.clear()
    ecommerce_order_exports_db.update({
        'EXP-1001': {
            'export_id': 'EXP-1001',
            'format': 'csv',
            'include_pii': True,
            'created_at': datetime.now().isoformat()
        }
    })

    cloud_service_registry.update({
        'discovery': ['api-gateway', 'service-mesh', 'billing-service'],
        'sensitive_services': ['secrets-manager', 'payment-processor', 'user-directory'],
        'policies': ['zero-trust', 'mTLS', 'rate-limits']
    })
    apt_operations_log.clear()

    underwriting_rules_db.clear()
    underwriting_rules_db.extend([
        {
            'rule_id': 'UW-001',
            'description': 'Auto claims over $50k require manual underwriting review',
            'status': 'active',
            'severity': 'high'
        },
        {
            'rule_id': 'UW-002',
            'description': 'Home policies in flood zones require 2x premium multiplier',
            'status': 'active',
            'severity': 'medium'
        },
        {
            'rule_id': 'UW-003',
            'description': 'Life insurance applicants over age 65 flagged for enhanced due diligence',
            'status': 'active',
            'severity': 'high'
        }
    ])

    actuarial_models_db.clear()
    actuarial_models_db.update({
        'MODEL-AUTO-RISK': {
            'model_id': 'MODEL-AUTO-RISK',
            'name': 'Auto Risk Composite',
            'version': '3.4',
            'status': 'active',
            'last_calibrated': datetime.now().isoformat()
        },
        'MODEL-HOME-RISK': {
            'model_id': 'MODEL-HOME-RISK',
            'name': 'Home Catastrophe Risk',
            'version': '2.1',
            'status': 'active',
            'last_calibrated': datetime.now().isoformat()
        }
    })

    # E-commerce checkout data
    payment_methods_db.clear()
    payment_methods_db.update({
        'visa': {'enabled': True, 'processing_fee': 0.029},
        'mastercard': {'enabled': True, 'processing_fee': 0.029},
        'amex': {'enabled': True, 'processing_fee': 0.035},
        'paypal': {'enabled': True, 'processing_fee': 0.031},
        'crypto': {'enabled': False, 'processing_fee': 0.01}
    })

    tax_calculations_db.clear()
    promotions_db.clear()
    promotions_db.update({
        'SAVE10': {'discount': 0.10, 'active': True, 'min_purchase': 50},
        'SUMMER25': {'discount': 0.25, 'active': True, 'min_purchase': 100},
        'ADMIN50': {'discount': 0.50, 'active': True, 'min_purchase': 0}
    })

    discounts_db.clear()
    shipping_addresses_db.clear()
    fraudulent_methods_db.clear()
    transaction_exports_db.clear()

    currency_rates_db.clear()
    currency_rates_db.update({
        'USD': {'rate': 1.0, 'symbol': '$'},
        'EUR': {'rate': 0.92, 'symbol': '€'},
        'GBP': {'rate': 0.79, 'symbol': '£'},
        'JPY': {'rate': 149.50, 'symbol': '¥'}
    })

    audit_suppressions_db.clear()

    # Demo medical records
    medical_records_db['patient_789'] = {
        'patient_id': 'patient_789',
        'name': 'John D. Patient',
        'dob': '1980-05-15',
        'ssn': '***-**-1234',
        'records': [
            {
                'record_id': 'MED-001',
                'date': '2024-01-15',
                'provider': 'Dr. Smith',
                'diagnosis': 'Routine checkup',
                'sensitive': False
            },
            {
                'record_id': 'MED-002',
                'date': '2024-02-20',
                'provider': 'Dr. Johnson',
                'diagnosis': 'Mental health consultation',
                'sensitive': True
            }
        ]
    }

    # Demo healthcare providers
    providers_db['PROV-001'] = {
        'provider_id': 'PROV-001',
        'name': 'City General Hospital',
        'type': 'hospital',
        'network': 'preferred',
        'specialties': ['emergency', 'surgery', 'cardiology']
    }
    providers_db['PROV-002'] = {
        'provider_id': 'PROV-002',
        'name': 'Mental Health Associates',
        'type': 'clinic',
        'network': 'in-network',
        'specialties': ['psychiatry', 'therapy']
    }

    # Demo insurance claims
    claims_db.clear()
    claims_db.update({
        'CLM-1001': {
            'claim_id': 'CLM-1001',
            'policy_number': 'POL-123456789',
            'claim_type': 'auto',
            'claim_amount': 12500,
            'status': 'under_review',
            'fraud_score': 0.18,
            'submitted_at': datetime.now().isoformat(),
            'adjuster': 'ADJ-428'
        },
        'CLM-1002': {
            'claim_id': 'CLM-1002',
            'policy_number': 'POL-987654321',
            'claim_type': 'home',
            'claim_amount': 54000,
            'status': 'approved',
            'fraud_score': 0.62,
            'submitted_at': datetime.now().isoformat(),
            'adjuster': 'ADJ-771'
        }
    })

    # Demo SaaS tenants
    saas_tenants_db.clear()
    saas_tenants_db.update({
        'tenant-1': {
            'tenant_id': 'tenant-1',
            'name': 'Acme Analytics',
            'plan': 'growth',
            'owner_id': 'user-1',
            'data_region': 'us-east-1',
            'seat_count': 45,
            'created_at': datetime.now().isoformat()
        },
        'tenant-2': {
            'tenant_id': 'tenant-2',
            'name': 'Northwind Labs',
            'plan': 'starter',
            'owner_id': 'user-2',
            'data_region': 'us-west-2',
            'seat_count': 12,
            'created_at': datetime.now().isoformat()
        }
    })
    saas_projects_db.clear()
    saas_projects_db.update({
        'tenant-1': [
            {
                'project_id': 'proj-101',
                'name': 'Revenue Forecasting',
                'status': 'active',
                'last_updated': datetime.now().isoformat()
            },
            {
                'project_id': 'proj-102',
                'name': 'Customer Churn',
                'status': 'active',
                'last_updated': datetime.now().isoformat()
            }
        ],
        'tenant-2': [
            {
                'project_id': 'proj-201',
                'name': 'Ops Dashboards',
                'status': 'paused',
                'last_updated': datetime.now().isoformat()
            }
        ]
    })
    saas_users_db.clear()
    saas_users_db.update({
        'user-1': {'user_id': 'user-1', 'email': 'owner@acme.io', 'role': 'owner', 'tenant_id': 'tenant-1'},
        'user-2': {'user_id': 'user-2', 'email': 'admin@northwind.io', 'role': 'admin', 'tenant_id': 'tenant-2'},
        'user-3': {'user_id': 'user-3', 'email': 'viewer@acme.io', 'role': 'viewer', 'tenant_id': 'tenant-1'}
    })
    rebuild_saas_user_index()
    saas_shared_links_db.clear()
    saas_shared_links_db.extend([
        {
            'share_id': 'share-01',
            'resource': 'proj-101/report',
            'private': False,
            'expires_at': None
        },
        {
            'share_id': 'share-02',
            'resource': 'proj-102/forecast',
            'private': True,
            'expires_at': datetime.now().isoformat()
        }
    ])
    saas_org_invites_db.clear()
    saas_org_invites_db.update({
        'invite-1': {
            'invite_id': 'invite-1',
            'email': 'new.user@acme.io',
            'role': 'admin',
            'tenant_id': 'tenant-1',
            'created_at': datetime.now().isoformat()
        }
    })
    saas_saml_configs_db.clear()
    saas_saml_configs_db.update({
        'tenant-1': {
            'tenant_id': 'tenant-1',
            'entity_id': 'urn:acme:saml',
            'sso_url': 'https://idp.example/sso',
            'last_updated': datetime.now().isoformat()
        }
    })
    saas_session_revocations_db.clear()
    saas_session_revocations_db.update({
        'sess-1': {
            'session_id': 'sess-1',
            'revoked': True,
            'revoked_at': datetime.now().isoformat()
        }
    })
    saas_billing_invoices_db.clear()
    saas_billing_invoices_db.update({
        'inv-1001': {
            'invoice_id': 'inv-1001',
            'tenant_id': 'tenant-1',
            'amount': 2490,
            'status': 'open',
            'issued_at': datetime.now().isoformat()
        }
    })
    saas_billing_usage_db.clear()
    saas_billing_usage_db.update({
        'tenant-1': {'usage_units': 12000, 'period': '2025-12'},
        'tenant-2': {'usage_units': 3200, 'period': '2025-12'}
    })
    saas_workspace_settings_db.clear()
    saas_workspace_settings_db.update({
        'tenant-1': {'data_retention_days': 90, 'audit_enabled': True, 'ip_allowlist': []},
        'tenant-2': {'data_retention_days': 30, 'audit_enabled': True, 'ip_allowlist': ['10.0.0.0/24']}
    })
    saas_coupons_db.clear()
    saas_coupons_db.update({
        'FREE100': {'discount': 1.0, 'expires_at': '2026-01-01'},
        'STACK10': {'discount': 0.10, 'expires_at': '2026-06-01'}
    })
    saas_refresh_tokens_db.clear()
    saas_refresh_tokens_db.update({
        'user-1': {'refresh_token': 'refresh-tenant-1', 'device_id': 'laptop-1'}
    })
    saas_audit_logs_db.clear()
    saas_audit_logs_db.extend([
        {'log_id': 'audit-01', 'event': 'login', 'actor': 'user-1', 'timestamp': datetime.now().isoformat()},
        {'log_id': 'audit-02', 'event': 'export', 'actor': 'user-2', 'timestamp': datetime.now().isoformat()}
    ])

    # Demo government data
    gov_cases_db.clear()
    gov_cases_db.update({
        '1': {
            'case_id': '1',
            'citizen_id': 'CIT-1001',
            'program': 'benefits',
            'status': 'pending',
            'assigned_agent': 'AGT-045',
            'ssn': '123-45-6789',
            'last_updated': datetime.now().isoformat()
        },
        '2': {
            'case_id': '2',
            'citizen_id': 'CIT-1002',
            'program': 'permits',
            'status': 'review',
            'assigned_agent': 'AGT-087',
            'ssn': '987-65-4321',
            'last_updated': datetime.now().isoformat()
        }
    })
    gov_records_db.clear()
    gov_records_db.update({
        'record-1': {
            'record_id': 'record-1',
            'citizen_id': 'CIT-1001',
            'name': 'Alex Rivera',
            'ssn': '123-45-6789',
            'address': '100 Main St, City, ST 12345',
            'classification': 'restricted',
            'status': 'active'
        },
        'record-2': {
            'record_id': 'record-2',
            'citizen_id': 'CIT-1002',
            'name': 'Jordan Lee',
            'ssn': '987-65-4321',
            'address': '220 Oak St, City, ST 12345',
            'classification': 'confidential',
            'status': 'active'
        }
    })
    gov_users_db.clear()
    gov_users_db.update({
        'user-1': {'user_id': 'user-1', 'name': 'Case Worker', 'role': 'case_worker', 'agency': 'benefits'},
        'user-2': {'user_id': 'user-2', 'name': 'Supervisor', 'role': 'supervisor', 'agency': 'permits'}
    })
    gov_access_cards_db.clear()
    gov_access_cards_db.update({
        '1': {'card_id': '1', 'holder': 'user-1', 'clearance': 'public', 'active': True},
        '2': {'card_id': '2', 'holder': 'user-2', 'clearance': 'restricted', 'active': True}
    })
    gov_service_requests_db.clear()
    gov_service_requests_db.update({
        'SR-1001': {
            'request_id': 'SR-1001',
            'type': 'address_change',
            'priority': 'normal',
            'status': 'open',
            'submitted_at': datetime.now().isoformat()
        }
    })
    gov_audit_logs_db.clear()
    gov_audit_logs_db.update({
        'log-1': {'log_id': 'log-1', 'event': 'case_update', 'actor': 'user-1'},
        'log-2': {'log_id': 'log-2', 'event': 'record_export', 'actor': 'user-2'}
    })
    gov_credentials_db.clear()
    gov_credentials_db.update({
        'cred-1': {'user_id': 'user-1', 'hash': 'md5:5f4dcc3b5aa765d61d8327deb882cf99'},
        'cred-2': {'user_id': 'user-2', 'hash': 'md5:098f6bcd4621d373cade4e832627b4f6'}
    })
    gov_benefits_applications_db.clear()
    gov_benefits_applications_db.update({
        'APP-1001': {
            'application_id': 'APP-1001',
            'citizen_id': 'CIT-1001',
            'program': 'housing',
            'status': 'approved',
            'submitted_at': datetime.now().isoformat()
        }
    })
    gov_classifications_db.clear()
    gov_classifications_db.update({
        'record-1': 'restricted',
        'record-2': 'confidential'
    })

    telecom_subscribers_db.clear()
    telecom_subscribers_db.update({
        'sub-1001': {
            'subscriber_id': 'sub-1001',
            'name': 'Alex Rivera',
            'plan_id': 'unlimited',
            'msisdn': '+15551230001',
            'status': 'active',
            'last_seen': datetime.now().isoformat()
        }
    })
    telecom_network_towers_db.clear()
    telecom_network_towers_db.update({
        'tower-1': {
            'tower_id': 'tower-1',
            'region': 'north',
            'status': 'active',
            'carrier': '5G'
        }
    })
    telecom_invoices_db.clear()
    telecom_invoices_db.update({
        'inv-1001': {
            'invoice_id': 'inv-1001',
            'amount': 129.99,
            'status': 'open'
        }
    })
    telecom_porting_requests_db.clear()
    telecom_porting_requests_db.update({
        'PORT-1001': {
            'request_id': 'PORT-1001',
            'number': '+15551230001',
            'bypass_pin': False,
            'status': 'submitted'
        }
    })
    telecom_api_keys_db.clear()
    telecom_api_keys_db.update({
        'key-1': {
            'key_id': 'key-1',
            'label': 'carrier-api',
            'secret': 'telecom-secret-key'
        }
    })
    telecom_device_bindings_db.clear()
    telecom_device_bindings_db.update({
        'bind-1': {
            'binding_id': 'bind-1',
            'subscriber_id': 'sub-1001',
            'device_id': 'dev-1001',
            'sim_id': 'SIM-1001',
            'status': 'active'
        }
    })
    telecom_imei_blacklist_db.clear()
    telecom_imei_blacklist_db.update({
        'IMEI-1001': {
            'imei': 'IMEI-1001',
            'blacklisted': False,
            'updated_at': datetime.now().isoformat()
        }
    })
    telecom_roaming_overrides_db.clear()
    telecom_roaming_overrides_db.update({
        'roam-1': {
            'subscriber_id': 'sub-1001',
            'region': 'EU',
            'override_policy': True,
            'updated_at': datetime.now().isoformat()
        }
    })

    energy_outages_db.clear()
    energy_outages_db.update({
        'out-1001': {
            'outage_id': 'out-1001',
            'status': 'reported',
            'customers_impacted': 1200,
            'region': 'west'
        }
    })
    energy_meter_readings_db.clear()
    energy_meter_readings_db.update({
        'meter-1001': {
            'meter_id': 'meter-1001',
            'kwh': 582.4,
            'timestamp': datetime.now().isoformat()
        }
    })
    energy_customers_db.clear()
    energy_customers_db.update({
        'cust-1001': {
            'customer_id': 'cust-1001',
            'name': 'Jordan Lee',
            'status': 'active'
        }
    })
    energy_assets_db.clear()
    energy_assets_db.update({
        'asset-1001': {
            'asset_id': 'asset-1001',
            'type': 'substation',
            'status': 'active'
        }
    })
    energy_demand_response_db.clear()
    energy_demand_response_db.update({
        'dr-1001': {
            'event_id': 'dr-1001',
            'region': 'west',
            'override_limits': True,
            'created_at': datetime.now().isoformat()
        }
    })
    energy_tariff_overrides_db.clear()
    energy_tariff_overrides_db.update({
        'tariff-1': {
            'tariff_id': 'tariff-1',
            'rate_override': 0.01,
            'effective_at': datetime.now().isoformat()
        }
    })
    energy_der_interconnections_db.clear()
    energy_der_interconnections_db.update({
        'der-1': {
            'interconnection_id': 'der-1',
            'status': 'approved',
            'bypass_review': True,
            'approved_at': datetime.now().isoformat()
        }
    })


def reset_demo_data():
    """
    Reset all demo data to initial state.

    This clears all data stores and re-initializes them with fresh demo data.
    Useful for resetting between test runs or demo sessions.
    """
    from app.models import data_stores

    # Clear all data stores
    for attr_name in dir(data_stores):
        if not attr_name.startswith('_'):
            attr = getattr(data_stores, attr_name)
            if isinstance(attr, dict):
                attr.clear()
            elif isinstance(attr, list):
                attr.clear()

    # Re-initialize with fresh data
    init_demo_data()


def get_demo_user() -> dict:
    """
    Get the default demo user credentials and data.

    Returns:
        Dictionary with demo user information

    Example:
        demo_user = get_demo_user()
        email = demo_user['email']
        password = demo_user['password']
    """
    return {
        'id': 'user_123456',
        'email': 'demo@chimera.com',
        'password': 'demo123',
        'name': ' Demo User'
    }


def get_demo_customer() -> dict:
    """
    Get the default demo customer data.

    Returns:
        Dictionary with demo customer information
    """
    return {
        'customer_id': 'CUST-001',
        'name': 'John Smith',
        'segment': 'retail',
        'risk_score': 0.32
    }


def seed_additional_users(count: int = 10) -> list:
    """
    Seed additional test users for load testing.

    Args:
        count: Number of users to create

    Returns:
        List of created user dictionaries
    """
    users = []
    for i in range(count):
        user_id = f'user_{i+1000}'
        email = f'testuser{i+1}@example.com'

        user = {
            'id': user_id,
            'email': email,
            'password': f'test{i+1}123',
            'name': f'Test User {i+1}',
            'created': datetime.now().isoformat()
        }

        _add_user_record(email, user)
        users.append(user)

    return users


def seed_additional_products(count: int = 50) -> list:
    """
    Seed additional products for e-commerce testing.

    Args:
        count: Number of products to create

    Returns:
        List of created product dictionaries
    """
    from app.models import products_db
    import random

    product_categories = [
        'Security Tools', 'Monitoring Solutions', 'Compliance Packages',
        'Analytics Platforms', 'Developer Tools', 'Enterprise Software'
    ]

    products = []
    for i in range(count):
        product_id = f'PROD-{i+1000:04d}'
        category = random.choice(product_categories)

        product = {
            'product_id': product_id,
            'name': f'{category} Edition {i+1}',
            'price': round(random.uniform(49.99, 999.99), 2),
            'category': category,
            'in_stock': random.choice([True, True, True, False]),
            'stock_quantity': random.randint(0, 500)
        }

        products_db[product_id] = product
        products.append(product)

    return products


def seed_transactions(user_id: str, count: int = 20) -> list:
    """
    Seed transaction history for a user.

    Args:
        user_id: User ID to create transactions for
        count: Number of transactions to create

    Returns:
        List of created transaction dictionaries
    """
    from app.models import transactions_db
    import random
    from datetime import timedelta

    if user_id not in transactions_db:
        transactions_db[user_id] = []

    transactions = []
    base_date = datetime.now()

    transaction_types = ['deposit', 'withdrawal', 'transfer', 'payment']
    descriptions = [
        'Online purchase', 'ATM withdrawal', 'Direct deposit',
        'Bill payment', 'Wire transfer', 'Mobile payment'
    ]

    for i in range(count):
        transaction_date = base_date - timedelta(days=random.randint(0, 90))

        transaction = {
            'transaction_id': f'TXN-{random.randint(100000, 999999)}',
            'type': random.choice(transaction_types),
            'amount': round(random.uniform(10.00, 500.00), 2),
            'description': random.choice(descriptions),
            'date': transaction_date.isoformat(),
            'status': 'completed'
        }

        transactions_db[user_id].append(transaction)
        transactions.append(transaction)

    return transactions


def get_seed_statistics() -> dict:
    """
    Get statistics about current demo data.

    Returns:
        Dictionary with counts of various data types
    """
    from app.models import (
        users_db, accounts_db, transactions_db, products_db,
        customers_db, policies_db, orders_db, medical_records_db
    )

    stats = {
        'users': len(users_db),
        'accounts': sum(len(v) if isinstance(v, list) else 1 for v in accounts_db.values()),
        'transactions': sum(len(v) if isinstance(v, list) else 1 for v in transactions_db.values()),
        'products': len(products_db),
        'customers': len(customers_db),
        'policies': len(policies_db),
        'orders': len(orders_db),
        'medical_records': len(medical_records_db)
    }

    return stats


def create_predictable_test_data(seed: int = 42) -> dict:
    """
    Create predictable test data for automated testing.

    Uses a fixed random seed to ensure reproducibility.

    Args:
        seed: Random seed for reproducibility

    Returns:
        Dictionary with created test data references
    """
    import random
    random.seed(seed)

    # Create predictable users
    test_users = seed_additional_users(5)

    # Create predictable products
    test_products = seed_additional_products(10)

    # Create predictable transactions
    test_transactions = []
    for user in test_users:
        txns = seed_transactions(user['id'], 5)
        test_transactions.extend(txns)

    random.seed()  # Reset random seed

    return {
        'users': test_users,
        'products': test_products,
        'transactions': test_transactions
    }


def export_demo_data() -> dict:
    """
    Export all current demo data for backup or inspection.

    Returns:
        Dictionary with all data store contents
    """
    from app.models import data_stores

    export = {}
    for attr_name in dir(data_stores):
        if not attr_name.startswith('_'):
            attr = getattr(data_stores, attr_name)
            if isinstance(attr, (dict, list)):
                export[attr_name] = attr

    return export


def import_demo_data(data: dict) -> bool:
    """
    Import demo data from an export.

    Args:
        data: Dictionary with data to import

    Returns:
        True if successful, False otherwise
    """
    try:
        from app.models import data_stores

        for key, value in data.items():
            if hasattr(data_stores, key):
                attr = getattr(data_stores, key)
                if isinstance(attr, dict) and isinstance(value, dict):
                    attr.clear()
                    attr.update(value)
                elif isinstance(attr, list) and isinstance(value, list):
                    attr.clear()
                    attr.extend(value)

        return True
    except Exception:
        return False
