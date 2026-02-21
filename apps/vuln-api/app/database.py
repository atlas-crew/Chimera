"""
Database initialization and seed data for api-demo.

This module handles database creation and seeding with demo data
for WAF testing scenarios.
"""

import os
from datetime import datetime, timedelta
from app.models import db, User, BankAccount, Patient, InsurancePolicy, Transaction, Claim


def init_database(app):
    """
    Initialize database if USE_DATABASE environment variable is set.

    Args:
        app: Flask application instance
    """
    use_database = os.getenv('USE_DATABASE', 'false').lower() == 'true'

    if not use_database:
        return False

    # Configure SQLite database
    db_path = os.getenv('DATABASE_PATH', '/tmp/api-demo.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = os.getenv('SQL_DEBUG', 'false').lower() == 'true'

    # Initialize SQLAlchemy
    db.init_app(app)

    with app.app_context():
        # Drop and recreate all tables (fresh state on every restart)
        db.drop_all()
        db.create_all()

        # Seed demo data
        seed_data()

    return True


def seed_data():
    """
    Seed database with demo data for testing.
    Creates intentionally vulnerable data for WAF demonstrations.
    """
    print("Seeding database with demo data...")

    # Create users
    users = [
        User(
            email='admin@example.com',
            password='admin123',  # VULNERABLE: Weak password
            role='admin',
            full_name='Admin User',
            is_active=True
        ),
        User(
            email='john.doe@example.com',
            password='password',  # VULNERABLE: Default password
            role='user',
            full_name='John Doe',
            is_active=True
        ),
        User(
            email='doctor@hospital.com',
            password='doctor123',
            role='doctor',
            full_name='Dr. Sarah Smith',
            is_active=True
        ),
        User(
            email='agent@insurance.com',
            password='agent123',
            role='agent',
            full_name='Mike Johnson',
            is_active=True
        ),
        User(
            email='underwriter@insurance.com',
            password='underwriter123',
            role='underwriter',
            full_name='Emily Davis',
            is_active=True
        ),
    ]

    for user in users:
        db.session.add(user)

    db.session.commit()

    # Create bank accounts
    accounts = [
        BankAccount(
            account_number='ACC-1001',
            user_id=1,  # admin
            account_type='checking',
            balance=50000.00,
            routing_number='021000021'
        ),
        BankAccount(
            account_number='ACC-1002',
            user_id=2,  # john
            account_type='savings',
            balance=25000.00,
            routing_number='021000021'
        ),
        BankAccount(
            account_number='ACC-1003',
            user_id=2,  # john
            account_type='investment',
            balance=100000.00,
            routing_number='021000021'
        ),
    ]

    for account in accounts:
        db.session.add(account)

    db.session.commit()

    # Create patient records
    patients = [
        Patient(
            patient_id='PT-00001',
            full_name='Alice Anderson',
            ssn='123-45-6789',  # VULNERABLE: Real SSN format
            date_of_birth=datetime(1985, 3, 15).date(),
            diagnosis='Type 2 Diabetes',
            prescription='Metformin 500mg twice daily',
            insurance_id='INS-9876543',
            doctor_name='Dr. Sarah Smith',
            last_visit=datetime.utcnow() - timedelta(days=30),
            medical_record_number='MRN-0001'
        ),
        Patient(
            patient_id='PT-00002',
            full_name='Bob Builder',
            ssn='987-65-4321',
            date_of_birth=datetime(1978, 7, 22).date(),
            diagnosis='Hypertension',
            prescription='Lisinopril 10mg daily',
            insurance_id='INS-1234567',
            doctor_name='Dr. Sarah Smith',
            last_visit=datetime.utcnow() - timedelta(days=15),
            medical_record_number='MRN-0002'
        ),
        Patient(
            patient_id='PT-00003',
            full_name='Charlie Chen',
            ssn='555-12-3456',
            date_of_birth=datetime(1992, 11, 8).date(),
            diagnosis='Asthma',
            prescription='Albuterol inhaler as needed',
            insurance_id='INS-5555555',
            doctor_name='Dr. Sarah Smith',
            last_visit=datetime.utcnow() - timedelta(days=5),
            medical_record_number='MRN-0003'
        ),
    ]

    for patient in patients:
        db.session.add(patient)

    db.session.commit()

    # Create insurance policies
    policies = [
        InsurancePolicy(
            policy_number='POL-10001',
            user_id=2,  # john
            policy_type='auto',
            premium=1200.00,
            coverage_amount=50000.00,
            deductible=500.00,
            status='active',
            risk_score=45,
            underwriter='Emily Davis',
            start_date=datetime.utcnow() - timedelta(days=365),
            end_date=datetime.utcnow() + timedelta(days=365)
        ),
        InsurancePolicy(
            policy_number='POL-10002',
            user_id=2,  # john
            policy_type='home',
            premium=2400.00,
            coverage_amount=300000.00,
            deductible=1000.00,
            status='active',
            risk_score=25,
            underwriter='Emily Davis',
            start_date=datetime.utcnow() - timedelta(days=730),
            end_date=datetime.utcnow() + timedelta(days=365)
        ),
        InsurancePolicy(
            policy_number='POL-10003',
            user_id=1,  # admin
            policy_type='life',
            premium=5000.00,
            coverage_amount=1000000.00,
            deductible=0.00,
            status='active',
            risk_score=15,
            underwriter='Emily Davis',
            start_date=datetime.utcnow() - timedelta(days=1095),
            end_date=datetime.utcnow() + timedelta(days=3650)
        ),
    ]

    for policy in policies:
        db.session.add(policy)

    db.session.commit()

    # Create transactions
    transactions = [
        Transaction(
            transaction_id='TXN-00001',
            from_account_id=1,
            to_account_id=2,
            amount=5000.00,
            transaction_type='transfer',
            status='completed',
            aml_flag=False,
            timestamp=datetime.utcnow() - timedelta(hours=24)
        ),
        Transaction(
            transaction_id='TXN-00002',
            from_account_id=2,
            to_account_id=999,  # External account
            amount=15000.00,
            transaction_type='wire',
            status='flagged',
            aml_flag=True,
            flagged_reason='Large wire transfer to unknown account',
            timestamp=datetime.utcnow() - timedelta(hours=12)
        ),
        Transaction(
            transaction_id='TXN-00003',
            from_account_id=3,
            to_account_id=1,
            amount=2500.00,
            transaction_type='transfer',
            status='completed',
            aml_flag=False,
            timestamp=datetime.utcnow() - timedelta(hours=6)
        ),
    ]

    for transaction in transactions:
        db.session.add(transaction)

    db.session.commit()

    # Create claims
    claims = [
        Claim(
            claim_number='CLM-00001',
            policy_id=1,  # auto policy
            claim_amount=3500.00,
            claim_type='accident',
            description='Minor fender bender, front bumper damage',
            status='approved',
            fraud_flag=False,
            fraud_score=15,
            adjuster='Mike Johnson',
            submitted_date=datetime.utcnow() - timedelta(days=45),
            approved_amount=3500.00
        ),
        Claim(
            claim_number='CLM-00002',
            policy_id=2,  # home policy
            claim_amount=25000.00,
            claim_type='property_damage',
            description='Water damage from burst pipe',
            status='under_review',
            fraud_flag=True,
            fraud_score=75,
            adjuster='Mike Johnson',
            submitted_date=datetime.utcnow() - timedelta(days=10),
            approved_amount=None
        ),
        Claim(
            claim_number='CLM-00003',
            policy_id=1,  # auto policy
            claim_amount=1200.00,
            claim_type='theft',
            description='Stolen catalytic converter',
            status='paid',
            fraud_flag=False,
            fraud_score=30,
            adjuster='Mike Johnson',
            submitted_date=datetime.utcnow() - timedelta(days=60),
            approved_amount=1200.00
        ),
    ]

    for claim in claims:
        db.session.add(claim)

    db.session.commit()

    print(f"✓ Seeded {len(users)} users")
    print(f"✓ Seeded {len(accounts)} bank accounts")
    print(f"✓ Seeded {len(patients)} patient records")
    print(f"✓ Seeded {len(policies)} insurance policies")
    print(f"✓ Seeded {len(transactions)} transactions")
    print(f"✓ Seeded {len(claims)} claims")
    print("Database seeding complete!")
