from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from models import db, Wallet, WalletRequest, WalletTransaction, get_ist_now
from services.audit_service import log_audit_event

MIN_TOPUP_AMOUNT = Decimal('10.00')
MAX_TOPUP_AMOUNT = Decimal('10000.00')

def quantize_money(val):
    return Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def create_topup_request(customer_id, amount_val):
    """
    Creates a new PENDING top-up request.
    Stores the exact server-side IST timestamp at the moment of creation.
    """
    try:
        amount = quantize_money(amount_val)
    except Exception:
        raise ValueError("Invalid monetary amount")
        
    if amount < MIN_TOPUP_AMOUNT or amount > MAX_TOPUP_AMOUNT:
        raise ValueError(f"Top-up amount must be between ₹{MIN_TOPUP_AMOUNT:.2f} and ₹{MAX_TOPUP_AMOUNT:.2f}")

    # Check for existing PENDING request to prevent duplicate requests
    existing = WalletRequest.query.filter_by(customer_id=customer_id, status='PENDING').first()
    if existing:
        raise ValueError("You already have a pending top-up request. Please wait for vendor approval or cancel the existing request.")

    req = WalletRequest(
        customer_id=customer_id,
        amount=amount,
        status='PENDING',
        created_at=get_ist_now()
    )
    db.session.add(req)
    db.session.commit()

    log_audit_event(
        actor_type='customer',
        actor_id=customer_id,
        action='REQUESTED_TOPUP',
        entity='WalletRequest',
        entity_id=req.id,
        details={'amount': float(amount)}
    )

    return req

def cancel_topup_request(request_id, customer_id):
    """
    Allows a customer to cancel their own PENDING top-up request.
    """
    req = db.session.get(WalletRequest, request_id)
    if not req or req.customer_id != customer_id:
        raise ValueError("Wallet request not found")

    if req.status != 'PENDING':
        raise ValueError("This request has already been processed.")

    req.status = 'CANCELLED'
    req.updated_at = get_ist_now()
    db.session.commit()

    log_audit_event(
        actor_type='customer',
        actor_id=customer_id,
        action='CANCELLED_TOPUP',
        entity='WalletRequest',
        entity_id=req.id,
        details={'amount': float(req.amount)}
    )
    return req

def approve_topup_request(request_id, vendor_id):
    """
    Approves a top-up request, adding funds to the customer's wallet balance.
    Stores the exact server-side IST approved timestamp.
    """
    req = db.session.get(WalletRequest, request_id)
    if not req:
        raise ValueError("This request could not be found.")
    
    if req.status != 'PENDING':
        raise ValueError("This request has already been processed.")

    wallet = Wallet.query.filter_by(customer_id=req.customer_id).first()
    if not wallet:
        wallet = Wallet(customer_id=req.customer_id, balance=Decimal('0.00'))
        db.session.add(wallet)

    balance_before = quantize_money(wallet.balance)
    req_amount = quantize_money(req.amount)
    balance_after = balance_before + req_amount
    wallet.balance = balance_after

    req.status = 'APPROVED'
    req.approved_by = vendor_id
    req.approved_at = get_ist_now()

    # Log financial ledger transaction with exact real timestamp
    w_tx = WalletTransaction(
        customer_id=req.customer_id,
        type='TOPUP',
        amount=req_amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference_id=f"TOPUP-{req.id}",
        description=f"Approved Prepaid Top-Up of ₹{req_amount:.2f}",
        created_at=get_ist_now()
    )
    db.session.add(w_tx)
    db.session.commit()

    log_audit_event(
        actor_type='vendor',
        actor_id=vendor_id,
        action='APPROVED_TOPUP',
        entity='WalletRequest',
        entity_id=req.id,
        details={
            'amount': float(req_amount),
            'customer_id': req.customer_id,
            'balance_before': float(balance_before),
            'balance_after': float(balance_after)
        }
    )

    return req

def reject_topup_request(request_id, vendor_id, reason=None):
    """
    Rejects a pending top-up request.
    """
    req = db.session.get(WalletRequest, request_id)
    if not req:
        raise ValueError("This request could not be found.")

    if req.status != 'PENDING':
        raise ValueError("This request has already been processed.")

    req.status = 'REJECTED'
    req.rejected_by = vendor_id
    req.rejected_at = get_ist_now()
    req.rejection_reason = (reason or "Rejected by vendor").strip()
    db.session.commit()

    log_audit_event(
        actor_type='vendor',
        actor_id=vendor_id,
        action='REJECTED_TOPUP',
        entity='WalletRequest',
        entity_id=req.id,
        details={
            'amount': float(req.amount),
            'customer_id': req.customer_id,
            'reason': req.rejection_reason
        }
    )

    return req

def process_manual_adjustment(customer_id, amount_val, vendor_id, reason="Vendor Adjustment"):
    """
    Allows vendor to manually adjust customer wallet balance with real IST timestamp.
    """
    try:
        adj_amount = quantize_money(amount_val)
    except Exception:
        raise ValueError("Invalid monetary adjustment amount")

    wallet = Wallet.query.filter_by(customer_id=customer_id).first()
    if not wallet:
        wallet = Wallet(customer_id=customer_id, balance=Decimal('0.00'))
        db.session.add(wallet)

    balance_before = quantize_money(wallet.balance)
    balance_after = balance_before + adj_amount
    if balance_after < Decimal('0.00'):
        raise ValueError(f"Manual adjustment would result in negative balance (₹{balance_after:.2f})")

    wallet.balance = balance_after

    w_tx = WalletTransaction(
        customer_id=customer_id,
        type='MANUAL_ADJUSTMENT',
        amount=adj_amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference_id=f"MANUAL-{customer_id}",
        description=reason,
        created_at=get_ist_now()
    )
    db.session.add(w_tx)
    db.session.commit()

    log_audit_event(
        actor_type='vendor',
        actor_id=vendor_id,
        action='MANUAL_BALANCE_ADJUSTMENT',
        entity='Wallet',
        entity_id=wallet.id,
        details={
            'customer_id': customer_id,
            'adjustment_amount': float(adj_amount),
            'balance_before': float(balance_before),
            'balance_after': float(balance_after),
            'reason': reason
        }
    )

    return wallet
