/**
 * FOODWALLET Internationalization (i18n) Engine
 * Supported Languages: English ('en'), Simple Tamil ('ta')
 * Indian Standard Time (IST) Real Date & Timestamp Formatter
 */

const translations = {
  en: {
    app_name: "FOODWALLET",
    welcome: "Welcome",
    login: "Sign In",
    register: "Create Account",
    vendor_login: "Vendor Sign In",
    vendor_username: "Username / Phone Number",
    phone_number: "Phone Number",
    password: "Password",
    full_name: "Full Name",
    email_address: "Email Address",
    enter_phone: "Enter your phone number",
    enter_password: "Enter your password",
    enter_name: "Enter your full name",
    enter_email: "gayathri.p_25it@kgkite.ac.in",

    // Auth error messages
    auth_err_invalid: "Invalid username/phone number or password",
    auth_err_exists: "An account with this phone number or email already exists",

    // Navigation
    nav_home: "Home",
    nav_eat: "Eat",
    nav_wallet: "Wallet",
    nav_history: "History",
    nav_profile: "Profile",

    // Home view
    wallet_balance: "Prepaid Wallet Balance",
    quick_actions: "Quick Actions",
    what_did_you_eat: "What did you eat?",
    add_money: "Add Money",
    recent_transactions: "Recent Activity",
    no_recent_transactions: "No recent transactions yet.",

    // Eat view
    total_bill: "Total Bill",
    confirm_and_pay: "Confirm & Pay",
    placing_order: "Placing Order...",

    // Wallet view
    request_topup: "Request Money Top-Up",
    topup_hint: "Enter amount to add to your prepaid wallet balance.",
    enter_topup_amount: "Enter Amount (₹)",
    submit_request: "Submit Top-Up Request",
    topup_history: "Top-Up Requests History",
    no_topup_history: "No top-up requests found.",
    topup_success_msg: "Top-up request sent to vendor successfully!",

    // Statuses
    status_pending: "PENDING",
    status_approved: "APPROVED",
    status_rejected: "REJECTED",
    status_cancelled: "CANCELLED",
    paid_status: "PAID",

    // Profile view
    profile_info: "Customer Profile",
    member_since: "Member Since",
    total_orders_placed: "Total Orders Placed",
    total_amount_spent: "Total Amount Spent",
    not_provided: "Not Provided",
    logout: "Log Out",

    // Vendor Dashboard
    stat_total_customers: "Total Customers",
    stat_pending_requests: "Pending Requests",
    stat_today_sales: "Today's Sales",
    stat_active_items: "Active Food Items",

    vtab_requests: "Prepaid Requests",
    vtab_menu: "Food Menu",
    vtab_customers: "Customers Directory",
    vtab_audit: "System Audit Logs",
    vtab_settings: "Vendor Settings",

    customer_name: "Customer",
    btn_approve: "Approve",
    btn_reject: "Reject",
    btn_edit: "Edit",
    btn_activate: "Activate",
    btn_deactivate: "Deactivate",
    btn_add_item: "+ Add Food Item",
    approving: "Approving...",
    rejecting: "Rejecting...",
    loading: "Loading...",

    // Audit log actions & entities
    entity_topup_req: "Top-Up Request",
    entity_food_item: "Food Item",
    entity_customer: "Customer",

    // Pop-up Notification
    prepaid_popup_title: "New Prepaid Request:",
    prepaid_popup_body: "requested money for food wallet!",

    // Receipt Card
    items_breakdown: "Food Items Eaten",
    total_amount: "Total Amount",
    balance_before: "Balance Before",
    balance_after: "Balance After",
    show_to_vendor: "Show this card directly to the vendor screen",
    close_card: "Close Card",
    date_time: "Date & Time"
  },
  ta: {
    app_name: "ஃபுட்வாலட்",
    welcome: "வரவேற்கிறோம்",
    login: "உள்நுழைக",
    register: "கணக்கு தொடங்க",
    vendor_login: "வியாபாரி உள்நுழைவு",
    vendor_username: "பயனர் பெயர் / தொலைபேசி எண்",
    phone_number: "தொலைபேசி எண்",
    password: "கடவுச்சொல்",
    full_name: "முழு பெயர்",
    email_address: "மின்னஞ்சல் முகவரி",
    enter_phone: "உங்கள் தொலைபேசி எண்ணை உள்ளிடுக",
    enter_password: "உங்கள் கடவுச்சொல்லை உள்ளிடுக",
    enter_name: "உங்கள் முழு பெயரை உள்ளிடுக",
    enter_email: "மின்னஞ்சலை உள்ளிடுக",

    // Auth error messages
    auth_err_invalid: "தவறான பயனர் பெயர்/தொலைபேசி எண் அல்லது கடவுச்சொல்",
    auth_err_exists: "இந்த தொலைபேசி எண்/மின்னஞ்சலில் ஏற்கனவே கணக்கு உள்ளது",

    // Navigation
    nav_home: "முகப்பு",
    nav_eat: "உணவு",
    nav_wallet: "பணப்பை",
    nav_history: "வரலாறு",
    nav_profile: "சுயவிவரம்",

    // Home view
    wallet_balance: "பணப்பை இருப்பு",
    quick_actions: "வேகமான செயல்பாடுகள்",
    what_did_you_eat: "என்ன சாப்பிட்டீர்கள்?",
    add_money: "பணம் சேர்க்க",
    recent_transactions: "சமீபத்திய பரிவர்த்தனைகள்",
    no_recent_transactions: "சமீபத்திய பரிவர்த்தனைகள் எதுவும் இல்லை.",

    // Eat view
    total_bill: "மொத்த கட்டணம்",
    confirm_and_pay: "உறுதிசெய்து செலுத்துங்கள்",
    placing_order: "ஆர்டர் செய்யப்படுகிறது...",

    // Wallet view
    request_topup: "பணம் சேர்க்க விண்ணப்பிக்கவும்",
    topup_hint: "உங்கள் பணப்பையில் சேர்க்க விரும்பும் தொகையை உள்ளிடவும்.",
    enter_topup_amount: "தொகையை உள்ளிடுக (₹)",
    submit_request: "விண்ணப்பிக்கவும்",
    topup_history: "பணம் சேர்த்த வரலாறு",
    no_topup_history: "விண்ணப்பங்கள் எதுவும் இல்லை.",
    topup_success_msg: "பணம் சேர்க்கும் விண்ணப்பம் அனுப்பப்பட்டது!",

    // Statuses
    status_pending: "நிலுவையில்",
    status_approved: "ஏற்றுக்கொள்ளப்பட்டது",
    status_rejected: "நிராகரிக்கப்பட்டது",
    status_cancelled: "ரத்து செய்யப்பட்டது",
    paid_status: "செலுத்தப்பட்டது",

    // Profile view
    profile_info: "வாடிக்கையாளர் சுயவிவரம்",
    member_since: "இணைந்த நாள்",
    total_orders_placed: "மொத்த உணவு ஆர்டர்கள்",
    total_amount_spent: "மொத்த செலவழித்த தொகை",
    not_provided: "வழங்கப்படவில்லை",
    logout: "வெளியேறு",

    // Vendor Dashboard
    stat_total_customers: "மொத்த வாடிக்கையாளர்கள்",
    stat_pending_requests: "நிலுவை விண்ணப்பங்கள்",
    stat_today_sales: "இன்றைய விற்பனை",
    stat_active_items: "செயலில் உள்ள உணவுகள்",

    vtab_requests: "பணப்பைக் கோரிக்கைகள்",
    vtab_menu: "உணவுப் பட்டியல்",
    vtab_customers: "வாடிக்கையாளர்கள் பட்டியல்",
    vtab_audit: "கணினி தணிக்கைப் பதிவுகள்",
    vtab_settings: "அமைப்புகள்",

    customer_name: "வாடிக்கையாளர்",
    btn_approve: "ஏற்றுக்கொள்",
    btn_reject: "நிராகரி",
    btn_edit: "திருத்து",
    btn_activate: "செயல்படுத்து",
    btn_deactivate: "முடக்கு",
    btn_add_item: "+ புதிய உணவு சேர்க்க",
    approving: "ஏற்கப்படுகிறது...",
    rejecting: "நிராகரிக்கப்படுகிறது...",
    loading: "காத்திருக்கவும்...",

    // Audit log actions & entities
    entity_topup_req: "பணப்பைக் கோரிக்கை",
    entity_food_item: "உணவுப் பொருள்",
    entity_customer: "வாடிக்கையாளர்",

    // Pop-up Notification
    prepaid_popup_title: "புதிய பணப்பைக் கோரிக்கை:",
    prepaid_popup_body: "பணப்பையில் பணம் சேர்க்க விண்ணப்பித்துள்ளார்!",

    // Receipt Card
    items_breakdown: "சாப்பிட்ட உணவுகள்",
    total_amount: "மொத்த தொகை",
    balance_before: "முந்தைய இருப்பு",
    balance_after: "தற்போதைய இருப்பு",
    show_to_vendor: "இந்த ரசீதை வியாபாரியிடம் காட்டவும்",
    close_card: "மூடுக",
    date_time: "நாள் மற்றும் நேரம்"
  }
};

class I18nEngine {
  constructor() {
    this.currentLang = localStorage.getItem('foodwallet_lang') || 'en';
  }

  setLanguage(lang) {
    if (!translations[lang]) return;
    this.currentLang = lang;
    localStorage.setItem('foodwallet_lang', lang);
    this.updateDOM();

    if (window.state && window.state.token && window.state.user && window.state.user.role === 'customer') {
      fetch('/api/auth/language', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${window.state.token}`
        },
        body: JSON.stringify({ language: lang })
      }).catch(err => console.error(err));
    }
  }

  t(key) {
    return (translations[this.currentLang] && translations[this.currentLang][key]) 
      || (translations['en'][key]) 
      || key;
  }

  updateDOM() {
    document.querySelectorAll('[data-i18n]').forEach(elem => {
      const key = elem.getAttribute('data-i18n');
      if (translations[this.currentLang][key]) {
        if (elem.tagName === 'INPUT' && (elem.type === 'button' || elem.type === 'submit')) {
          elem.value = this.t(key);
        } else if (elem.hasAttribute('placeholder')) {
          elem.placeholder = this.t(key);
        } else {
          elem.textContent = this.t(key);
        }
      }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(elem => {
      const key = elem.getAttribute('data-i18n-placeholder');
      if (translations[this.currentLang][key]) {
        elem.placeholder = this.t(key);
      }
    });

    document.querySelectorAll('.lang-btn').forEach(btn => {
      if (btn.getAttribute('data-lang') === this.currentLang) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  /**
   * Formats ISO timestamp string stored in DB into exact real IST date & time.
   * Output Example: "19 Aug 2026, 12:11:34 AM"
   */
  formatRealDateTime(isoDateStr) {
    if (!isoDateStr) return '-';
    const date = new Date(isoDateStr);
    if (isNaN(date.getTime())) return '-';

    return date.toLocaleString(this.currentLang === 'ta' ? 'ta-IN' : 'en-IN', {
      timeZone: 'Asia/Kolkata',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  }

  /**
   * Calculates relative time from stored database ISO timestamp (not page load time).
   */
  formatRelativeTime(isoDateStr) {
    if (!isoDateStr) return '-';
    const date = new Date(isoDateStr);
    if (isNaN(date.getTime())) return '-';

    const now = new Date();
    const diffSecs = Math.floor((now - date) / 1000);

    if (diffSecs >= 0 && diffSecs < 60) {
      return this.currentLang === 'ta' ? 'சற்று முன்' : 'Just now';
    }
    const diffMins = Math.floor(diffSecs / 60);
    if (diffMins > 0 && diffMins < 60) {
      return this.currentLang === 'ta' ? `${diffMins} நிமிடங்களுக்கு முன்` : `${diffMins} mins ago`;
    }
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours > 0 && diffHours < 24) {
      return this.currentLang === 'ta' ? `${diffHours} மணிநேரத்திற்கு முன்` : `${diffHours} hours ago`;
    }

    return this.formatRealDateTime(isoDateStr);
  }
}

const i18n = new I18nEngine();

document.addEventListener('DOMContentLoaded', () => {
  i18n.updateDOM();
});
