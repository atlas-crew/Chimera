"""
Database initialization and seed data for the SQLite-backed demos.

Flask-SQLAlchemy is gone: this module owns a plain SQLAlchemy 2.0 engine
plus a thread-safe ``sessionmaker``. ``init_database()`` is invoked once
from the ASGI lifespan (and the legacy Flask factory during the migration)
when ``USE_DATABASE=true``.

The injection demos in ``app.blueprints.database_vulnerable`` reach for
``get_session()`` to obtain a SQLAlchemy ``Session`` and call
``session.connection().connection.cursor()`` for raw DB-API access — this
preserves the f-string SQL paths that the WAF tests target.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.orm import (
    Base,
    BankAccount,
    Claim,
    InsurancePolicy,
    Patient,
    Transaction,
    User,
)


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def is_database_enabled() -> bool:
    """True iff USE_DATABASE=true in the environment."""
    return os.getenv("USE_DATABASE", "false").lower() == "true"


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError(
            "Database has not been initialized. Call init_database() during app startup."
        )
    return _engine


def get_session() -> Session:
    """Return a fresh ``Session`` bound to the configured engine."""
    if _SessionLocal is None:
        raise RuntimeError(
            "Database has not been initialized. Call init_database() during app startup."
        )
    return _SessionLocal()


def init_database() -> bool:
    """Initialize the engine, recreate tables, and seed demo data.

    Returns ``True`` when the database was initialized, ``False`` when
    ``USE_DATABASE`` is not enabled.
    """
    global _engine, _SessionLocal

    if not is_database_enabled():
        return False

    db_path = os.getenv("DATABASE_PATH", "/tmp/api-demo.db")
    echo = os.getenv("SQL_DEBUG", "false").lower() == "true"

    # ``check_same_thread=False`` lets a single SQLite connection be used
    # across Starlette's threadpool when sync handlers are dispatched there.
    _engine = create_engine(
        f"sqlite:///{db_path}",
        echo=echo,
        connect_args={"check_same_thread": False},
        future=True,
    )
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, future=True)

    # Fresh state every boot — same semantics as the Flask version.
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)

    with _SessionLocal() as session:
        seed_data(session)

    return True


def seed_data(session: Session) -> None:
    """Populate the SQLite database with the demo fixtures used by WAF tests."""
    print("Seeding database with demo data...")

    users = [
        User(
            email="admin@example.com",
            password="admin123",  # VULNERABLE: weak password
            role="admin",
            full_name="Admin User",
            is_active=True,
        ),
        User(
            email="john.doe@example.com",
            password="password",  # VULNERABLE: default password
            role="user",
            full_name="John Doe",
            is_active=True,
        ),
        User(
            email="doctor@hospital.com",
            password="doctor123",
            role="doctor",
            full_name="Dr. Sarah Smith",
            is_active=True,
        ),
        User(
            email="agent@insurance.com",
            password="agent123",
            role="agent",
            full_name="Mike Johnson",
            is_active=True,
        ),
        User(
            email="underwriter@insurance.com",
            password="underwriter123",
            role="underwriter",
            full_name="Emily Davis",
            is_active=True,
        ),
    ]
    session.add_all(users)
    session.commit()

    accounts = [
        BankAccount(
            account_number="ACC-1001",
            user_id=1,  # admin
            account_type="checking",
            balance=50000.00,
            routing_number="021000021",
        ),
        BankAccount(
            account_number="ACC-1002",
            user_id=2,  # john
            account_type="savings",
            balance=25000.00,
            routing_number="021000021",
        ),
        BankAccount(
            account_number="ACC-1003",
            user_id=2,  # john
            account_type="investment",
            balance=100000.00,
            routing_number="021000021",
        ),
    ]
    session.add_all(accounts)
    session.commit()

    patients = [
        Patient(
            patient_id="PT-00001",
            full_name="Alice Anderson",
            ssn="123-45-6789",  # VULNERABLE: real SSN format
            date_of_birth=datetime(1985, 3, 15).date(),
            diagnosis="Type 2 Diabetes",
            prescription="Metformin 500mg twice daily",
            insurance_id="INS-9876543",
            doctor_name="Dr. Sarah Smith",
            last_visit=datetime.utcnow() - timedelta(days=30),
            medical_record_number="MRN-0001",
        ),
        Patient(
            patient_id="PT-00002",
            full_name="Bob Builder",
            ssn="987-65-4321",
            date_of_birth=datetime(1978, 7, 22).date(),
            diagnosis="Hypertension",
            prescription="Lisinopril 10mg daily",
            insurance_id="INS-1234567",
            doctor_name="Dr. Sarah Smith",
            last_visit=datetime.utcnow() - timedelta(days=15),
            medical_record_number="MRN-0002",
        ),
        Patient(
            patient_id="PT-00003",
            full_name="Charlie Chen",
            ssn="555-12-3456",
            date_of_birth=datetime(1992, 11, 8).date(),
            diagnosis="Asthma",
            prescription="Albuterol inhaler as needed",
            insurance_id="INS-5555555",
            doctor_name="Dr. Sarah Smith",
            last_visit=datetime.utcnow() - timedelta(days=5),
            medical_record_number="MRN-0003",
        ),
    ]
    session.add_all(patients)
    session.commit()

    policies = [
        InsurancePolicy(
            policy_number="POL-10001",
            user_id=2,  # john
            policy_type="auto",
            premium=1200.00,
            coverage_amount=50000.00,
            deductible=500.00,
            status="active",
            risk_score=45,
            underwriter="Emily Davis",
            start_date=datetime.utcnow() - timedelta(days=365),
            end_date=datetime.utcnow() + timedelta(days=365),
        ),
        InsurancePolicy(
            policy_number="POL-10002",
            user_id=2,  # john
            policy_type="home",
            premium=2400.00,
            coverage_amount=300000.00,
            deductible=1000.00,
            status="active",
            risk_score=25,
            underwriter="Emily Davis",
            start_date=datetime.utcnow() - timedelta(days=730),
            end_date=datetime.utcnow() + timedelta(days=365),
        ),
        InsurancePolicy(
            policy_number="POL-10003",
            user_id=1,  # admin
            policy_type="life",
            premium=5000.00,
            coverage_amount=1000000.00,
            deductible=0.00,
            status="active",
            risk_score=15,
            underwriter="Emily Davis",
            start_date=datetime.utcnow() - timedelta(days=1095),
            end_date=datetime.utcnow() + timedelta(days=3650),
        ),
    ]
    session.add_all(policies)
    session.commit()

    transactions = [
        Transaction(
            transaction_id="TXN-00001",
            from_account_id=1,
            to_account_id=2,
            amount=5000.00,
            transaction_type="transfer",
            status="completed",
            aml_flag=False,
            timestamp=datetime.utcnow() - timedelta(hours=24),
        ),
        Transaction(
            transaction_id="TXN-00002",
            from_account_id=2,
            to_account_id=999,  # external account
            amount=15000.00,
            transaction_type="wire",
            status="flagged",
            aml_flag=True,
            flagged_reason="Large wire transfer to unknown account",
            timestamp=datetime.utcnow() - timedelta(hours=12),
        ),
        Transaction(
            transaction_id="TXN-00003",
            from_account_id=3,
            to_account_id=1,
            amount=2500.00,
            transaction_type="transfer",
            status="completed",
            aml_flag=False,
            timestamp=datetime.utcnow() - timedelta(hours=6),
        ),
    ]
    session.add_all(transactions)
    session.commit()

    claims = [
        Claim(
            claim_number="CLM-00001",
            policy_id=1,
            claim_amount=3500.00,
            claim_type="accident",
            description="Minor fender bender, front bumper damage",
            status="approved",
            fraud_flag=False,
            fraud_score=15,
            adjuster="Mike Johnson",
            submitted_date=datetime.utcnow() - timedelta(days=45),
            approved_amount=3500.00,
        ),
        Claim(
            claim_number="CLM-00002",
            policy_id=2,
            claim_amount=25000.00,
            claim_type="property_damage",
            description="Water damage from burst pipe",
            status="under_review",
            fraud_flag=True,
            fraud_score=75,
            adjuster="Mike Johnson",
            submitted_date=datetime.utcnow() - timedelta(days=10),
            approved_amount=None,
        ),
        Claim(
            claim_number="CLM-00003",
            policy_id=1,
            claim_amount=1200.00,
            claim_type="theft",
            description="Stolen catalytic converter",
            status="paid",
            fraud_flag=False,
            fraud_score=30,
            adjuster="Mike Johnson",
            submitted_date=datetime.utcnow() - timedelta(days=60),
            approved_amount=1200.00,
        ),
    ]
    session.add_all(claims)
    session.commit()

    print(f"Seeded {len(users)} users")
    print(f"Seeded {len(accounts)} bank accounts")
    print(f"Seeded {len(patients)} patient records")
    print(f"Seeded {len(policies)} insurance policies")
    print(f"Seeded {len(transactions)} transactions")
    print(f"Seeded {len(claims)} claims")
    print("Database seeding complete!")
