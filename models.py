from datetime import datetime, timezone, timedelta
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

# Indian Standard Time (IST UTC+5:30)
IST_TZ = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    return datetime.now(IST_TZ)

# Alias for backward compatibility
get_utc_now = get_ist_now

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer') # 'customer' or 'vendor'
    preferred_language = db.Column(db.String(10), nullable=False, default='en') # 'en' or 'ta'
    created_at = db.Column(db.DateTime(timezone=True), default=get_ist_now)

    wallet = db.relationship('Wallet', backref='customer', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'role': self.role,
            'preferred_language': self.preferred_language,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal('0.00'))
    updated_at = db.Column(db.DateTime(timezone=True), default=get_ist_now, onupdate=get_ist_now)

    __table_args__ = (
        CheckConstraint('balance >= 0.00', name='ck_wallet_balance_non_negative'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'balance': float(self.balance),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WalletRequest(db.Model):
    __tablename__ = 'wallet_requests'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='PENDING', index=True) # PENDING, APPROVED, REJECTED, CANCELLED
    rejection_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_ist_now)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejected_at = db.Column(db.DateTime(timezone=True), nullable=True)
    rejected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_ist_now, onupdate=get_ist_now)

    customer_rel = db.relationship('User', foreign_keys=[customer_id])

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer_rel.name if self.customer_rel else f"Customer #{self.customer_id}",
            'customer_phone': self.customer_rel.phone if self.customer_rel else "",
            'amount': float(self.amount),
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by': self.approved_by,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'rejected_by': self.rejected_by
        }

class FoodItem(db.Model):
    __tablename__ = 'food_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_ist_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_ist_now, onupdate=get_ist_now)

    __table_args__ = (
        CheckConstraint('price > 0.00', name='ck_food_item_price_positive'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': float(self.price),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FoodTransaction(db.Model):
    __tablename__ = 'food_transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_before = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    is_refunded = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_ist_now)

    customer_rel = db.relationship('User', foreign_keys=[customer_id])
    items = db.relationship('FoodTransactionItem', backref='transaction', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer_rel.name if self.customer_rel else f"Customer #{self.customer_id}",
            'total_amount': float(self.total_amount),
            'balance_before': float(self.balance_before),
            'balance_after': float(self.balance_after),
            'is_refunded': self.is_refunded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }

class FoodTransactionItem(db.Model):
    __tablename__ = 'food_transaction_items'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('food_transactions.id', ondelete='CASCADE'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    food_name_snapshot = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'food_id': self.food_item_id,
            'food_name': self.food_name_snapshot,
            'unit_price': float(self.unit_price),
            'quantity': self.quantity,
            'subtotal': float(self.subtotal)
        }

class WalletTransaction(db.Model):
    __tablename__ = 'wallet_transactions'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False) # 'TOPUP', 'PURCHASE', 'REFUND', 'MANUAL_ADJUSTMENT'
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_before = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    reference_id = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_ist_now)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'type': self.type,
            'amount': float(self.amount),
            'balance_before': float(self.balance_before),
            'balance_after': float(self.balance_after),
            'reference_id': self.reference_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    actor_type = db.Column(db.String(20), nullable=False) # 'customer' or 'vendor'
    actor_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(50), nullable=False)
    entity = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=get_ist_now)

    def to_dict(self):
        return {
            'id': self.id,
            'actor_type': self.actor_type,
            'actor_id': self.actor_id,
            'action': self.action,
            'entity': self.entity,
            'entity_id': self.entity_id,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class VendorSetting(db.Model):
    __tablename__ = 'vendor_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value
        }

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_ist_now)

    def to_dict(self):
        return {
            'id': self.id,
            'jti': self.jti,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ReceiptSequence(db.Model):
    __tablename__ = 'receipt_sequences'

    id = db.Column(db.Integer, primary_key=True)
    date_str = db.Column(db.String(8), unique=True, nullable=False) # e.g. '20260819'
    last_seq = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'date_str': self.date_str,
            'last_seq': self.last_seq
        }

class IdempotencyRecord(db.Model):
    __tablename__ = 'idempotency_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    idempotency_key = db.Column(db.String(100), nullable=False, index=True)
    request_path = db.Column(db.String(100), nullable=True)
    response_body = db.Column(db.Text, nullable=False)
    status_code = db.Column(db.Integer, nullable=False, default=200)
    created_at = db.Column(db.DateTime(timezone=True), default=get_ist_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'idempotency_key': self.idempotency_key,
            'request_path': self.request_path,
            'response_body': self.response_body,
            'status_code': self.status_code,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


        class PasswordResetOTP(db.Model):
            __tablename__ = 'password_reset_otps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    otp_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_ist_now)

    user = db.relationship('User', foreign_keys=[user_id])
