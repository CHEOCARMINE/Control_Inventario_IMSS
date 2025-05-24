$(function() {
  // Abrir el modal y cargar via AJAX el formulario (GET)
  $('body').on('click', '[data-remote]', function(e) {
    e.preventDefault();
    const url = $(this).data('remote');
    $('#modal .modal-content')
      .html('<div class="p-4 text-center">Cargando…</div>')
      .load(url, function(response, status) {
        if (status !== 'success') {
          $(this).html('<div class="text-danger p-4">Error al cargar el formulario.</div>');
        } else {
          $('#modal').modal('show');
        }
      });
  });

  // Filtros auto-submit
  const baseUrl = window.location.pathname;
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

  window.clearFilters = function() {
    filterForm.reset();
    window.location.href = baseUrl;
  };
});
