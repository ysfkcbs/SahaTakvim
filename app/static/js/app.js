document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('reservationModal');
  if (!modal) return;
  modal.addEventListener('show.bs.modal', event => {
    const cell = event.relatedTarget;
    if (!cell || !cell.dataset) return;
    const dateInput = document.getElementById('reservation_date_input');
    const hourInput = document.getElementById('reservation_hour_input');
    if (dateInput) dateInput.value = cell.dataset.date;
    if (hourInput) hourInput.value = cell.dataset.hour;
  });
});
