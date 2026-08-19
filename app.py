import os
from decimal import Decimal
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, g
from config import Config
from models import db, User, Wallet, WalletRequest, FoodItem, FoodTransaction, FoodTransactionItem, WalletTransaction, AuditLog, VendorSetting, TokenBlocklist, ReceiptSequence, IdempotencyRecord, get_ist_now, get_utc_now
from services.auth_service import hash_password, verify_password, generate_jwt_token, customer_required, vendor_required, check_rate_limit, revoke_token, get_auth_token_from_request
from services.wallet_service import create_topup_request, approve_topup_request, reject_topup_request, cancel_topup_request, process_manual_adjustment
from services.billing_service import create_food_transaction, process_food_refund
from services.audit_service import log_audit_event

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_initial_data(app)

    # ----------------------------------------------------
    # Global User-Friendly Error Handlers (No raw stack traces exposed to users)
    # ----------------------------------------------------
    @app.errorhandler(500)
    def handle_500_error(e):
        app.logger.error(f"Internal Server Error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500

    @app.errorhandler(404)
    def handle_404_error(e):
        return jsonify({'error': 'We couldn\'t find the requested resource. Please try again.'}), 404

    @app.errorhandler(400)
    def handle_400_error(e):
        return jsonify({'error': 'Invalid request parameters. Please check your details and try again.'}), 400

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500

    # ----------------------------------------------------
    # Frontend Page Routes (Separate URLs for Customer App, Customer Login, and Vendor Control)
    # ----------------------------------------------------
    @app.route('/')
    def customer_page():
        return render_template('index.html', app_name=app.config['APP_NAME'])

    @app.route('/login')
    def customer_login_page():
        return render_template('login.html', app_name=app.config['APP_NAME'])

    @app.route(f"/{app.config['VENDOR_LOGIN_PATH']}")
    def secret_vendor_page():
        return render_template('vendor.html', app_name=app.config['APP_NAME'], vendor_path=app.config['VENDOR_LOGIN_PATH'])

    # ----------------------------------------------------
    # Customer Authentication & Production Profile APIs
    # ----------------------------------------------------
    @app.route('/api/auth/register', methods=['POST'])
    def customer_register():
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip() or None
        password = data.get('password', '').strip()

        if not name or not phone or not password:
            return jsonify({'error': 'Please enter your full name, phone number, and password'}), 400

        if User.query.filter_by(phone=phone).first():
            return jsonify({'error': 'An account with this phone number or email already exists'}), 400

        if email and User.query.filter_by(email=email).first():
            return jsonify({'error': 'An account with this phone number or email already exists'}), 400

        try:
            user = User(
                name=name,
                phone=phone,
                email=email,
                password_hash=hash_password(password),
                role='customer',
                preferred_language='en',
                created_at=get_ist_now()
            )
            db.session.add(user)
            db.session.flush()

            wallet = Wallet(customer_id=user.id, balance=Decimal('0.00'), updated_at=get_ist_now())
            db.session.add(wallet)
            db.session.commit()

            log_audit_event('customer', user.id, 'REGISTERED', 'User', user.id, {'name': name, 'phone': phone})
            token = generate_jwt_token(user.id, 'customer')

            return jsonify({
                'message': 'Account created successfully',
                'access_token': token,
                'token_type': 'bearer',
                'user': user.to_dict(),
                'wallet_balance': 0.0
            }), 201
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration exception: {e}")
            return jsonify({'error': 'Unable to create account right now. Please try again.'}), 500

    @app.route('/api/auth/login', methods=['POST'])
    def customer_login():
        ip = request.remote_addr or 'unknown'
        if not check_rate_limit(f"cust_login_{ip}", max_requests=5, window_seconds=60):
            return jsonify({'error': 'Too many login attempts. Please wait 1 minute.'}), 429

        data = request.get_json() or {}
        phone_or_email = data.get('contact', '').strip() or data.get('phone', '').strip()
        password = data.get('password', '').strip()

        if not phone_or_email or not password:
            return jsonify({'error': 'Invalid username/phone number or password'}), 400

        user = User.query.filter((User.phone == phone_or_email) | (User.email == phone_or_email)).first()
        if not user or user.role != 'customer' or not verify_password(user.password_hash, password):
            return jsonify({'error': 'Invalid username/phone number or password'}), 401

        token = generate_jwt_token(user.id, 'customer')
        wallet = Wallet.query.filter_by(customer_id=user.id).first()
        balance = float(wallet.balance) if wallet else 0.0

        return jsonify({
            'message': 'Login successful',
            'access_token': token,
            'token_type': 'bearer',
            'user': user.to_dict(),
            'wallet_balance': balance
        }), 200

    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        token = get_auth_token_from_request()
        if token:
            revoke_token(token)
        return jsonify({'message': 'Logged out successfully'}), 200

    @app.route('/api/auth/me', methods=['GET'])
    @customer_required
    def get_customer_profile():
        wallet = Wallet.query.filter_by(customer_id=g.user.id).first()
        orders = FoodTransaction.query.filter_by(customer_id=g.user.id).all()
        
        total_orders = len(orders)
        total_spent = sum(float(o.total_amount) for o in orders if not o.is_refunded)

        return jsonify({
            'user': g.user.to_dict(),
            'wallet_balance': float(wallet.balance) if wallet else 0.0,
            'total_orders': total_orders,
            'total_spent': round(total_spent, 2)
        }), 200

    @app.route('/api/auth/language', methods=['PUT'])
    @customer_required
    def update_language():
        data = request.get_json() or {}
        lang = data.get('language', 'en').lower()
        if lang not in ['en', 'ta']:
            return jsonify({'error': 'Unsupported language. Allowed: en, ta'}), 400
        
        g.user.preferred_language = lang
        db.session.commit()
        return jsonify({'message': 'Language preference updated', 'preferred_language': lang}), 200

    # ----------------------------------------------------
    # Customer Wallet & Top-Up Request APIs
    # ----------------------------------------------------
    @app.route('/api/wallet', methods=['GET'])
    @customer_required
    def get_customer_wallet():
        wallet = Wallet.query.filter_by(customer_id=g.user.id).first()
        if not wallet:
            wallet = Wallet(customer_id=g.user.id, balance=Decimal('0.00'), updated_at=get_ist_now())
            db.session.add(wallet)
            db.session.commit()

        topup_requests = WalletRequest.query.filter_by(customer_id=g.user.id).order_by(WalletRequest.id.desc()).all()

        return jsonify({
            'balance': float(wallet.balance),
            'topup_requests': [r.to_dict() for r in topup_requests]
        }), 200

    @app.route('/api/wallet/topup', methods=['POST'])
    @customer_required
    def request_topup():
        data = request.get_json() or {}
        amount = data.get('amount')
        try:
            req = create_topup_request(g.user.id, amount)
            return jsonify({
                'message': 'Top-up request sent to vendor successfully',
                'request': req.to_dict()
            }), 201
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            app.logger.error(f"Topup exception: {e}")
            return jsonify({'error': 'Unable to submit top-up request right now. Please try again.'}), 500

    @app.route('/api/wallet/topup/<int:req_id>/cancel', methods=['POST'])
    @customer_required
    def cancel_topup(req_id):
        try:
            req = cancel_topup_request(req_id, g.user.id)
            return jsonify({
                'message': 'Top-up request cancelled',
                'request': req.to_dict()
            }), 200
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            app.logger.error(f"Cancel topup exception: {e}")
            return jsonify({'error': 'Unable to cancel request right now. Please try again.'}), 500

    @app.route('/api/wallet/history', methods=['GET'])
    @customer_required
    def get_wallet_history():
        txs = WalletTransaction.query.filter_by(customer_id=g.user.id).order_by(WalletTransaction.id.desc()).all()
        return jsonify([tx.to_dict() for tx in txs]), 200

    # ----------------------------------------------------
    # Customer Food Billing & Receipts APIs
    # ----------------------------------------------------
    @app.route('/api/orders', methods=['POST'])
    @customer_required
    def place_food_order():
        data = request.get_json() or {}
        items = data.get('items', [])
        idempotency_key = request.headers.get('Idempotency-Key') or data.get('idempotency_key')
        
        try:
            res_payload, is_cached = create_food_transaction(g.user.id, items, idempotency_key=idempotency_key)
            if is_cached:
                return jsonify(res_payload), 200
            return jsonify({
                'message': 'Order placed successfully',
                'receipt': res_payload
            }), 201
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            app.logger.error(f"Place food order exception: {e}", exc_info=True)
            return jsonify({'error': 'We couldn\'t complete this request. Please try again.'}), 500

    @app.route('/api/orders', methods=['GET'])
    @customer_required
    def get_customer_orders():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = FoodTransaction.query.filter_by(customer_id=g.user.id).order_by(FoodTransaction.id.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'orders': [o.to_dict() for o in paginated.items],
            'total': paginated.total,
            'page': paginated.page,
            'pages': paginated.pages
        }), 200

    @app.route('/api/orders/<transaction_id>', methods=['GET'])
    @customer_required
    def get_order_receipt(transaction_id):
        order = FoodTransaction.query.filter_by(transaction_id=transaction_id, customer_id=g.user.id).first()
        if not order:
            return jsonify({'error': 'Transaction receipt not found'}), 404
        return jsonify(order.to_dict()), 200

    @app.route('/api/menu', methods=['GET'])
    def get_customer_menu():
        items = FoodItem.query.filter_by(is_active=True).order_by(FoodItem.id.asc()).all()
        return jsonify([i.to_dict() for i in items]), 200

    # ----------------------------------------------------
    # Vendor Control Center APIs
    # ----------------------------------------------------
    @app.route('/api/vendor/login', methods=['POST'])
    def vendor_login():
        ip = request.remote_addr or 'unknown'
        if not check_rate_limit(f"vendor_login_{ip}", max_requests=5, window_seconds=60):
            return jsonify({'error': 'Too many vendor login attempts. Please wait 1 minute.'}), 429

        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'error': 'Invalid username/phone number or password'}), 400

        user = User.query.filter(
            (User.role == 'vendor') & 
            (
                (User.phone == username) | 
                (User.email == username) | 
                (User.name == username) | 
                (username.lower() == 'admin')
            )
        ).first()

        if not user or not verify_password(user.password_hash, password):
            return jsonify({'error': 'Invalid username/phone number or password'}), 401

        token = generate_jwt_token(user.id, 'vendor')
        log_audit_event('vendor', user.id, 'VENDOR_LOGIN', 'User', user.id, {'username': username})

        return jsonify({
            'message': 'Vendor authentication successful',
            'access_token': token,
            'token_type': 'bearer',
            'user': user.to_dict()
        }), 200

    @app.route('/api/vendor/summary', methods=['GET'])
    @vendor_required
    def get_vendor_summary():
        total_customers = User.query.filter_by(role='customer').count()
        pending_requests = WalletRequest.query.filter_by(status='PENDING').count()
        
        today_start = get_ist_now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = FoodTransaction.query.filter(FoodTransaction.created_at >= today_start).all()
        today_sales = sum(float(o.total_amount) for o in today_orders if not o.is_refunded)

        all_orders = FoodTransaction.query.all()
        total_sales = sum(float(o.total_amount) for o in all_orders if not o.is_refunded)
        active_items = FoodItem.query.filter_by(is_active=True).count()

        return jsonify({
            'total_customers': total_customers,
            'pending_requests': pending_requests,
            'today_sales': round(today_sales, 2),
            'total_sales': round(total_sales, 2),
            'active_items': active_items
        }), 200

    @app.route('/api/vendor/wallet-requests', methods=['GET'])
    @vendor_required
    def get_all_wallet_requests():
        reqs = WalletRequest.query.order_by(WalletRequest.id.desc()).all()
        return jsonify([r.to_dict() for r in reqs]), 200

    @app.route('/api/vendor/wallet-requests/<int:req_id>/approve', methods=['POST'])
    @vendor_required
    def approve_request_endpoint(req_id):
        try:
            req = approve_topup_request(req_id, g.user.id)
            return jsonify({
                'message': f"Top-up request of ₹{float(req.amount):.2f} approved successfully",
                'request': req.to_dict()
            }), 200
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            app.logger.error(f"Vendor approve error: {e}")
            return jsonify({'error': 'Unable to approve the request right now. Please try again.'}), 500

    @app.route('/api/vendor/wallet-requests/<int:req_id>/reject', methods=['POST'])
    @vendor_required
    def reject_request_endpoint(req_id):
        data = request.get_json() or {}
        reason = data.get('reason')
        try:
            req = reject_topup_request(req_id, g.user.id, reason=reason)
            return jsonify({
                'message': f"Top-up request of ₹{float(req.amount):.2f} rejected",
                'request': req.to_dict()
            }), 200
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            app.logger.error(f"Vendor reject error: {e}")
            return jsonify({'error': 'Unable to reject the request right now. Please try again.'}), 500

    @app.route('/api/vendor/orders/<transaction_id>/refund', methods=['POST'])
    @vendor_required
    def refund_food_order(transaction_id):
        data = request.get_json() or {}
        reason = data.get('reason', 'Vendor Refund')
        try:
            food_tx = process_food_refund(transaction_id, g.user.id, reason=reason)
            return jsonify({
                'message': f"Order {transaction_id} refunded successfully",
                'transaction': food_tx.to_dict()
            }), 200
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            app.logger.error(f"Vendor refund error: {e}")
            return jsonify({'error': 'Unable to refund order. Please try again.'}), 500

    @app.route('/api/vendor/customers/<int:cust_id>/adjust-balance', methods=['POST'])
    @vendor_required
    def adjust_customer_balance(cust_id):
        data = request.get_json() or {}
        amount = data.get('amount')
        reason = data.get('reason', 'Vendor Adjustment')
        try:
            wallet = process_manual_adjustment(cust_id, amount, g.user.id, reason=reason)
            return jsonify({
                'message': f"Customer balance adjusted successfully",
                'balance': float(wallet.balance)
            }), 200
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            app.logger.error(f"Adjust balance error: {e}")
            return jsonify({'error': 'Unable to adjust customer balance. Please try again.'}), 500

    @app.route('/api/vendor/menu', methods=['GET'])
    @vendor_required
    def get_vendor_menu():
        items = FoodItem.query.order_by(FoodItem.id.asc()).all()
        return jsonify([i.to_dict() for i in items]), 200

    @app.route('/api/vendor/menu', methods=['POST'])
    @vendor_required
    def add_menu_item():
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        price_val = data.get('price')

        if not name:
            return jsonify({'error': 'Item name cannot be empty'}), 400

        try:
            price = Decimal(str(price_val))
            if price <= Decimal('0.00'):
                return jsonify({'error': 'Price must be greater than zero'}), 400
        except Exception:
            return jsonify({'error': 'Invalid price value'}), 400

        existing = FoodItem.query.filter_by(name=name).first()
        if existing:
            return jsonify({'error': f"Food item '{name}' already exists"}), 400

        item = FoodItem(name=name, price=price, is_active=True, created_at=get_ist_now())
        db.session.add(item)
        db.session.commit()

        log_audit_event('vendor', g.user.id, 'ADDED_FOOD_ITEM', 'FoodItem', item.id, {'name': name, 'price': float(price)})
        return jsonify({'message': 'Food item added successfully', 'item': item.to_dict()}), 201

    @app.route('/api/vendor/menu/<int:item_id>', methods=['PUT'])
    @vendor_required
    def update_menu_item(item_id):
        item = db.session.get(FoodItem, item_id)
        if not item:
            return jsonify({'error': 'Food item not found'}), 404

        data = request.get_json() or {}
        if 'name' in data:
            new_name = data['name'].strip()
            if not new_name:
                return jsonify({'error': 'Name cannot be empty'}), 400
            item.name = new_name

        if 'price' in data:
            try:
                p = Decimal(str(data['price']))
                if p <= Decimal('0.00'):
                    return jsonify({'error': 'Price must be greater than zero'}), 400
                item.price = p
            except Exception:
                return jsonify({'error': 'Invalid price value'}), 400

        if 'is_active' in data:
            item.is_active = bool(data['is_active'])

        item.updated_at = get_ist_now()
        db.session.commit()

        log_audit_event('vendor', g.user.id, 'UPDATED_FOOD_ITEM', 'FoodItem', item.id, item.to_dict())
        return jsonify({'message': 'Food item updated successfully', 'item': item.to_dict()}), 200

    @app.route('/api/vendor/menu/<int:item_id>/toggle-active', methods=['POST'])
    @vendor_required
    def toggle_menu_item_active(item_id):
        item = db.session.get(FoodItem, item_id)
        if not item:
            return jsonify({'error': 'Food item not found'}), 404

        item.is_active = not item.is_active
        item.updated_at = get_ist_now()
        db.session.commit()

        action_name = "Activated" if item.is_active else "Deactivated"
        log_audit_event('vendor', g.user.id, 'TOGGLE_FOOD_ITEM_ACTIVE', 'FoodItem', item.id, {'name': item.name, 'is_active': item.is_active})
        return jsonify({'message': f"Food item '{item.name}' {action_name.lower()} successfully", 'item': item.to_dict()}), 200

    @app.route('/api/vendor/customers', methods=['GET'])
    @vendor_required
    def get_vendor_customers():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        query = User.query.filter_by(role='customer').order_by(User.id.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        threshold = get_low_balance_threshold()

        for c in paginated.items:
            w = Wallet.query.filter_by(customer_id=c.id).first()
            bal = float(w.balance) if w else 0.0
            tx_count = FoodTransaction.query.filter_by(customer_id=c.id).count()

            # Retrieve active food items ordered by customer
            orders = FoodTransaction.query.filter_by(customer_id=c.id, is_refunded=False).all()
            ordered_food_ids = set()
            for o in orders:
                for item in o.items:
                    ordered_food_ids.add(item.food_item_id)

            active_items_ordered = FoodItem.query.filter(FoodItem.id.in_(list(ordered_food_ids)), FoodItem.is_active == True).all() if ordered_food_ids else []
            active_items_str = ", ".join([item.name for item in active_items_ordered]) if active_items_ordered else "-"

            result.append({
                'user': c.to_dict(),
                'balance': bal,
                'is_low_balance': bal < float(threshold),
                'total_orders': tx_count,
                'active_food_items': active_items_str
            })

        return jsonify({
            'customers': result,
            'total': paginated.total,
            'page': paginated.page,
            'pages': paginated.pages
        }), 200

    @app.route('/api/vendor/audit-logs', methods=['GET'])
    @vendor_required
    def get_audit_logs():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        query = AuditLog.query.order_by(AuditLog.id.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'logs': [l.to_dict() for l in paginated.items],
            'total': paginated.total,
            'page': paginated.page,
            'pages': paginated.pages
        }), 200

    @app.route('/api/vendor/settings', methods=['GET'])
    @vendor_required
    def get_vendor_settings():
        threshold = get_low_balance_threshold()
        return jsonify({'low_balance_threshold': float(threshold)}), 200

    @app.route('/api/vendor/settings', methods=['POST'])
    @vendor_required
    def update_vendor_settings():
        data = request.get_json() or {}
        threshold_val = data.get('low_balance_threshold')
        try:
            val = Decimal(str(threshold_val))
            if val < Decimal('0.00'):
                return jsonify({'error': 'Threshold cannot be negative'}), 400
        except Exception:
            return jsonify({'error': 'Invalid threshold value'}), 400

        setting = VendorSetting.query.filter_by(key='low_balance_threshold').first()
        if not setting:
            setting = VendorSetting(key='low_balance_threshold', value=str(val))
            db.session.add(setting)
        else:
            setting.value = str(val)
        
        db.session.commit()
        log_audit_event('vendor', g.user.id, 'UPDATED_SETTING', 'VendorSetting', setting.id, {'threshold': float(val)})
        return jsonify({'message': 'Settings updated successfully', 'low_balance_threshold': float(val)}), 200

    return app

def get_low_balance_threshold():
    setting = VendorSetting.query.filter_by(key='low_balance_threshold').first()
    if setting:
        try:
            return Decimal(setting.value)
        except Exception:
            pass
    return Decimal('50.00')

def seed_initial_data(app):
    with app.app_context():
        vendor_user = User.query.filter(
            (User.role == 'vendor') | (User.phone == '9999999999') | (User.email == 'vendor@foodwallet.local')
        ).first()
        
        if not vendor_user:
            v_user = User(
                name="admin",
                phone="9999999999",
                email="vendor@foodwallet.local",
                password_hash=hash_password(app.config['VENDOR_PASSWORD']),
                role='vendor',
                preferred_language='en',
                created_at=get_ist_now()
            )
            db.session.add(v_user)
            db.session.commit()

        if FoodItem.query.count() == 0:
            sample_menu = [
                ('Parotta', Decimal('15.00')),
                ('Dosa', Decimal('30.00')),
                ('Idli', Decimal('10.00')),
                ('Meals', Decimal('80.00')),
                ('Tea', Decimal('10.00'))
            ]
            for name, price in sample_menu:
                item = FoodItem(name=name, price=price, is_active=True, created_at=get_ist_now())
                db.session.add(item)
            db.session.commit()

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
