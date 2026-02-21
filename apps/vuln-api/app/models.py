"""
Database models for api-demo (opt-in SQLite backend).

SECURITY WARNING: These models are INTENTIONALLY VULNERABLE for WAF testing.
DO NOT use in production environments.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """
    User accounts for authentication demos.
    Intentionally stores plaintext passwords for auth bypass demonstrations.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # VULNERABLE: Plaintext password
    role = db.Column(db.String(50), default='user')  # user, admin, doctor, agent, underwriter
    full_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    accounts = db.relationship('BankAccount', backref='owner', lazy='dynamic')
    policies = db.relationship('InsurancePolicy', backref='holder', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class BankAccount(db.Model):
    """
    Banking accounts for financial services demos.
    """
    __tablename__ = 'bank_accounts'

    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_type = db.Column(db.String(50))  # checking, savings, investment
    balance = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), default='active')  # active, frozen, closed
    routing_number = db.Column(db.String(9))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'account_number': self.account_number,
            'account_type': self.account_type,
            'balance': self.balance,
            'currency': self.currency,
            'status': self.status,
            'routing_number': self.routing_number,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Patient(db.Model):
    """
    Healthcare patient records for HIPAA violation demos.
    VULNERABLE: Stores SSN in plaintext.
    """
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    ssn = db.Column(db.String(11), nullable=False)  # VULNERABLE: Plaintext SSN
    date_of_birth = db.Column(db.Date)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    insurance_id = db.Column(db.String(50))
    doctor_name = db.Column(db.String(200))
    last_visit = db.Column(db.DateTime)
    medical_record_number = db.Column(db.String(20))

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'full_name': self.full_name,
            'ssn': self.ssn,  # VULNERABLE: Exposed in API
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'diagnosis': self.diagnosis,
            'prescription': self.prescription,
            'insurance_id': self.insurance_id,
            'doctor_name': self.doctor_name,
            'last_visit': self.last_visit.isoformat() if self.last_visit else None,
            'medical_record_number': self.medical_record_number
        }


class InsurancePolicy(db.Model):
    """
    Insurance policies for underwriting and claims demos.
    """
    __tablename__ = 'insurance_policies'

    id = db.Column(db.Integer, primary_key=True)
    policy_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    policy_type = db.Column(db.String(50))  # life, health, auto, home
    premium = db.Column(db.Float)
    coverage_amount = db.Column(db.Float)
    deductible = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active, lapsed, cancelled, claimed
    risk_score = db.Column(db.Integer)  # 1-100 (higher = riskier)
    underwriter = db.Column(db.String(200))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'policy_number': self.policy_number,
            'policy_type': self.policy_type,
            'premium': self.premium,
            'coverage_amount': self.coverage_amount,
            'deductible': self.deductible,
            'status': self.status,
            'risk_score': self.risk_score,
            'underwriter': self.underwriter,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Transaction(db.Model):
    """
    Financial transactions for AML/fraud detection demos.
    """
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    from_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'))
    to_account_id = db.Column(db.Integer)  # Can be external
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    transaction_type = db.Column(db.String(50))  # transfer, withdrawal, deposit, wire
    status = db.Column(db.String(20), default='pending')  # pending, completed, flagged, rejected
    aml_flag = db.Column(db.Boolean, default=False)
    flagged_reason = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    from_account = db.relationship('BankAccount', foreign_keys=[from_account_id])

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'from_account_id': self.from_account_id,
            'to_account_id': self.to_account_id,
            'amount': self.amount,
            'currency': self.currency,
            'transaction_type': self.transaction_type,
            'status': self.status,
            'aml_flag': self.aml_flag,
            'flagged_reason': self.flagged_reason,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Claim(db.Model):
    """
    Insurance claims for fraud detection demos.
    """
    __tablename__ = 'claims'

    id = db.Column(db.Integer, primary_key=True)
    claim_number = db.Column(db.String(20), unique=True, nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('insurance_policies.id'), nullable=False)
    claim_amount = db.Column(db.Float, nullable=False)
    claim_type = db.Column(db.String(50))  # accident, theft, medical, property_damage
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='submitted')  # submitted, under_review, approved, denied, paid
    fraud_flag = db.Column(db.Boolean, default=False)
    fraud_score = db.Column(db.Integer)  # 0-100
    adjuster = db.Column(db.String(200))
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow)
    approved_amount = db.Column(db.Float)

    policy = db.relationship('InsurancePolicy', backref='claims')

    def to_dict(self):
        return {
            'id': self.id,
            'claim_number': self.claim_number,
            'policy_id': self.policy_id,
            'claim_amount': self.claim_amount,
            'claim_type': self.claim_type,
            'description': self.description,
            'status': self.status,
            'fraud_flag': self.fraud_flag,
            'fraud_score': self.fraud_score,
            'adjuster': self.adjuster,
            'submitted_date': self.submitted_date.isoformat() if self.submitted_date else None,
            'approved_amount': self.approved_amount
        }
