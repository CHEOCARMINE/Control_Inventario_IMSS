// URL base para limpiar filtros
const baseUrl = window.location.pathname;

// auto-submit con debounce
let typingTimer;
const doneTypingInterval = 600;
const filterForm = document.getElementById('filterForm');

document.querySelectorAll('.auto-submit').forEach(field => {
  field.addEventListener('keyup', () => {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => filterForm.submit(), doneTypingInterval);
  });

  field.addEventListener('change', () => filterForm.submit());
});

function clearFilters() {
  filterForm.reset();
  window.location.href = baseUrl;
}
