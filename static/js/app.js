/**
 * FOODWALLET Customer Single-Page Application (SPA) Engine
 * Strict Authentication Gate:
 * IF NOT authenticated -> RENDER ONLY Sign In / Create Account Page
 * ELSE -> RENDER ONLY Customer Dashboard
 */

let state = {
  token: localStorage.getItem('foodwallet_token') || null,
  user: JSON.parse(localStorage.getItem('foodwallet_user') || 'null'),
  balance: parseFloat(localStorage.getItem('foodwallet_balance') || '0.0'),
  menu: JSON.parse(localStorage.getItem('foodwallet_menu') || '[]'),
  cart: {},
  history: JSON.parse(localStorage.getItem('foodwallet_history') || '[]')
};

// Toast Notification Helper
function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// Session Expiration Handling
function handleUnauthorizedResponse() {
  state.token = null;
  state.user = null;
  state.balance = 0.0;
  state.cart = {};
  state.history = [];
  localStorage.removeItem('foodwallet_token');
  localStorage.removeItem('foodwallet_user');
  localStorage.removeItem('foodwallet_balance');
  localStorage.removeItem('foodwallet_menu');
  localStorage.removeItem('foodwallet_history');
  
  renderAuthState();
}

// Ultra-Fast API Fetch Helper
async function apiFetch(endpoint, options = {}) {
  options.headers = options.headers || {};
  options.headers['Content-Type'] = 'application/json';
  if (state.token) {
    options.headers['Authorization'] = `Bearer ${state.token}`;
  }

  try {
    const res = await fetch(endpoint, options);
    const data = await res.json();
    if (res.status === 401 || res.status === 403) {
      handleUnauthorizedResponse();
      throw new Error(data.error || i18n.t('auth_err_invalid'));
    }
    if (!res.ok) {
      throw new Error(data.error || 'Request failed');
    }
    return data;
  } catch (err) {
    throw err;
  }
}

// Render Authentication Gate: Strictly 1 state visible at a time
function renderAuthState() {
  const authPanel = document.getElementById('auth-panel');
  const mainPanel = document.getElementById('main-panel');

  if (state.token && state.user) {
    // LOGGED IN: Hide Customer Sign In page completely, show Customer Dashboard ONLY
    if (authPanel) {
      authPanel.style.display = 'none';
      authPanel.classList.add('hidden');
    }
    if (mainPanel) {
      mainPanel.style.display = 'block';
      mainPanel.classList.remove('hidden');
    }
    initAuthenticatedDashboard();
  } else {
    // NOT LOGGED IN: Show Customer Sign In / Create Account page ONLY, hide Customer Dashboard completely
    if (authPanel) {
      authPanel.style.display = 'block';
      authPanel.classList.remove('hidden');
    }
    if (mainPanel) {
      mainPanel.style.display = 'none';
      mainPanel.classList.add('hidden');
    }
    showAuthTab('login');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  renderAuthState();
});

// Tab Color Shifting Helper for Login Screen
function showAuthTab(tab) {
  const loginForm = document.getElementById('login-form');
  const regForm = document.getElementById('register-form');
  const btnLogin = document.getElementById('tab-btn-login');
  const btnReg = document.getElementById('tab-btn-register');

  if (tab === 'login') {
    if (loginForm) loginForm.style.display = 'block';
    if (regForm) regForm.style.display = 'none';
    if (btnLogin) btnLogin.className = 'btn-primary';
    if (btnReg) btnReg.className = 'btn-secondary';
  } else {
    if (loginForm) loginForm.style.display = 'none';
    if (regForm) regForm.style.display = 'block';
    if (btnLogin) btnLogin.className = 'btn-secondary';
    if (btnReg) btnReg.className = 'btn-primary';
  }
}

async function handleCustomerRegister(e) {
  e.preventDefault();
  const nameInput = document.getElementById('reg-name');
  const phoneInput = document.getElementById('reg-phone');
  const emailInput = document.getElementById('reg-email');
  const passInput = document.getElementById('reg-password');
  const btn = document.getElementById('btn-submit-register');

  const name = nameInput ? nameInput.value : '';
  const phone = phoneInput ? phoneInput.value : '';
  const email = emailInput ? emailInput.value : '';
  const password = passInput ? passInput.value : '';

  if (btn) {
    btn.disabled = true;
    btn.textContent = i18n.t('loading');
  }

  try {
    const data = await apiFetch('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, phone, email, password })
    });

    state.token = data.access_token;
    state.user = data.user;
    state.balance = data.wallet_balance;
    localStorage.setItem('foodwallet_token', data.access_token);
    localStorage.setItem('foodwallet_user', JSON.stringify(data.user));
    localStorage.setItem('foodwallet_balance', data.wallet_balance.toString());

    renderAuthState();
    showToast(i18n.t('welcome') + `, ${data.user.name}!`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = i18n.t('register');
    }
  }
}

async function handleCustomerLogin(e) {
  e.preventDefault();
  const contactInput = document.getElementById('login-contact');
  const passInput = document.getElementById('login-password');
  const btn = document.getElementById('btn-submit-login');

  const contact = contactInput ? contactInput.value : '';
  const password = passInput ? passInput.value : '';

  if (btn) {
    btn.disabled = true;
    btn.textContent = i18n.t('loading');
  }

  try {
    const data = await apiFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ phone: contact, password })
    });

    state.token = data.access_token;
    state.user = data.user;
    state.balance = data.wallet_balance;
    localStorage.setItem('foodwallet_token', data.access_token);
    localStorage.setItem('foodwallet_user', JSON.stringify(data.user));
    localStorage.setItem('foodwallet_balance', data.wallet_balance.toString());

    renderAuthState();
    showToast(i18n.t('welcome') + `, ${data.user.name}!`, 'success');
  } catch (err) {
    const errorMsg = err.message.includes('credentials') ? i18n.t('auth_err_invalid') : err.message;
    showToast(errorMsg, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = i18n.t('login');
    }
  }
}

function handleLogout() {
  state.token = null;
  state.user = null;
  state.balance = 0.0;
  state.cart = {};
  state.history = [];
  localStorage.removeItem('foodwallet_token');
  localStorage.removeItem('foodwallet_user');
  localStorage.removeItem('foodwallet_balance');
  localStorage.removeItem('foodwallet_menu');
  localStorage.removeItem('foodwallet_history');
  
  renderAuthState();
}

function initAuthenticatedDashboard() {
  // 1. Instant 0ms Pre-rendering from local cache
  if (state.user) {
    populateProfileUI(state.user, state.balance, 0, 0);
  }
  if (state.balance !== undefined) {
    const elemBal = document.getElementById('cust-balance-display');
    if (elemBal) elemBal.textContent = state.balance.toFixed(2);
  }
  if (state.menu && state.menu.length > 0) {
    renderMenu();
  }
  if (state.history && state.history.length > 0) {
    renderHistoryUI(state.history);
  }

  // 2. Ultra-Fast Parallel API Hydration
  loadUserProfile();
  loadMenuData();
  loadWalletData();
  loadOrdersData();
}

function switchTab(tabId) {
  const panels = document.querySelectorAll('.tab-panel');
  panels.forEach(p => p.classList.remove('active'));
  
  const navItems = document.querySelectorAll('.bottom-nav .nav-item');
  navItems.forEach(n => n.classList.remove('active'));

  const targetPanel = document.getElementById(`panel-${tabId}`);
  if (targetPanel) targetPanel.classList.add('active');

  const targetNav = document.getElementById(`nav-${tabId}`);
  if (targetNav) targetNav.classList.add('active');

  if (tabId === 'eat') loadMenuData();
  if (tabId === 'wallet') loadWalletData();
  if (tabId === 'history') loadOrdersData();
  if (tabId === 'profile') loadUserProfile();
}

async function loadUserProfile() {
  try {
    const data = await apiFetch('/api/auth/me');
    state.user = data.user;
    state.balance = data.wallet_balance;
    localStorage.setItem('foodwallet_user', JSON.stringify(data.user));
    localStorage.setItem('foodwallet_balance', data.wallet_balance.toString());

    populateProfileUI(data.user, data.wallet_balance, data.total_orders, data.total_spent);
  } catch (err) {
    console.error(err);
  }
}

function populateProfileUI(user, balance, ordersCount, totalSpent) {
  const elemName = document.getElementById('prof-name');
  const elemPhone = document.getElementById('prof-phone');
  const elemOrders = document.getElementById('prof-total-orders');
  const elemSpent = document.getElementById('prof-total-spent');
  const elemDate = document.getElementById('prof-created-at');
  const elemBal = document.getElementById('cust-balance-display');

  if (elemName) elemName.textContent = user.name || 'Customer';
  if (elemPhone) elemPhone.textContent = user.phone || '-';
  if (elemOrders) elemOrders.textContent = ordersCount || 0;
  if (elemSpent) elemSpent.textContent = (totalSpent || 0).toFixed(2);
  if (elemDate) elemDate.textContent = user.created_at ? i18n.formatRealDateTime(user.created_at) : '-';
  if (elemBal) elemBal.textContent = (balance || 0).toFixed(2);
}

async function loadMenuData() {
  try {
    const items = await apiFetch('/api/menu');
    state.menu = items;
    localStorage.setItem('foodwallet_menu', JSON.stringify(items));
    renderMenu();
  } catch (err) {
    console.error(err);
  }
}

function renderMenu() {
  const container = document.getElementById('food-menu-list');
  if (!container) return;

  if (!state.menu || state.menu.length === 0) {
    container.innerHTML = `<div style="text-align: center; padding: 24px; color: var(--text-muted);" data-i18n="no_food_available">No food items available today.</div>`;
    return;
  }

  container.innerHTML = state.menu.map(item => {
    const qty = state.cart[item.id] || 0;
    return `
      <div class="food-item-card">
        <div class="food-item-left">
          <div class="food-emoji">🍱</div>
          <div>
            <div class="food-item-name">${item.name}</div>
            <div class="food-item-price">₹${item.price.toFixed(2)}</div>
          </div>
        </div>
        <div class="counter-controls">
          <button class="counter-btn minus" onclick="updateCartItem(${item.id}, -1)">−</button>
          <span class="counter-qty">${qty}</span>
          <button class="counter-btn plus" onclick="updateCartItem(${item.id}, 1)">+</button>
        </div>
      </div>
    `;
  }).join('');

  updateCartTotalDisplay();
}

function updateCartItem(foodId, change) {
  const current = state.cart[foodId] || 0;
  const next = current + change;
  if (next <= 0) {
    delete state.cart[foodId];
  } else {
    state.cart[foodId] = next;
  }
  renderMenu();
}

function updateCartTotalDisplay() {
  let total = 0;
  if (state.menu) {
    state.menu.forEach(item => {
      const qty = state.cart[item.id] || 0;
      total += item.price * qty;
    });
  }
  const elemTotal = document.getElementById('cart-total-display');
  if (elemTotal) elemTotal.textContent = total.toFixed(2);
}

async function loadWalletData() {
  try {
    const data = await apiFetch('/api/wallet');
    state.balance = data.balance;
    localStorage.setItem('foodwallet_balance', data.balance.toString());

    const elemBal = document.getElementById('cust-balance-display');
    if (elemBal) elemBal.textContent = data.balance.toFixed(2);

    renderTopupRequests(data.topup_requests || []);
  } catch (err) {
    console.error(err);
  }
}

function renderTopupRequests(requests) {
  const container = document.getElementById('wallet-requests-list');
  if (!container) return;

  if (!requests || requests.length === 0) {
    container.innerHTML = `<div style="text-align: center; padding: 16px; color: var(--text-muted);" data-i18n="no_pending_requests">No top-up requests submitted.</div>`;
    return;
  }

  container.innerHTML = requests.map(r => {
    const realTime = i18n.formatRealDateTime(r.created_at);
    const statusClass = r.status;

    const cancelBtn = r.status === 'PENDING' 
      ? `<button class="btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; color: #be123c; border-color: #fecdd3; width: auto;" onclick="cancelTopup(${r.id})">${i18n.t('cancel')}</button>`
      : '';

    return `
      <div class="wallet-request-card card" style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; background: #ffffff; border-radius: 18px; padding: 16px 18px; box-shadow: var(--box-shadow-card);">
        <div>
          <div style="font-size: 1.05rem; font-weight: 800; color: var(--text-dark);">₹${r.amount.toFixed(2)}</div>
          <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; font-weight: 600;">${realTime}</div>
          ${r.rejection_reason ? `<div style="font-size: 0.75rem; color: #be123c; margin-top: 2px;">${r.rejection_reason}</div>` : ''}
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="badge-status ${statusClass}">${i18n.t(`status_${r.status.toLowerCase()}`)}</span>
          ${cancelBtn}
        </div>
      </div>
    `;
  }).join('');
}

async function handleTopupSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('topup-amount-input');
  const btn = document.getElementById('btn-submit-topup');

  const amount = input ? parseFloat(input.value) : 0;
  if (!amount || amount < 10) {
    showToast('Minimum top-up amount is ₹10.00', 'error');
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.textContent = i18n.t('loading');
  }

  try {
    const res = await apiFetch('/api/wallet/topup', {
      method: 'POST',
      body: JSON.stringify({ amount })
    });

    if (input) input.value = '';
    showToast(res.message || 'Top-up request sent to vendor', 'success');
    loadWalletData();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = i18n.t('send_request');
    }
  }
}

async function cancelTopup(reqId) {
  try {
    const res = await apiFetch(`/api/wallet/topup/${reqId}/cancel`, { method: 'POST' });
    showToast(res.message || 'Top-up request cancelled', 'info');
    loadWalletData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function submitFoodOrder() {
  const items = Object.keys(state.cart).map(foodId => ({
    food_id: parseInt(foodId),
    quantity: state.cart[foodId]
  })).filter(i => i.quantity > 0);

  if (items.length === 0) {
    showToast('Please select at least one food item', 'error');
    return;
  }

  const btn = document.getElementById('btn-confirm-order');
  if (btn) {
    btn.disabled = true;
    btn.textContent = i18n.t('placing_order');
  }

  const idempKey = 'order-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

  try {
    const data = await apiFetch('/api/orders', {
      method: 'POST',
      headers: { 'Idempotency-Key': idempKey },
      body: JSON.stringify({ items })
    });

    state.cart = {};
    renderMenu();
    loadWalletData();
    loadUserProfile();

    const receipt = data.receipt || data;

    triggerCheckmarkAnimation(i18n.t('status_approved') + '!', () => {
      openReceiptModal(receipt);
    });

  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = i18n.t('confirm_and_pay');
    }
  }
}

function triggerCheckmarkAnimation(msgText, callback) {
  const overlay = document.getElementById('checkmark-overlay');
  const msg = document.getElementById('checkmark-msg');
  if (msg) msg.textContent = msgText;
  
  if (overlay) overlay.classList.add('active');
  setTimeout(() => {
    if (overlay) overlay.classList.remove('active');
    if (callback) callback();
  }, 1400);
}

async function loadOrdersData() {
  try {
    const data = await apiFetch('/api/orders');
    const orders = (data && data.orders) ? data.orders : (Array.isArray(data) ? data : []);
    state.history = orders;
    localStorage.setItem('foodwallet_history', JSON.stringify(orders));

    renderHistoryUI(orders);
  } catch (err) {
    console.error(err);
  }
}

function renderHistoryUI(orders) {
  const homeRecent = document.getElementById('home-recent-activity');
  if (homeRecent) {
    if (!orders || orders.length === 0) {
      homeRecent.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted); text-align: center; padding: 16px;" data-i18n="no_recent_transactions">${i18n.t('no_recent_transactions')}</div>`;
    } else {
      homeRecent.innerHTML = orders.slice(0, 3).map(o => renderReceiptListItem(o)).join('');
    }
  }

  const fullHistory = document.getElementById('full-history-list');
  if (fullHistory) {
    if (!orders || orders.length === 0) {
      fullHistory.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted); text-align: center; padding: 24px;" data-i18n="no_recent_transactions">${i18n.t('no_recent_transactions')}</div>`;
    } else {
      fullHistory.innerHTML = orders.map(o => renderReceiptListItem(o)).join('');
    }
  }
}

function renderReceiptListItem(o) {
  const realTime = i18n.formatRealDateTime(o.created_at);
  const itemsSummary = (o.items || []).map(i => `${i.food_name} × ${i.quantity}`).join(', ');
  const statusBadge = o.is_refunded 
    ? `<span class="badge-status REJECTED">REFUNDED</span>` 
    : `<span class="badge-status PAID">${i18n.t('paid_status')}</span>`;

  return `
    <div class="recent-activity-card" onclick="openReceiptModalById('${o.transaction_id}')">
      <div>
        <div class="recent-activity-id">${o.transaction_id}</div>
        <div class="recent-activity-details">${itemsSummary}</div>
      </div>
      <div style="text-align: right;">
        <div class="recent-activity-amount">₹${o.total_amount.toFixed(2)}</div>
        <div>${statusBadge}</div>
        <div class="recent-activity-time">${realTime}</div>
      </div>
    </div>
  `;
}

function openReceiptModalById(txId) {
  const order = state.history.find(o => o.transaction_id === txId);
  if (order) openReceiptModal(order);
}

function openReceiptModal(rcpt) {
  if (!rcpt) return;
  const elemTx = document.getElementById('rcpt-tx-id');
  const elemCust = document.getElementById('rcpt-customer');
  const elemDt = document.getElementById('rcpt-datetime');
  const elemTotal = document.getElementById('rcpt-total-amount');
  const elemBefore = document.getElementById('rcpt-bal-before');
  const elemAfter = document.getElementById('rcpt-bal-after');

  if (elemTx) elemTx.textContent = rcpt.transaction_id || '';
  if (elemCust) elemCust.textContent = rcpt.customer_name || '';
  if (elemDt) elemDt.textContent = rcpt.created_at ? i18n.formatRealDateTime(rcpt.created_at) : '';
  if (elemTotal) elemTotal.textContent = (rcpt.total_amount || 0).toFixed(2);
  if (elemBefore) elemBefore.textContent = (rcpt.balance_before || 0).toFixed(2);
  if (elemAfter) elemAfter.textContent = (rcpt.balance_after || 0).toFixed(2);

  const itemsContainer = document.getElementById('rcpt-items-list');
  if (itemsContainer) {
    itemsContainer.innerHTML = (rcpt.items || []).map(i => `
      <div class="receipt-item-row">
        <span>${i.food_name} × ${i.quantity}</span>
        <span>₹${i.subtotal.toFixed(2)}</span>
      </div>
    `).join('');
  }

  const modal = document.getElementById('receipt-modal');
  if (modal) modal.classList.add('active');
}

function closeReceiptModal() {
  const modal = document.getElementById('receipt-modal');
  if (modal) modal.classList.remove('active');
}
