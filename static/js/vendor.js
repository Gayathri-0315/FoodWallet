/**
 * FOODWALLET Vendor Control Dashboard JavaScript Engine
 * Secret Canteen Management Portal Engine
 * Formats Real Timestamps & Real Date for Audit Logs, Top-Up Requests, and Customer Registrations
 * Clean English Error Messages (No developer/programming code output exposed)
 */

let vendorState = {
  token: localStorage.getItem('foodwallet_vendor_token') || null,
  user: JSON.parse(localStorage.getItem('foodwallet_vendor_user') || 'null'),
  summary: {},
  requests: [],
  menu: [],
  customers: [],
  auditLogs: [],
  lastPendingCount: 0
};

function showVendorToast(msg, type = 'info') {
  const container = document.getElementById('vtoast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

async function vendorApiFetch(endpoint, options = {}) {
  options.headers = options.headers || {};
  options.headers['Content-Type'] = 'application/json';
  if (vendorState.token) {
    options.headers['Authorization'] = `Bearer ${vendorState.token}`;
  }

  try {
    const res = await fetch(endpoint, options);
    const text = await res.text();
    let data = {};
    try {
      data = JSON.parse(text);
    } catch (e) {
      data = {};
    }

    if (res.status === 401 || res.status === 403) {
      handleVendorLogout();
      throw new Error(data.error || 'Authentication expired. Please sign in again.');
    }

    if (!res.ok) {
      const msg = (data && data.error && !data.error.includes('Unexpected') && !data.error.includes('<') && !data.error.includes('Traceback'))
        ? data.error 
        : 'Unable to complete the request right now. Please try again.';
      throw new Error(msg);
    }
    return data;
  } catch (err) {
    let friendlyMsg = err.message || 'Something went wrong. Please try again.';
    if (friendlyMsg.includes('Unexpected') || friendlyMsg.includes('<') || friendlyMsg.includes('SyntaxError') || friendlyMsg.includes('TypeError') || friendlyMsg.includes('JSON')) {
      friendlyMsg = 'Unable to complete the request right now. Please try again.';
    }
    throw new Error(friendlyMsg);
  }
}

function renderVendorAuthState() {
  const authView = document.getElementById('vendor-auth-view');
  const dashView = document.getElementById('vendor-dashboard-view');

  if (vendorState.token && vendorState.user) {
    // VENDOR LOGGED IN: Hide vendor login card completely, show vendor dashboard ONLY
    if (authView) {
      authView.style.display = 'none';
      authView.classList.add('hidden');
    }
    if (dashView) {
      dashView.style.display = 'flex';
      dashView.classList.remove('hidden');
    }
    initVendorDashboard();
  } else {
    // VENDOR NOT LOGGED IN: Show vendor login card ONLY, hide vendor dashboard completely
    if (authView) {
      authView.style.display = 'block';
      authView.classList.remove('hidden');
    }
    if (dashView) {
      dashView.style.display = 'none';
      dashView.classList.add('hidden');
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  renderVendorAuthState();
});

async function handleVendorLogin(e) {
  e.preventDefault();
  const userInput = document.getElementById('vendor-user-input');
  const passInput = document.getElementById('vendor-pass-input');
  const btn = document.getElementById('btn-vendor-login');

  const username = userInput ? userInput.value : '';
  const password = passInput ? passInput.value : '';

  if (btn) {
    btn.disabled = true;
    btn.textContent = i18n.t('loading');
  }

  try {
    const data = await vendorApiFetch('/api/vendor/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });

    vendorState.token = data.access_token;
    vendorState.user = data.user;
    localStorage.setItem('foodwallet_vendor_token', data.access_token);
    localStorage.setItem('foodwallet_vendor_user', JSON.stringify(data.user));

    renderVendorAuthState();
    showVendorToast('Vendor Sign In Successful', 'success');
  } catch (err) {
    showVendorToast(err.message || 'Invalid username or password. Please try again.', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = i18n.t('vendor_login');
    }
  }
}

function handleVendorLogout() {
  vendorState.token = null;
  vendorState.user = null;
  localStorage.removeItem('foodwallet_vendor_token');
  localStorage.removeItem('foodwallet_vendor_user');
  
  renderVendorAuthState();
}

function initVendorDashboard() {
  loadVendorSummary();
  loadVendorRequests();
  loadVendorMenu();
  loadVendorCustomers();
  loadVendorAuditLogs();
  loadVendorSettings();

  switchVendorTab('requests');

  // Background Polling for Live Prepaid Request Notifications
  setInterval(pollVendorRequests, 8000);
}

// Top-Left Sidebar Tab Switcher
function switchVendorTab(tabId) {
  const panels = ['requests', 'menu', 'customers', 'audit', 'settings'];
  panels.forEach(p => {
    const panelElem = document.getElementById(`vpanel-${p}`);
    const btnElem = document.getElementById(`vtab-btn-${p}`);
    if (panelElem) panelElem.style.display = (p === tabId) ? 'block' : 'none';
    if (btnElem) {
      if (p === tabId) {
        btnElem.classList.add('active');
      } else {
        btnElem.classList.remove('active');
      }
    }
  });

  if (tabId === 'requests') loadVendorRequests();
  if (tabId === 'menu') loadVendorMenu();
  if (tabId === 'customers') loadVendorCustomers();
  if (tabId === 'audit') loadVendorAuditLogs();
  if (tabId === 'settings') loadVendorSettings();
}

async function loadVendorSummary() {
  try {
    const data = await vendorApiFetch('/api/vendor/summary');
    vendorState.summary = data;
    const elemCust = document.getElementById('vstat-customers');
    const elemPend = document.getElementById('vstat-pending');
    const elemSales = document.getElementById('vstat-today-sales');
    const elemItems = document.getElementById('vstat-items');

    if (elemCust) elemCust.textContent = data.total_customers;
    if (elemPend) elemPend.textContent = data.pending_requests;
    if (elemSales) elemSales.textContent = data.today_sales.toFixed(2);
    if (elemItems) elemItems.textContent = data.active_items;
  } catch (err) {
    console.error(err);
  }
}

async function pollVendorRequests() {
  if (!vendorState.token) return;
  try {
    const reqs = await vendorApiFetch('/api/vendor/wallet-requests');
    const requestsList = Array.isArray(reqs) ? reqs : [];
    const pendingList = requestsList.filter(r => r.status === 'PENDING');
    
    if (pendingList.length > vendorState.lastPendingCount) {
      const latest = pendingList[0];
      const title = i18n.t('prepaid_popup_title');
      const body = i18n.t('prepaid_popup_body');
      showVendorToast(`🔔 ${title} ${latest.customer_name} ${body} ₹${latest.amount.toFixed(2)}`, 'info');
    }
    
    vendorState.lastPendingCount = pendingList.length;
    vendorState.requests = requestsList;
    renderVendorRequestsTable();
    loadVendorSummary();
  } catch (err) {
    console.error(err);
  }
}

async function loadVendorRequests() {
  try {
    const reqs = await vendorApiFetch('/api/vendor/wallet-requests');
    const list = Array.isArray(reqs) ? reqs : [];
    vendorState.requests = list;
    vendorState.lastPendingCount = list.filter(r => r.status === 'PENDING').length;
    renderVendorRequestsTable();
  } catch (err) {
    console.error(err);
  }
}

function renderVendorRequestsTable() {
  const tbody = document.getElementById('vtable-requests-body');
  if (!tbody) return;

  if (!vendorState.requests || vendorState.requests.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No wallet requests found.</td></tr>`;
    return;
  }

  tbody.innerHTML = vendorState.requests.map(r => {
    const realTime = i18n.formatRealDateTime(r.created_at);
    const statusClass = r.status;
    const isPending = r.status === 'PENDING';

    const actions = isPending ? `
      <div style="display: flex; gap: 6px;">
        <button class="btn-primary" id="btn-approve-${r.id}" style="padding: 4px 10px; font-size: 0.75rem; width: auto;" onclick="approveRequest(${r.id})">${i18n.t('btn_approve')}</button>
        <button class="btn-secondary" id="btn-reject-${r.id}" style="padding: 4px 10px; font-size: 0.75rem; color: #be123c; border-color: #fecdd3; width: auto;" onclick="rejectRequest(${r.id})">${i18n.t('btn_reject')}</button>
      </div>
    ` : '-';

    return `
      <tr>
        <td>#${r.id}</td>
        <td><strong>${r.customer_name}</strong></td>
        <td>₹${r.amount.toFixed(2)}</td>
        <td style="white-space: nowrap; font-size: 0.8rem; font-weight: 600;">${realTime}</td>
        <td><span class="badge-status ${statusClass}">${i18n.t(`status_${r.status.toLowerCase()}`)}</span></td>
        <td>${actions}</td>
      </tr>
    `;
  }).join('');
}

async function approveRequest(reqId) {
  const btnApprove = document.getElementById(`btn-approve-${reqId}`);
  const btnReject = document.getElementById(`btn-reject-${reqId}`);
  
  if (btnApprove) { btnApprove.disabled = true; btnApprove.textContent = i18n.t('approving'); }
  if (btnReject) { btnReject.disabled = true; }

  try {
    const res = await vendorApiFetch(`/api/vendor/wallet-requests/${reqId}/approve`, { method: 'POST' });
    showVendorToast(res.message || 'Top-up request approved successfully!', 'success');
    loadVendorRequests();
    loadVendorSummary();
    loadVendorCustomers();
    loadVendorAuditLogs();
  } catch (err) {
    const cleanError = (err.message && !err.message.includes('Unexpected') && !err.message.includes('<'))
      ? err.message 
      : 'Unable to approve the request right now. Please try again.';
    showVendorToast(cleanError, 'error');
  } finally {
    if (btnApprove) { btnApprove.disabled = false; btnApprove.textContent = i18n.t('btn_approve'); }
    if (btnReject) { btnReject.disabled = false; }
  }
}

async function rejectRequest(reqId) {
  const reason = prompt("Enter rejection reason (optional):", "Incorrect details");
  const btnApprove = document.getElementById(`btn-approve-${reqId}`);
  const btnReject = document.getElementById(`btn-reject-${reqId}`);

  if (btnApprove) { btnApprove.disabled = true; }
  if (btnReject) { btnReject.disabled = true; btnReject.textContent = i18n.t('rejecting'); }

  try {
    const res = await vendorApiFetch(`/api/vendor/wallet-requests/${reqId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
    showVendorToast(res.message || 'Top-up request rejected.', 'info');
    loadVendorRequests();
    loadVendorSummary();
    loadVendorAuditLogs();
  } catch (err) {
    const cleanError = (err.message && !err.message.includes('Unexpected') && !err.message.includes('<'))
      ? err.message 
      : 'Unable to reject the request right now. Please try again.';
    showVendorToast(cleanError, 'error');
  } finally {
    if (btnApprove) { btnApprove.disabled = false; }
    if (btnReject) { btnReject.disabled = false; btnReject.textContent = i18n.t('btn_reject'); }
  }
}

async function loadVendorMenu() {
  try {
    const items = await vendorApiFetch('/api/vendor/menu');
    vendorState.menu = Array.isArray(items) ? items : [];
    renderVendorMenuTable();
  } catch (err) {
    console.error(err);
  }
}

function renderVendorMenuTable() {
  const tbody = document.getElementById('vtable-menu-body');
  if (!tbody) return;

  if (!vendorState.menu || vendorState.menu.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No menu items found.</td></tr>`;
    return;
  }

  tbody.innerHTML = vendorState.menu.map(i => {
    const statusBadge = i.is_active 
      ? `<span class="badge-status APPROVED">ACTIVE</span>` 
      : `<span class="badge-status REJECTED">INACTIVE</span>`;

    const activateBtn = i.is_active
      ? `<button class="btn-primary" style="padding: 4px 10px; font-size: 0.75rem; width: auto; opacity: 0.4; cursor: default;" disabled>${i18n.t('btn_activate')}</button>`
      : `<button class="btn-primary" style="padding: 4px 10px; font-size: 0.75rem; width: auto;" onclick="setFoodItemActive(${i.id}, true)">${i18n.t('btn_activate')}</button>`;

    const deactivateBtn = !i.is_active
      ? `<button class="btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; color: #be123c; width: auto; opacity: 0.4; cursor: default;" disabled>${i18n.t('btn_deactivate')}</button>`
      : `<button class="btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; color: #be123c; border-color: #fecdd3; width: auto;" onclick="setFoodItemActive(${i.id}, false)">${i18n.t('btn_deactivate')}</button>`;

    return `
      <tr>
        <td>#${i.id}</td>
        <td><strong>${i.name}</strong></td>
        <td>₹${i.price.toFixed(2)}</td>
        <td>${statusBadge}</td>
        <td>
          <div style="display: flex; gap: 6px; align-items: center;">
            <button class="btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; width: auto;" onclick="openEditMenuModal(${i.id})">${i18n.t('btn_edit')}</button>
            ${activateBtn}
            ${deactivateBtn}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

async function setFoodItemActive(id, targetState) {
  const item = vendorState.menu.find(i => i.id === id);
  if (item && item.is_active === targetState) return;

  try {
    const res = await vendorApiFetch(`/api/vendor/menu/${id}/toggle-active`, { method: 'POST' });
    showVendorToast(res.message || 'Food item updated', 'success');
    loadVendorMenu();
    loadVendorSummary();
  } catch (err) {
    showVendorToast(err.message || 'Unable to update food item', 'error');
  }
}

function openAddMenuModal() {
  const modalTitle = document.getElementById('menu-modal-title');
  const inputId = document.getElementById('modal-menu-id');
  const inputName = document.getElementById('modal-menu-name');
  const inputPrice = document.getElementById('modal-menu-price');

  if (modalTitle) modalTitle.textContent = 'Add Food Item';
  if (inputId) inputId.value = '';
  if (inputName) inputName.value = '';
  if (inputPrice) inputPrice.value = '';

  const modal = document.getElementById('menu-modal');
  if (modal) modal.classList.add('active');
}

function openEditMenuModal(id) {
  const item = vendorState.menu.find(i => i.id === id);
  if (!item) return;

  const modalTitle = document.getElementById('menu-modal-title');
  const inputId = document.getElementById('modal-menu-id');
  const inputName = document.getElementById('modal-menu-name');
  const inputPrice = document.getElementById('modal-menu-price');

  if (modalTitle) modalTitle.textContent = 'Edit Food Item';
  if (inputId) inputId.value = item.id;
  if (inputName) inputName.value = item.name;
  if (inputPrice) inputPrice.value = item.price;

  const modal = document.getElementById('menu-modal');
  if (modal) modal.classList.add('active');
}

function closeMenuModal() {
  const modal = document.getElementById('menu-modal');
  if (modal) modal.classList.remove('active');
}

async function handleSaveMenuItem(e) {
  e.preventDefault();
  const idInput = document.getElementById('modal-menu-id');
  const nameInput = document.getElementById('modal-menu-name');
  const priceInput = document.getElementById('modal-menu-price');
  const btn = document.getElementById('btn-save-menu-item');

  const id = idInput ? idInput.value : '';
  const name = nameInput ? nameInput.value : '';
  const price = priceInput ? priceInput.value : '';

  if (btn) {
    btn.disabled = true;
    btn.textContent = i18n.t('loading');
  }

  try {
    if (id) {
      await vendorApiFetch(`/api/vendor/menu/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ name, price })
      });
      showVendorToast('Menu item updated successfully', 'success');
    } else {
      await vendorApiFetch('/api/vendor/menu', {
        method: 'POST',
        body: JSON.stringify({ name, price })
      });
      showVendorToast('Menu item added successfully', 'success');
    }

    closeMenuModal();
    loadVendorMenu();
    loadVendorSummary();
  } catch (err) {
    showVendorToast(err.message || 'Unable to save menu item', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Save';
    }
  }
}

async function loadVendorCustomers() {
  try {
    const data = await vendorApiFetch('/api/vendor/customers');
    const customers = (data && data.customers) ? data.customers : (Array.isArray(data) ? data : []);
    vendorState.customers = customers;
    renderVendorCustomersTable();
  } catch (err) {
    console.error(err);
  }
}

function renderVendorCustomersTable() {
  const tbody = document.getElementById('vtable-customers-body');
  if (!tbody) return;

  if (!vendorState.customers || vendorState.customers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No registered customers found.</td></tr>`;
    return;
  }

  tbody.innerHTML = vendorState.customers.map(c => {
    const lowBadge = c.is_low_balance ? `<span class="badge-status REJECTED" style="margin-left: 6px;">LOW</span>` : '';
    const regDate = c.user.created_at ? i18n.formatRealDateTime(c.user.created_at) : '-';

    return `
      <tr>
        <td>#${c.user.id}</td>
        <td><strong>${c.user.name}</strong></td>
        <td>${c.user.phone}</td>
        <td>₹${c.balance.toFixed(2)} ${lowBadge}</td>
        <td>${c.total_orders}</td>
        <td style="white-space: nowrap; font-size: 0.8rem; font-weight: 600;">${regDate}</td>
      </tr>
    `;
  }).join('');
}

async function loadVendorAuditLogs() {
  try {
    const data = await vendorApiFetch('/api/vendor/audit-logs');
    const logs = (data && data.logs) ? data.logs : (Array.isArray(data) ? data : []);
    vendorState.auditLogs = logs;
    renderVendorAuditTable();
  } catch (err) {
    console.error(err);
  }
}

function formatHumanTargetEntity(entity, entityId) {
  const idStr = entityId ? ` #${entityId}` : '';
  if (entity === 'WalletRequest') {
    return `${i18n.t('entity_topup_req')}${idStr}`;
  } else if (entity === 'FoodItem') {
    return `${i18n.t('entity_food_item')}${idStr}`;
  } else if (entity === 'User' || entity === 'Wallet') {
    return `${i18n.t('entity_customer')}${idStr}`;
  } else if (entity === 'FoodTransaction') {
    return `Food Order ${entityId || ''}`;
  }
  return `${entity}${idStr}`;
}

function formatAuditDetailsToHumanLanguage(action, detailsObj) {
  let details = detailsObj;
  if (typeof details === 'string') {
    try { details = JSON.parse(details); } catch (e) { details = {}; }
  }
  details = details || {};
  const isTa = i18n.currentLang === 'ta';

  switch (action) {
    case 'APPROVED_TOPUP':
      return isTa
        ? `வாடிக்கையாளருக்கு ₹${(details.amount || 0).toFixed(2)} பணம் சேர்க்க அனுமதி வழங்கப்பட்டது.`
        : `Approved money top-up of ₹${(details.amount || 0).toFixed(2)} for Customer #${details.customer_id || ''}. New Balance: ₹${(details.balance_after || 0).toFixed(2)}`;
    case 'REJECTED_TOPUP':
      return isTa
        ? `வாடிக்கையாளரின் ₹${(details.amount || 0).toFixed(2)} பணப்பைக் கோரிக்கை நிராகரிக்கப்பட்டது.`
        : `Rejected top-up request of ₹${(details.amount || 0).toFixed(2)} for Customer #${details.customer_id || ''}. Reason: ${details.reason || 'None'}`;
    case 'REQUESTED_TOPUP':
      return isTa
        ? `வாடிக்கையாளர் ₹${(details.amount || 0).toFixed(2)} பணப்பையில் சேர்க்க விண்ணப்பித்துள்ளார்.`
        : `Customer requested to add ₹${(details.amount || 0).toFixed(2)} to their prepaid wallet`;
    case 'CANCELLED_TOPUP':
      return isTa
        ? `வாடிக்கையாளர் தனது பணப்பைக் கோரிக்கையை ரத்து செய்தார்.`
        : `Customer cancelled their top-up request of ₹${(details.amount || 0).toFixed(2)}`;
    case 'REGISTERED':
      return isTa
        ? `புதிய வாடிக்கையாளர் கணக்கு தொடங்கப்பட்டது: ${details.name || ''} (${details.phone || ''})`
        : `New customer account created: ${details.name || ''} (${details.phone || ''})`;
    case 'VENDOR_LOGIN':
      return isTa
        ? `வியாபாரி நிர்வாகப் பக்கத்தில் உள்நுழைந்தார்.`
        : `Vendor logged into the control dashboard`;
    case 'FOOD_PURCHASE':
      return isTa
        ? `வாடிக்கையாளர் உணவு வாங்கினார். மொத்த தொகை: ₹${(details.total_amount || 0).toFixed(2)}.`
        : `Customer purchased food items. Total: ₹${(details.total_amount || 0).toFixed(2)}. Remaining Balance: ₹${(details.balance_after || 0).toFixed(2)}`;
    case 'FOOD_REFUND':
      return isTa
        ? `உணவுத் தொகை ₹${(details.refund_amount || 0).toFixed(2)} வாடிக்கையாளருக்குத் திரும்ப செலுத்தப்பட்டது.`
        : `Refunded ₹${(details.refund_amount || 0).toFixed(2)} back to Customer #${details.customer_id || ''}`;
    case 'TOGGLE_FOOD_ITEM_ACTIVE':
      return isTa
        ? `உணவுப் பொருள் '${details.name || ''}' நிலையை மாற்றினார்.`
        : `Toggled food item '${details.name || ''}' active state`;
    case 'ADDED_FOOD_ITEM':
      return isTa
        ? `புதிய உணவுப் பொருள் சேர்க்கப்பட்டது: '${details.name || ''}' (₹${(details.price || 0).toFixed(2)})`
        : `Added new food item '${details.name || ''}' priced at ₹${(details.price || 0).toFixed(2)}`;
    case 'UPDATED_FOOD_ITEM':
      return isTa
        ? `உணவுப் பொருள் '${details.name || ''}' விலை ₹${(details.price || 0).toFixed(2)} என மாற்றப்பட்டது.`
        : `Updated food item '${details.name || ''}' price to ₹${(details.price || 0).toFixed(2)}`;
    case 'UPDATED_SETTING':
      return isTa
        ? `குறைந்த இருப்பு வரம்பு ₹${(details.threshold || 0).toFixed(2)} என மாற்றப்பட்டது.`
        : `Updated low balance alert limit to ₹${(details.threshold || 0).toFixed(2)}`;
    default:
      return Object.keys(details).length > 0 ? JSON.stringify(details) : 'Completed';
  }
}

function renderVendorAuditTable() {
  const tbody = document.getElementById('vtable-audit-body');
  if (!tbody) return;

  if (!vendorState.auditLogs || vendorState.auditLogs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No audit logs recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = vendorState.auditLogs.map(l => {
    const realTime = i18n.formatRealDateTime(l.timestamp);
    const readableDetails = formatAuditDetailsToHumanLanguage(l.action, l.details);
    const humanEntity = formatHumanTargetEntity(l.entity, l.entity_id);
    const readableAction = l.action.replace(/_/g, ' ');

    return `
      <tr>
        <td style="white-space: nowrap; font-size: 0.8rem; font-weight: 600;">${realTime}</td>
        <td><span class="badge-status ${l.actor_type === 'vendor' ? 'APPROVED' : 'PENDING'}">${l.actor_type.toUpperCase()}</span></td>
        <td style="font-size: 0.82rem; font-weight: 700; color: var(--text-dark);">${humanEntity}</td>
        <td><span style="font-size: 0.82rem; font-weight: 600; color: var(--text-dark);">${readableDetails}</span></td>
      </tr>
    `;
  }).join('');
}

async function loadVendorSettings() {
  try {
    const data = await vendorApiFetch('/api/vendor/settings');
    const input = document.getElementById('vinput-threshold');
    if (input) input.value = data.low_balance_threshold;
  } catch (err) {
    console.error(err);
  }
}

async function handleSaveSettings(e) {
  e.preventDefault();
  const input = document.getElementById('vinput-threshold');
  const val = input ? parseFloat(input.value) : 50;
  try {
    await vendorApiFetch('/api/vendor/settings', {
      method: 'POST',
      body: JSON.stringify({ low_balance_threshold: val })
    });
    showVendorToast('Settings updated successfully', 'success');
  } catch (err) {
    showVendorToast(err.message || 'Unable to update settings', 'error');
  }
}
