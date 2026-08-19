import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from models import db, User, Wallet, FoodItem, FoodTransaction, FoodTransactionItem, WalletTransaction, ReceiptSequence, IdempotencyRecord, get_ist_now, get_utc_now
from services.audit_service import log_audit_event

def quantize_money(val):
    return Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def generate_unique_transaction_id():
    """
    Generates a unique transaction ID formatted as FW-YYYYMMDD-XXXXXX
    resetting daily based on IST timezone (Asia/Kolkata).
    """
    ist_today_str = get_ist_now().strftime("%Y%m%d")
    
    seq_record = ReceiptSequence.query.filter_by(date_str=ist_today_str).first()
    if not seq_record:
        seq_record = ReceiptSequence(date_str=ist_today_str, last_seq=1)
        db.session.add(seq_record)
        next_seq = 1
    else:
        seq_record.last_seq += 1
        next_seq = seq_record.last_seq

    db.session.commit()
    return f"FW-{ist_today_str}-{next_seq:06d}"

def check_idempotency(user_id, idempotency_key, path):
    if not idempotency_key:
        return None
    try:
        record = IdempotencyRecord.query.filter_by(idempotency_key=idempotency_key).first()
        if record:
            return json.loads(record.response_body), record.status_code
    except Exception as e:
        print("Idempotency check warning:", e)
    return None

def save_idempotency_record(user_id, idempotency_key, path, response_data, status_code):
    if not idempotency_key:
        return
    try:
        rec = IdempotencyRecord(
            user_id=user_id,
            idempotency_key=idempotency_key,
            request_path=path,
            response_body=json.dumps(response_data),
            status_code=status_code,
            created_at=get_ist_now()
        )
        db.session.add(rec)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Save idempotency record warning:", e)

def create_food_transaction(customer_id, items_payload, idempotency_key=None):
    """
    Executes a food order billing operation with idempotency protection.
    Returns (result_dict, is_cached).
    """
    if idempotency_key:
        cached = check_idempotency(customer_id, idempotency_key, '/api/orders')
        if cached:
            return cached[0], True

    if not items_payload or not isinstance(items_payload, list):
        raise ValueError("Please select at least one food item")

    wallet = Wallet.query.filter_by(customer_id=customer_id).first()
    if not wallet:
        raise ValueError("Customer wallet not found")

    balance_before = quantize_money(wallet.balance)
    total_amount = Decimal('0.00')
    line_items_to_create = []

    for item_data in items_payload:
        food_id = item_data.get('food_id')
        qty = item_data.get('quantity', 0)

        if not food_id or qty <= 0:
            continue

        food_item = db.session.get(FoodItem, food_id)
        if not food_item or not food_item.is_active:
            raise ValueError(f"Food item {food_id} is no longer available")

        unit_price = quantize_money(food_item.price)
        subtotal = quantize_money(unit_price * Decimal(str(qty)))
        total_amount += subtotal

        line_items_to_create.append({
            'food_id': food_item.id,
            'food_name': food_item.name,
            'unit_price': unit_price,
            'quantity': qty,
            'subtotal': subtotal
        })

    if total_amount <= Decimal('0.00'):
        raise ValueError("Please select at least one food item")

    if balance_before < total_amount:
        raise ValueError(f"Insufficient balance (₹{balance_before:.2f}). Total bill is ₹{total_amount:.2f}")

    balance_after = balance_before - total_amount
    wallet.balance = balance_after

    tx_id = generate_unique_transaction_id()
    now_ist = get_ist_now()

    food_tx = FoodTransaction(
        transaction_id=tx_id,
        customer_id=customer_id,
        total_amount=total_amount,
        balance_before=balance_before,
        balance_after=balance_after,
        created_at=now_ist
    )
    db.session.add(food_tx)
    db.session.flush()

    for item_dict in line_items_to_create:
        tx_item = FoodTransactionItem(
            transaction_id=food_tx.id,
            food_item_id=item_dict['food_id'],
            food_name_snapshot=item_dict['food_name'],
            unit_price=item_dict['unit_price'],
            quantity=item_dict['quantity'],
            subtotal=item_dict['subtotal']
        )
        db.session.add(tx_item)

    w_tx = WalletTransaction(
        customer_id=customer_id,
        type='PURCHASE',
        amount=total_amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference_id=tx_id,
        description=f"Food Order {tx_id}",
        created_at=now_ist
    )
    db.session.add(w_tx)
    db.session.commit()

    log_audit_event(
        actor_type='customer',
        actor_id=customer_id,
        action='FOOD_PURCHASE',
        entity='FoodTransaction',
        entity_id=tx_id,
        details={
            'total_amount': float(total_amount),
            'balance_before': float(balance_before),
            'balance_after': float(balance_after),
            'item_count': len(line_items_to_create)
        }
    )

    result_dict = food_tx.to_dict()

    if idempotency_key:
        save_idempotency_record(customer_id, idempotency_key, '/api/orders', result_dict, 200)

    return result_dict, False

def process_food_refund(transaction_id, vendor_id, reason="Vendor Refund"):
    """
    Refunds a food order back to the customer wallet with real IST timestamp.
    """
    food_tx = FoodTransaction.query.filter_by(transaction_id=transaction_id).first()
    if not food_tx:
        raise ValueError("Food transaction not found")

    if food_tx.is_refunded:
        raise ValueError("This transaction has already been refunded")

    wallet = Wallet.query.filter_by(customer_id=food_tx.customer_id).first()
    if not wallet:
        raise ValueError("Customer wallet not found")

    balance_before = quantize_money(wallet.balance)
    refund_amount = quantize_money(food_tx.total_amount)
    balance_after = balance_before + refund_amount

    wallet.balance = balance_after
    food_tx.is_refunded = True

    w_tx = WalletTransaction(
        customer_id=food_tx.customer_id,
        type='REFUND',
        amount=refund_amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference_id=f"REFUND-{transaction_id}",
        description=f"Refund for Order {transaction_id}: {reason}",
        created_at=get_ist_now()
    )
    db.session.add(w_tx)
    db.session.commit()

    log_audit_event(
        actor_type='vendor',
        actor_id=vendor_id,
        action='FOOD_REFUND',
        entity='FoodTransaction',
        entity_id=transaction_id,
        details={
            'customer_id': food_tx.customer_id,
            'refund_amount': float(refund_amount),
            'balance_after': float(balance_after),
            'reason': reason
        }
    )

    return food_tx
