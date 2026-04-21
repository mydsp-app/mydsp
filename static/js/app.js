document.addEventListener('DOMContentLoaded', function () {

  // ── Sidebar toggle ────────────────────────────────────────────
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const main = document.getElementById('main-content');
  if (toggle) {
    toggle.addEventListener('click', function () {
      sidebar.classList.toggle('collapsed');
      main.classList.toggle('expanded');
    });
  }

  // ── DataTables ────────────────────────────────────────────────
  if ($.fn.DataTable) {
    $.fn.dataTable.ext.errMode = 'none';
    $('.datatable').each(function () {
      if (!$.fn.DataTable.isDataTable(this)) {
        $(this).DataTable({
          pageLength: 25,
          language: { search: '', searchPlaceholder: 'Search...' },
          dom: '<"d-flex justify-content-between align-items-center mb-2"lf>rtip',
          order: []
        });
      }
    });
  }

  // ── Staff cost auto-calc ──────────────────────────────────────
  function calcStaffCost() {
    const qty        = parseFloat($('#qty_hours').val()) || 0;
    const ndisRate   = parseFloat($('#ndis_rate').val()) || 0;
    const actualRate = parseFloat($('#actual_rate').val()) || 0;
    const ndisRev    = qty * ndisRate;
    const actualWage = qty * actualRate;
    const superAmt   = actualWage * 0.12;
    const totalCost  = actualWage + superAmt;
    const margin     = ndisRev - totalCost;
    $('#ndis_revenue').val(ndisRev.toFixed(2));
    $('#actual_wage').val(actualWage.toFixed(2));
    $('#super_amount').val(superAmt.toFixed(2));
    $('#total_cost').val(totalCost.toFixed(2));
    $('#margin').val(margin.toFixed(2))
      .removeClass('text-success text-danger')
      .addClass(margin >= 0 ? 'text-success' : 'text-danger');
  }
  $('#qty_hours, #ndis_rate, #actual_rate').on('input', calcStaffCost);

  // NDIS rate auto-fill on shift type change
  const NDIS_RATES = {
    'Weekday Day': 70.23, 'Weekday Evening': 77.38, 'Saturday': 98.83,
    'Sunday': 127.43, 'Public Holiday': 156.03, 'SIL Night': 243.56,
    'SIL Active Night': 38.56
  };
  $('#shift_type').on('change', function () {
    const rate = NDIS_RATES[$(this).val()];
    if (rate) { $('#ndis_rate').val(rate); calcStaffCost(); }
  });

  // Participant name auto-fill from dropdown
  $('#participant_id').on('change', function () {
    const name = $(this).find('option:selected').text();
    if (name && name !== '-- Select --' && name !== '-- None --') {
      const nameField = $('#participant_name');
      if (nameField.length && !nameField.val()) nameField.val(name);
    }
  });

  // Confirm deletes
  document.querySelectorAll('form.delete-form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm('Are you sure you want to delete this entry? This cannot be undone.')) {
        e.preventDefault();
      }
    });
  });

  // Auto-dismiss alerts after 4s
  setTimeout(function () {
    document.querySelectorAll('.alert').forEach(function (el) {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    });
  }, 4000);

  // ── Alerts / Reminders ────────────────────────────────────────
  function levelIcon(level) {
    const icons = { danger: '🔴', warning: '🟡', info: '🔵' };
    return icons[level] || '⚪';
  }
  function levelClass(level) {
    const map = { danger: 'alert-danger', warning: 'alert-warning', info: 'alert-info' };
    return map[level] || 'alert-secondary';
  }
  function typeLabel(type) {
    const map = { plan: 'Plan', task: 'Task', budget: 'Budget', staff: 'Staff Cost' };
    return map[type] || type;
  }
  function typeBadgeClass(type) {
    const map = { plan: 'bg-purple', task: 'bg-primary', budget: 'bg-warning text-dark', staff: 'bg-danger' };
    return map[type] || 'bg-secondary';
  }

  function loadAlerts(showModalIfAny) {
    fetch('/api/alerts')
      .then(r => r.json())
      .then(data => {
        const count = data.count || 0;
        const badge = document.getElementById('alertBadge');
        if (badge) {
          if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.classList.remove('d-none');
            // Pulse animation for urgent
            const hasDanger = data.alerts.some(a => a.level === 'danger');
            if (hasDanger) badge.classList.add('pulse-badge');
          } else {
            badge.classList.add('d-none');
          }
        }

        // Build modal body
        const body = document.getElementById('alertsBody');
        if (!body) return;

        if (count === 0) {
          body.innerHTML = `<div class="text-center py-4 text-success">
            <i class="bi bi-check-circle-fill fs-2 mb-2 d-block"></i>
            <strong>All clear!</strong> No active reminders or alerts.
          </div>`;
        } else {
          // Group by type
          const groups = {};
          data.alerts.forEach(a => {
            if (!groups[a.type]) groups[a.type] = [];
            groups[a.type].push(a);
          });

          let html = `<div class="mb-2 text-muted small"><strong>${count}</strong> active alert${count !== 1 ? 's' : ''}</div>`;

          const order = ['plan', 'task', 'budget', 'staff'];
          order.forEach(type => {
            if (!groups[type]) return;
            html += `<h6 class="mt-3 mb-2 fw-bold" style="color:var(--navy);">
              <span class="badge ${typeBadgeClass(type)} me-2">${typeLabel(type)}</span>
              ${groups[type].length} alert${groups[type].length !== 1 ? 's' : ''}
            </h6>`;
            groups[type].forEach(a => {
              html += `<div class="alert ${levelClass(a.level)} py-2 px-3 mb-2 d-flex align-items-start gap-2">
                <span style="font-size:1rem;">${levelIcon(a.level)}</span>
                <span class="small">${a.message}</span>
              </div>`;
            });
          });
          body.innerHTML = html;
        }

        // Auto-show modal on dashboard if there are danger alerts
        if (showModalIfAny && count > 0) {
          const hasDanger = data.alerts.some(a => a.level === 'danger');
          const hasWarning = data.alerts.some(a => a.level === 'warning');
          // Only auto-popup if there are danger or warning alerts
          if (hasDanger || hasWarning) {
            const modal = document.getElementById('alertsModal');
            if (modal) {
              const shown = sessionStorage.getItem('alertsShown');
              if (!shown) {
                sessionStorage.setItem('alertsShown', '1');
                setTimeout(() => {
                  bootstrap.Modal.getOrCreateInstance(modal).show();
                }, 800);
              }
            }
          }
        }
      })
      .catch(() => {
        const body = document.getElementById('alertsBody');
        if (body) body.innerHTML = '<div class="text-muted small p-3">Could not load alerts.</div>';
      });
  }

  // Load alerts on every page
  if (document.getElementById('alertBellBtn')) {
    const isDashboard = document.body.dataset.page === 'dashboard';
    loadAlerts(isDashboard);
  }

  // Reload alerts when bell modal is opened
  const alertsModal = document.getElementById('alertsModal');
  if (alertsModal) {
    alertsModal.addEventListener('show.bs.modal', function () {
      loadAlerts(false);
    });
  }
});
