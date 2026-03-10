// Service Desk DP — Campos e Souza Consultoria
// Main JavaScript

// ── Sidebar toggle ────────────────────────────────────────────────────────────
(function () {
  const btn = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (btn && sidebar) {
    btn.addEventListener('click', () => {
      sidebar.classList.toggle('cs-sidebar-open');
    });
  }
})();

// ── Notification dropdown ─────────────────────────────────────────────────────
(function () {
  const btn = document.getElementById('notifBtn');
  const dropdown = document.getElementById('notifDropdown');
  if (!btn || !dropdown) return;

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = dropdown.style.display === 'block';
    dropdown.style.display = isOpen ? 'none' : 'block';
  });

  document.addEventListener('click', () => {
    if (dropdown) dropdown.style.display = 'none';
  });

  dropdown.addEventListener('click', (e) => e.stopPropagation());
})();

// ── Mark all notifications read ───────────────────────────────────────────────
(function () {
  const link = document.getElementById('mark-all-read');
  if (!link) return;

  link.addEventListener('click', async (e) => {
    e.preventDefault();
    try {
      await fetch(link.href, { credentials: 'same-origin' });
      const badge = document.getElementById('notif-badge');
      if (badge) badge.remove();
    } catch (_) {}
  });
})();

// ── Toast helper ──────────────────────────────────────────────────────────────
function showToast(title, message, type = 'teal') {
  const typeIcon = {
    teal:   { icon: 'fa-check-circle',       color: '#34B29A' },
    orange: { icon: 'fa-exclamation-circle',  color: '#FF9000' },
    red:    { icon: 'fa-times-circle',        color: '#ef4444' },
  };

  const t = typeIcon[type] || typeIcon.teal;
  const container = document.getElementById('toast-container');
  if (!container) return;

  const el = document.createElement('div');
  el.style.cssText = `
    background: #111; border: 1px solid rgba(255,255,255,.08);
    border-left: 3px solid ${t.color}; border-radius: 10px;
    padding: 14px 18px; display: flex; align-items: flex-start; gap: 12px;
    box-shadow: 0 10px 40px rgba(0,0,0,.6);
    animation: fadeIn .3s ease; min-width: 280px; max-width: 360px;
  `;

  el.innerHTML = `
    <i class="fas ${t.icon}" style="color:${t.color}; margin-top:2px; font-size:16px; flex-shrink:0;"></i>
    <div style="flex:1;">
      <div style="font-weight:600; font-size:13px; color:#fff; margin-bottom:3px;">${title}</div>
      <div style="font-size:12px; color:#7A7A7A; line-height:1.4;">${message}</div>
    </div>
    <button onclick="this.parentElement.remove()" style="background:none; border:none; color:#7A7A7A; cursor:pointer; font-size:16px; padding:0; line-height:1;">×</button>
  `;

  container.appendChild(el);
  setTimeout(() => el.style.opacity = '0', 5500);
  setTimeout(() => el.remove(), 6000);
}

// ── File upload display ───────────────────────────────────────────────────────
document.querySelectorAll('.upload-zone input[type="file"]').forEach((input) => {
  input.addEventListener('change', () => {
    const zone = input.closest('.upload-zone');
    if (!zone) return;
    const names = Array.from(input.files).map(f => f.name).join(', ');
    let preview = zone.querySelector('.upload-preview');
    if (!preview) {
      preview = document.createElement('div');
      preview.className = 'upload-preview';
      preview.style.cssText = 'margin-top:10px; font-size:12px; color:#34B29A; z-index:2; position:relative;';
      zone.appendChild(preview);
    }
    preview.textContent = names ? `📎 ${names}` : '';
  });
});

// ── Auto-close alerts after 4s ────────────────────────────────────────────────
document.querySelectorAll('[data-auto-close]').forEach((el) => {
  setTimeout(() => {
    el.style.transition = 'opacity .4s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  }, 4000);
});

// ── WebSocket — Notificações Realtime ─────────────────────────────────────────
(function () {
  if (!window.location.host) return;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${protocol}//${window.location.host}/ws/notifications/`;

  let ws;
  let retryDelay = 3000;

  function connect() {
    try {
      ws = new WebSocket(url);

      ws.onopen = () => { retryDelay = 3000; };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          showToast(data.title || 'Novo evento', data.message || '', data.type === 'danger' ? 'red' : data.type === 'warning' ? 'orange' : 'teal');

          // Atualiza badge
          const badge = document.getElementById('notif-badge');
          if (badge) {
            badge.textContent = parseInt(badge.textContent || '0') + 1;
          } else {
            const notifBtn = document.getElementById('notifBtn');
            if (notifBtn) {
              const span = document.createElement('span');
              span.id = 'notif-badge';
              span.className = 'notif-count';
              span.textContent = '1';
              notifBtn.appendChild(span);
            }
          }
        } catch (_) {}
      };

      ws.onclose = () => {
        setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 1.5, 30000);
      };

    } catch (_) {}
  }

  connect();
})();
