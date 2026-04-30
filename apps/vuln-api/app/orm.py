"""
SQLAlchemy 2.0 ORM models for the opt-in SQLite backend.

Lives at ``app.orm`` (not ``app.models``) because ``app/models/`` is a
package owning the in-memory data stores; a sibling ``app/models.py``
would be shadowed by the package and never imported.

These tables back the database_vulnerable blueprint's SQL injection demos.

SECURITY WARNING: These models exist to support INTENTIONALLY VULNERABLE
endpoints. Do not reuse this schema, defaults, or column choices in
production code.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models in the SQLite-backed demos."""


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)  # VULNERABLE: plaintext
    role: Mapped[str] = mapped_column(default="user")
    full_name: Mapped[Optional[str]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)

    accounts: Mapped[list["BankAccount"]] = relationship(
        back_populates="owner", foreign_keys="BankAccount.user_id"
    )
    policies: Mapped[list["InsurancePolicy"]] = relationship(
        back_populates="holder", foreign_keys="InsurancePolicy.user_id"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_number: Mapped[str] = mapped_column(unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    account_type: Mapped[Optional[str]] = mapped_column(default=None)
    balance: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(default="USD")
    status: Mapped[str] = mapped_column(default="active")
    routing_number: Mapped[Optional[str]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="accounts", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "account_number": self.account_number,
            "account_type": self.account_type,
            "balance": self.balance,
            "currency": self.currency,
            "status": self.status,
            "routing_number": self.routing_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Patient(Base):
    """HIPAA-violation demo: stores SSN in plaintext."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(nullable=False)
    ssn: Mapped[str] = mapped_column(nullable=False)  # VULNERABLE: plaintext SSN
    date_of_birth: Mapped[Optional[date]] = mapped_column(default=None)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text, default=None)
    prescription: Mapped[Optional[str]] = mapped_column(Text, default=None)
    insurance_id: Mapped[Optional[str]] = mapped_column(default=None)
    doctor_name: Mapped[Optional[str]] = mapped_column(default=None)
    last_visit: Mapped[Optional[datetime]] = mapped_column(default=None)
    medical_record_number: Mapped[Optional[str]] = mapped_column(default=None)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "full_name": self.full_name,
            "ssn": self.ssn,  # VULNERABLE: exposed in API
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "diagnosis": self.diagnosis,
            "prescription": self.prescription,
            "insurance_id": self.insurance_id,
            "doctor_name": self.doctor_name,
            "last_visit": self.last_visit.isoformat() if self.last_visit else None,
            "medical_record_number": self.medical_record_number,
        }


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_number: Mapped[str] = mapped_column(unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    policy_type: Mapped[Optional[str]] = mapped_column(default=None)
    premium: Mapped[Optional[float]] = mapped_column(default=None)
    coverage_amount: Mapped[Optional[float]] = mapped_column(default=None)
    deductible: Mapped[Optional[float]] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="active")
    risk_score: Mapped[Optional[int]] = mapped_column(default=None)
    underwriter: Mapped[Optional[str]] = mapped_column(default=None)
    start_date: Mapped[Optional[datetime]] = mapped_column(default=None)
    end_date: Mapped[Optional[datetime]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    holder: Mapped["User"] = relationship(back_populates="policies", foreign_keys=[user_id])
    claims: Mapped[list["Claim"]] = relationship(back_populates="policy")

    def to_dict(self):
        return {
            "id": self.id,
            "policy_number": self.policy_number,
            "policy_type": self.policy_type,
            "premium": self.premium,
            "coverage_amount": self.coverage_amount,
            "deductible": self.deductible,
            "status": self.status,
            "risk_score": self.risk_score,
            "underwriter": self.underwriter,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    from_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bank_accounts.id"), default=None
    )
    to_account_id: Mapped[Optional[int]] = mapped_column(default=None)
    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(default="USD")
    transaction_type: Mapped[Optional[str]] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="pending")
    aml_flag: Mapped[bool] = mapped_column(default=False)
    flagged_reason: Mapped[Optional[str]] = mapped_column(Text, default=None)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    from_account: Mapped[Optional["BankAccount"]] = relationship(foreign_keys=[from_account_id])

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "from_account_id": self.from_account_id,
            "to_account_id": self.to_account_id,
            "amount": self.amount,
            "currency": self.currency,
            "transaction_type": self.transaction_type,
            "status": self.status,
            "aml_flag": self.aml_flag,
            "flagged_reason": self.flagged_reason,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_number: Mapped[str] = mapped_column(unique=True, nullable=False)
    policy_id: Mapped[int] = mapped_column(ForeignKey("insurance_policies.id"), nullable=False)
    claim_amount: Mapped[float] = mapped_column(nullable=False)
    claim_type: Mapped[Optional[str]] = mapped_column(default=None)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(default="submitted")
    fraud_flag: Mapped[bool] = mapped_column(default=False)
    fraud_score: Mapped[Optional[int]] = mapped_column(default=None)
    adjuster: Mapped[Optional[str]] = mapped_column(default=None)
    submitted_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    approved_amount: Mapped[Optional[float]] = mapped_column(default=None)

    policy: Mapped["InsurancePolicy"] = relationship(back_populates="claims")

    def to_dict(self):
        return {
            "id": self.id,
            "claim_number": self.claim_number,
            "policy_id": self.policy_id,
            "claim_amount": self.claim_amount,
            "claim_type": self.claim_type,
            "description": self.description,
            "status": self.status,
            "fraud_flag": self.fraud_flag,
            "fraud_score": self.fraud_score,
            "adjuster": self.adjuster,
            "submitted_date": self.submitted_date.isoformat() if self.submitted_date else None,
            "approved_amount": self.approved_amount,
        }
