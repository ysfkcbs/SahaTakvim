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
  const fieldInput = document.getElementById('reservation_field_input');
  const fieldDisplay = document.getElementById('reservation_field_display');
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
    const fieldValue = fieldDisplay?.textContent?.trim() || 'Saha seçilmedi';
    reservationSummary.textContent = `${dateValue} • ${hourValue} • ${fieldValue} için rezervasyon oluşturuluyor.`;
  };

  if (modal) {
    modal.addEventListener('show.bs.modal', event => {
      const cell = event.relatedTarget;
      if (!cell || !cell.dataset) return;
      if (dateInput) dateInput.value = cell.dataset.date;
      if (hourInput) hourInput.value = cell.dataset.hour;
      const selectedField = cell.dataset.field || modal.dataset.selectedField;
      if (fieldInput && selectedField) {
        fieldInput.value = selectedField;
      }
      if (fieldDisplay) {
        fieldDisplay.textContent = modal.dataset.selectedFieldName || fieldDisplay.textContent;
      }
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

  const closingInputs = ['card_total_input', 'cash_total_input', 'iban_total_input']
    .map(id => document.getElementById(id))
    .filter(Boolean);
  const closingTotal = document.getElementById('daily_closing_total');
  const closingTotalSticky = document.getElementById('daily_closing_total_sticky');
  const closingModal = document.getElementById('dailyClosingModal');
  const closingDateInput = document.getElementById('closing_date_input');
  const closingNotesInput = document.getElementById('notes_input');
  const closingModalTitle = document.getElementById('dailyClosingModalTitle');
  const closingModalSummary = document.getElementById('daily_closing_modal_summary');
  const closingSubmit = document.getElementById('daily_closing_submit');

  const syncClosingTotal = () => {
    const total = closingInputs.reduce((sum, input) => sum + parseLocalizedNumber(input.value), 0);
    const formatted = formatCurrencyNumber(total);
    if (closingTotal) closingTotal.textContent = formatted;
    if (closingTotalSticky) closingTotalSticky.textContent = formatted;
    if (closingModalSummary && closingDateInput) {
      const dateText = closingDateInput.value || 'Tarih seçilmedi';
      closingModalSummary.textContent = `${dateText} için toplam ${formatted} TL.`;
    }
  };

  if (closingModal) {
    closingModal.addEventListener('show.bs.modal', event => {
      const trigger = event.relatedTarget;
      const mode = trigger?.dataset?.mode || 'new';
      const now = new Date();
      const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

      if (closingModalTitle) {
        closingModalTitle.textContent = mode === 'edit' ? 'Kapanış Kaydını Düzelt' : 'Yeni Kapanış Girişi';
      }
      if (closingSubmit) {
        closingSubmit.value = mode === 'edit' ? 'Güncelle' : 'Kaydet';
      }

      if (closingDateInput) closingDateInput.value = trigger?.dataset?.date || trigger?.dataset?.defaultDate || today;
      const cashInput = document.getElementById('cash_total_input');
      const cardInput = document.getElementById('card_total_input');
      const ibanInput = document.getElementById('iban_total_input');
      if (cashInput) cashInput.value = trigger?.dataset?.cash || '';
      if (cardInput) cardInput.value = trigger?.dataset?.card || '';
      if (ibanInput) ibanInput.value = trigger?.dataset?.iban || '';
      if (closingNotesInput) closingNotesInput.value = trigger?.dataset?.notes || '';

      syncClosingTotal();
    });
  }

  if (closingInputs.length && (closingTotal || closingTotalSticky)) {
    closingInputs.forEach(input => {
      input.addEventListener('input', syncClosingTotal);
      input.addEventListener('change', syncClosingTotal);
    });
    if (closingDateInput) closingDateInput.addEventListener('change', syncClosingTotal);

    syncClosingTotal();
  }

  const partnerModal = document.getElementById('partnerShareModal');
  if (partnerModal) {
    partnerModal.addEventListener('show.bs.modal', event => {
      const trigger = event.relatedTarget;
      const yearInput = document.getElementById('partner_share_year_input');
      const monthInput = document.getElementById('partner_share_month_input');
      const partnerInput = document.getElementById('partner_share_partner_input');
      const amountInput = document.getElementById('partner_share_amount_input');

      if (yearInput) yearInput.value = trigger?.dataset?.year || yearInput.value;
      if (monthInput && trigger?.dataset?.month) monthInput.value = trigger.dataset.month;
      if (partnerInput && trigger?.dataset?.partner) partnerInput.value = trigger.dataset.partner;
      if (amountInput) amountInput.value = trigger?.dataset?.amount || '';
    });
  }
});
