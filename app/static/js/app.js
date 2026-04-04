document.addEventListener('DOMContentLoaded', () => {
  const isStandalone =
    window.matchMedia?.('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;
  document.body.classList.toggle('is-standalone', Boolean(isStandalone));

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js').catch(() => {
        // Minimal PWA setup: fail silently if service worker registration is unavailable.
      });
    });
  }

  const parseLocalizedNumber = value => {
    if (!value) return 0;
    let text = String(value).trim().replace(/\s+/g, '');
    if (!text) return 0;
    const hasDot = text.includes('.');
    const hasComma = text.includes(',');
    if (hasDot && hasComma) {
      if (text.lastIndexOf(',') > text.lastIndexOf('.')) {
        text = text.replace(/\./g, '').replace(',', '.');
      } else {
        text = text.replace(/,/g, '');
      }
    } else if (hasComma) {
      text = text.replace(',', '.');
    }
    const parsed = Number(text);
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const formatCurrencyNumber = value =>
    new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);

  const modal = document.getElementById('reservationModal');
  const dateInput = document.getElementById('reservation_date_input');
  const hourInput = document.getElementById('reservation_hour_input');
  const reservationTypeInput = document.getElementById('reservation_type_input');
  const reservationSummary = document.getElementById('reservation_summary');

  const syncReservationTypeButtons = () => {
    if (!reservationTypeInput) return;
    document.querySelectorAll('.reservation-type-btn').forEach(button => {
      button.classList.toggle('is-active', button.dataset.reservationType === reservationTypeInput.value);
    });
  };

  const syncReservationSummary = () => {
    if (!reservationSummary || !dateInput || !hourInput) return;
    const dateValue = dateInput.value || 'Tarih seçilmedi';
    const hourValue = hourInput.options[hourInput.selectedIndex]?.text || hourInput.value || 'Saat seçilmedi';
    reservationSummary.textContent = `${dateValue} • ${hourValue} için rezervasyon oluşturuluyor.`;
  };

  if (modal) {
    modal.addEventListener('show.bs.modal', event => {
      const cell = event.relatedTarget;
      if (!cell || !cell.dataset) return;
      if (dateInput) dateInput.value = cell.dataset.date;
      if (hourInput) hourInput.value = cell.dataset.hour;
      syncReservationSummary();
      syncReservationTypeButtons();
    });
  }

  document.querySelectorAll('.reservation-type-btn').forEach(button => {
    button.addEventListener('click', () => {
      if (!reservationTypeInput) return;
      reservationTypeInput.value = button.dataset.reservationType || reservationTypeInput.value;
      syncReservationTypeButtons();
    });
  });

  if (dateInput) dateInput.addEventListener('change', syncReservationSummary);
  if (hourInput) hourInput.addEventListener('change', syncReservationSummary);
  syncReservationSummary();
  syncReservationTypeButtons();

  const dayTabs = Array.from(document.querySelectorAll('[data-day-tab]'));
  const dayPanels = Array.from(document.querySelectorAll('[data-day-panel]'));
  if (dayTabs.length && dayPanels.length) {
    const activateDay = index => {
      dayTabs.forEach(tab => {
        const isActive = tab.dataset.dayTab === String(index);
        tab.classList.toggle('is-active', isActive);
        tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
      });
      dayPanels.forEach(panel => {
        panel.classList.toggle('is-active', panel.dataset.dayPanel === String(index));
      });
    };

    dayTabs.forEach(tab => {
      tab.addEventListener('click', () => activateDay(tab.dataset.dayTab));
    });
  }

  document.querySelectorAll('.slot-edit-icon, .mobile-slot-edit').forEach(link => {
    link.addEventListener('click', event => {
      event.stopPropagation();
    });
  });

  const currentPath = window.location.pathname;
  document.querySelectorAll('.mobile-bottom-link').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    if (href === '/') {
      if (currentPath === '/') link.classList.add('is-active');
      return;
    }
    if (currentPath.startsWith(href)) link.classList.add('is-active');
  });

  const closingInputs = ['card_total_input', 'cash_total_input', 'iban_total_input']
    .map(id => document.getElementById(id))
    .filter(Boolean);
  const closingTotal = document.getElementById('daily_closing_total');
  const closingTotalSticky = document.getElementById('daily_closing_total_sticky');

  if (closingInputs.length && (closingTotal || closingTotalSticky)) {
    const syncClosingTotal = () => {
      const total = closingInputs.reduce((sum, input) => sum + parseLocalizedNumber(input.value), 0);
      const formatted = formatCurrencyNumber(total);
      if (closingTotal) closingTotal.textContent = formatted;
      if (closingTotalSticky) closingTotalSticky.textContent = formatted;
    };

    closingInputs.forEach(input => {
      input.addEventListener('input', syncClosingTotal);
      input.addEventListener('change', syncClosingTotal);
    });

    syncClosingTotal();
  }
});
