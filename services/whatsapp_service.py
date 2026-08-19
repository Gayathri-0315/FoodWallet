import requests
from decimal import Decimal
from flask import current_app
from models import db, WhatsAppLog, VendorSetting, Wallet

def get_low_balance_threshold():
    setting = VendorSetting.query.filter_by(key='low_balance_threshold').first()
    if setting:
        try:
            return Decimal(setting.value)
        except Exception:
            pass
    return current_app.config.get('DEFAULT_LOW_BALANCE_THRESHOLD', Decimal('50.00'))

def check_and_trigger_low_balance_alert(customer, current_balance):
    """
    Checks if balance is below threshold and sends WhatsApp notification if not previously alerted.
    Resets alerted flag when balance rises above threshold.
    """
    threshold = get_low_balance_threshold()
    wallet = Wallet.query.filter_by(customer_id=customer.id).first()
    
    if not wallet:
        return
    
    # If balance rises above threshold, reset alert state
    if current_balance > threshold:
        if wallet.has_low_balance_alerted:
            wallet.has_low_balance_alerted = False
            db.session.commit()
        return

    # If balance is at/below threshold and has not been alerted yet
    if current_balance <= threshold and not wallet.has_low_balance_alerted:
        send_whatsapp_low_balance_notification(customer, current_balance, threshold)
        wallet.has_low_balance_alerted = True
        db.session.commit()

def send_whatsapp_low_balance_notification(customer, balance, threshold):
    """
    Dispatches WhatsApp notification. Isolated from database transaction logic.
    """
    message_text = f"Dear {customer.name}, your FOODWALLET balance is low (₹{balance:.2f}). Threshold is ₹{threshold:.2f}. Please top up your prepaid wallet."
    phone = customer.phone.replace("+", "").replace("-", "").strip()
    
    api_token = current_app.config.get('WHATSAPP_API_TOKEN', '')
    phone_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID', '')
    whatsapp_enabled = current_app.config.get('WHATSAPP_ENABLED', False)

    status = 'SIMULATED'
    response_info = f"Alert simulated. Message: {message_text}"

    if whatsapp_enabled and api_token and phone_id and api_token != 'mock_whatsapp_token':
        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message_text}
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=5)
            if resp.status_code == 200:
                status = 'SENT'
                response_info = resp.text
            else:
                status = 'FAILED'
                response_info = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            status = 'FAILED'
            response_info = f"Network exception: {str(e)}"

    try:
        log_entry = WhatsAppLog(
            customer_id=customer.id,
            phone_number=customer.phone,
            balance=balance,
            threshold=threshold,
            status=status,
            response_details=response_info
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        print(f"Error writing WhatsApp log: {ex}")

    return {
        'status': status,
        'message': message_text,
        'wa_link': f"https://api.whatsapp.com/send?phone={phone}&text={requests.utils.quote(message_text)}"
    }
