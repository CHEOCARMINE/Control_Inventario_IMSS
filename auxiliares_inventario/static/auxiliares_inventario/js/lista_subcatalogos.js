$(function() {
  // Librerías de filtrado auto-submit 
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

  // Función de inicialización de Select2 para el campo Categoría
  function initSelect2Catalogo($container) {
    $container.find('.select2-catalogo').select2({
      theme: 'bootstrap4',
      placeholder: 'Selecciona categoría…',
      width: '100%',
      dropdownParent: $container.closest('.modal'),
      minimumResultsForSearch: 0
    });
  }

  // Función de binding para el form de Subcategoría (captura submit y refresca con AJAX)
  function bindFormSubcatalogo($container) {
    // Si no pasan $container, tomamos el modal completo
    const $ctx = $container || $('#modal .modal-content');

    $ctx.find('#form-subcatalogo')
      .off('submit')
      .on('submit', function(e) {
        e.preventDefault();
        const form = $(this);

        $.ajax({
          type: 'POST',
          url: form.attr('action'),
          data: form.serialize(),
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).done(res => {
          if (res.success) {
            // Éxito: ocultar modal y recargar página
            $('#modal').modal('hide');
            window.location = res.redirect_url;
          } else {
            // Error de validación: reinyectar HTML
            $('#modal .modal-content').html(res.html_form);
            // volver a inicializar Select2 y el handler de submit
            initSelect2Catalogo($('#modal .modal-content'));
            bindFormSubcatalogo($('#modal .modal-content'));
          }
        }).fail(() => {
          alert('Error de red. Intenta de nuevo.');
        });
      });
  }

  // Handler para abrir el modal (GET) y cargar el formulario
  $('body').on('click', '[data-remote]', function(e) {
    e.preventDefault();
    const url = $(this).data('remote');
    const $mc = $('#modal .modal-content')
      .html('<div class="p-4 text-center">Cargando…</div>');

    $mc.load(url, function(response, status) {
      if (status !== 'success') {
        $mc.html('<div class="text-danger p-4">Error al cargar el formulario.</div>');
      } else {
        // Una vez cargado con éxito:
        initSelect2Catalogo($mc);
        bindFormSubcatalogo($mc);
        $('#modal').modal('show');
      }
    });
  });

  // Inicializa el binding al arrancar la página (por si el modal ya está en el DOM)
  bindFormSubcatalogo($('#modal .modal-content'));
});
