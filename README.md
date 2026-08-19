# 🍱 FOODWALLET — Prepaid Food Billing & Canteen Management Application

Complete production-ready FoodWallet application codebase.

---

## 📂 Project Directory Location

```text
C:\Users\KiTE\.gemini\antigravity\scratch\foodwallet-ai
```

---

## 📁 Complete Folder Structure

```text
foodwallet-ai/
├── app.py                      # Main Flask Application & API Routes Engine
├── config.py                   # Environment Configuration & Database Connections
├── models.py                   # SQLAlchemy Models (IST Timezone, Audit, Wallets, Menu)
├── requirements.txt            # Python Dependencies List
├── foodwallet.db               # SQLite Production Database File
├── .env                        # Environment Variables File
├── services/
│   ├── audit_service.py        # System Audit Log Event Logger
│   ├── auth_service.py         # JWT Auth, Rate Limiting & Password Hashing
│   ├── billing_service.py      # Food Ordering & Idempotent Billing Engine
│   └── wallet_service.py       # Prepaid Wallet Top-Up & Financial Ledger Service
├── templates/
│   ├── index.html              # Customer SPA Application View
│   ├── vendor.html             # Secret Vendor Control Center View
│   └── login.html              # Dedicated Customer Sign In View
└── static/
    ├── css/
    │   └── style.css           # Custom UI Stylesheet & Responsive Layouts
    └── js/
        ├── app.js              # Customer App Engine & State Handler
        ├── vendor.js           # Secret Vendor Dashboard Engine
        └── i18n.js             # Internationalization (English / Tamil) & IST Time Engine
```

---

## 🚀 How to Run in VS Code

### Step 1: Open VS Code in Project Directory
Open VS Code terminal or command prompt and run:
```bash
cd C:\Users\KiTE\.gemini\antigravity\scratch\foodwallet-ai
code .
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Start the FoodWallet Server
```bash
python app.py
```

---

## 🌐 Application Access URLs & Credentials

| Portal | URL | Credentials |
| :--- | :--- | :--- |
| **Customer App** | `http://127.0.0.1:5000/` | Customer Sign In / Create Account |
| **Secret Vendor Control Center** | `http://127.0.0.1:5000/vendor-control-8x92k` | **Username**: `admin` or `9999999999`<br>**Password**: `vendor123` |

---

## ✨ Features Summary

1. **Strict Customer First-Screen Gate**: Customer opens `http://127.0.0.1:5000/` ➔ Sign In / Create Account ➔ Customer Dashboard. Zero dashboard flashing.
2. **Food Item Cards**: "What did you eat?" displays rounded food cards with emoji, food name, price, minus button, quantity counter, and plus button.
3. **Vendor Control Center**: Complete canteen management dashboard with live metrics, customer directory, audit logs, food menu toggles, and top-up approvals.
4. **Real IST Action Timestamps**: All actions (top-up requests, registrations, approvals, orders) record exact server-side **Indian Standard Time (IST UTC+5:30)**.
5. **Clean Error Handling**: Suppresses technical exceptions, database errors, and stack traces from end-user UI, returning friendly English alert messages.
