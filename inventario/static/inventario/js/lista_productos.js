$(function() {
  $('body').on('click', '[data-remote]', function(e) {
    e.preventDefault();

    const url = $(this).data('remote');

    let targetId = $(this).data('bsTarget');
    if (!targetId) {
      targetId = $(this).attr('data-bs-target');
    }

    const $modalContent = $(`${targetId} .modal-content`);

    $modalContent.html('<div class="p-4 text-center">Cargando…</div>');

    $modalContent.load(url, function(response, status, xhr) {
      if (status !== 'success') {
        $modalContent.html('<div class="text-danger p-4">Error al cargar el formulario.</div>');
      } else {
        $(targetId).modal('show');
      }
    });
  });

  const baseUrl = window.location.pathname;
  let typingTimer;
  const doneTypingInterval = 600; 
  const filterForm = document.getElementById('filterForm');

  if (filterForm) {
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
  }
});

$('body').on('shown.bs.modal', '#modalEditarProducto', function() {
  $('.select2-tags').select2({
    theme: 'bootstrap4', 
    tags: true,
    placeholder: 'Escribe o selecciona una marca…',
    width: '100%',
    dropdownParent: $(this),
    minimumResultsForSearch: 0
  });
});