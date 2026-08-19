import unittest
from decimal import Decimal
from app import create_app
from models import db, User, Wallet, WalletRequest, FoodItem, FoodTransaction, WalletTransaction, AuditLog

class FoodWalletTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            from app import seed_initial_data
            seed_initial_data(self.app)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_customer_registration_and_login(self):
        res = self.client.post('/api/auth/register', json={
            'name': 'Gayathri',
            'phone': '9876543210',
            'email': 'gaya@example.com',
            'password': 'password123'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn('access_token', data)
        self.assertEqual(data['user']['name'], 'Gayathri')
        self.assertEqual(data['wallet_balance'], 0.0)

        # Duplicate register attempt -> 400 error
        dup_res = self.client.post('/api/auth/register', json={
            'name': 'Gayathri Duplicate',
            'phone': '9876543210',
            'password': 'password123'
        })
        self.assertEqual(dup_res.status_code, 400)
        self.assertIn('already exists', dup_res.get_json()['error'])

        # Valid Login
        res_login = self.client.post('/api/auth/login', json={
            'contact': '9876543210',
            'password': 'password123'
        })
        self.assertEqual(res_login.status_code, 200)
        login_data = res_login.get_json()
        self.assertIn('access_token', login_data)

        # Invalid Password Login
        bad_login = self.client.post('/api/auth/login', json={
            'contact': '9876543210',
            'password': 'wrongpassword'
        })
        self.assertEqual(bad_login.status_code, 401)
        self.assertIn('Invalid username/phone number or password', bad_login.get_json()['error'])

    def test_production_customer_profile(self):
        res = self.client.post('/api/auth/register', json={
            'name': 'Priya Profile Test',
            'phone': '9777777777',
            'email': 'priya@example.com',
            'password': 'password123'
        })
        token = res.get_json()['access_token']

        prof_res = self.client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(prof_res.status_code, 200)
        data = prof_res.get_json()
        self.assertEqual(data['user']['name'], 'Priya Profile Test')
        self.assertEqual(data['user']['email'], 'priya@example.com')
        self.assertEqual(data['total_orders'], 0)
        self.assertEqual(data['total_spent'], 0.0)

    def test_role_based_authorization_403(self):
        res = self.client.post('/api/auth/register', json={
            'name': 'Customer Test',
            'phone': '9111111111',
            'password': 'password123'
        })
        cust_token = res.get_json()['access_token']

        v_res = self.client.get('/api/vendor/summary', headers={
            'Authorization': f'Bearer {cust_token}'
        })
        self.assertEqual(v_res.status_code, 403)

    def test_single_pending_topup_and_customer_cancellation(self):
        res = self.client.post('/api/auth/register', json={
            'name': 'Ramesh',
            'phone': '9222222222',
            'password': 'password123'
        })
        token = res.get_json()['access_token']

        # Request ₹500
        req1 = self.client.post('/api/wallet/topup', json={'amount': 500}, headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(req1.status_code, 201)
        req_id = req1.get_json()['request']['id']

        # Second request while pending -> fails with 400
        req2 = self.client.post('/api/wallet/topup', json={'amount': 300}, headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(req2.status_code, 400)

        # Customer cancels pending request
        cancel_res = self.client.post(f'/api/wallet/topup/{req_id}/cancel', json={}, headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(cancel_res.status_code, 200)
        self.assertEqual(cancel_res.get_json()['request']['status'], 'CANCELLED')

    def test_atomic_topup_approval_and_rejection(self):
        res = self.client.post('/api/auth/register', json={
            'name': 'Priya',
            'phone': '9333333333',
            'password': 'password123'
        })
        token = res.get_json()['access_token']

        req_res = self.client.post('/api/wallet/topup', json={'amount': 500}, headers={'Authorization': f'Bearer {token}'})
        req_id = req_res.get_json()['request']['id']

        v_login = self.client.post('/api/vendor/login', json={'username': 'admin', 'password': 'vendor123'})
        v_token = v_login.get_json()['access_token']

        app_res = self.client.post(f'/api/vendor/wallet-requests/{req_id}/approve', json={}, headers={'Authorization': f'Bearer {v_token}'})
        self.assertEqual(app_res.status_code, 200)

        w_res = self.client.get('/api/wallet', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(w_res.get_json()['balance'], 500.0)

    def test_food_order_billing_idempotency_and_refund(self):
        res = self.client.post('/api/auth/register', json={
            'name': 'Karthik',
            'phone': '9444444444',
            'password': 'password123'
        })
        token = res.get_json()['access_token']
        req_res = self.client.post('/api/wallet/topup', json={'amount': 100}, headers={'Authorization': f'Bearer {token}'})
        req_id = req_res.get_json()['request']['id']

        v_login = self.client.post('/api/vendor/login', json={'username': 'admin', 'password': 'vendor123'})
        v_token = v_login.get_json()['access_token']
        self.client.post(f'/api/vendor/wallet-requests/{req_id}/approve', json={}, headers={'Authorization': f'Bearer {v_token}'})

        menu = self.client.get('/api/menu').get_json()
        parotta = next(i for i in menu if i['name'] == 'Parotta') # ₹15

        # Order with Idempotency Key
        idemp_key = "idemp-test-key-100"
        order1 = self.client.post('/api/orders', json={
            'items': [{'food_id': parotta['id'], 'quantity': 2}] # ₹30
        }, headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': idemp_key})
        self.assertEqual(order1.status_code, 201)
        tx_id = order1.get_json()['receipt']['transaction_id']

        # Duplicate order request with same Idempotency Key -> returns cached response with 200
        order2 = self.client.post('/api/orders', json={
            'items': [{'food_id': parotta['id'], 'quantity': 2}]
        }, headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': idemp_key})
        self.assertEqual(order2.status_code, 200)

        # Balance after ₹30 deduction should be ₹70
        w_res = self.client.get('/api/wallet', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(w_res.get_json()['balance'], 70.0)

        # Vendor Refunds Order (₹30)
        ref_res = self.client.post(f'/api/vendor/orders/{tx_id}/refund', json={}, headers={'Authorization': f'Bearer {v_token}'})
        self.assertEqual(ref_res.status_code, 200)

        # Balance restored to ₹100
        w_res2 = self.client.get('/api/wallet', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(w_res2.get_json()['balance'], 100.0)

    def test_vendor_toggle_active_food_item(self):
        v_login = self.client.post('/api/vendor/login', json={'username': 'admin', 'password': 'vendor123'})
        v_token = v_login.get_json()['access_token']

        menu_res = self.client.get('/api/vendor/menu', headers={'Authorization': f'Bearer {v_token}'})
        tea_item = next(i for i in menu_res.get_json() if i['name'] == 'Tea')

        # Toggle Active (Deactivate)
        tog1 = self.client.post(f'/api/vendor/menu/{tea_item["id"]}/toggle-active', json={}, headers={'Authorization': f'Bearer {v_token}'})
        self.assertEqual(tog1.status_code, 200)
        self.assertFalse(tog1.get_json()['item']['is_active'])

        # Toggle Active (Re-activate)
        tog2 = self.client.post(f'/api/vendor/menu/{tea_item["id"]}/toggle-active', json={}, headers={'Authorization': f'Bearer {v_token}'})
        self.assertEqual(tog2.status_code, 200)
        self.assertTrue(tog2.get_json()['item']['is_active'])

if __name__ == '__main__':
    unittest.main()
