// static/inventario/js/lista_productos.js

$(function() {
  // ───────────────────────────────────────────────────────────────
  // 1) Apertura de modales vía AJAX
  //    Cualquier elemento con atributo data-remote="URL" y data-bs-target="#ModalID"
  //    cargará el contenido de la URL en el <div class="modal-content"> correspondiente.
  // ───────────────────────────────────────────────────────────────
  $('body').on('click', '[data-remote]', function(e) {
    e.preventDefault();

    // 1.a) URL a la que haremos la petición AJAX
    const url = $(this).data('remote');

    // 1.b) Determinar a qué modal vamos a cargar este contenido.
    //     Se pasa como data-bs-target="#modalRegistrarEntrada" (tal como en el HTML).
    let targetId = $(this).data('bsTarget');
    if (!targetId) {
      // fallback: si no existe data-bs-target como propiedad de data(), lo tomamos del atributo
      targetId = $(this).attr('data-bs-target');
    }

    // 1.c) Ubicamos dentro del modal el contenedor .modal-content donde vamos a insertar el formulario
    const $modalContent = $(`${targetId} .modal-content`);

    // 1.d) Mientras carga, mostrar mensaje
    $modalContent.html('<div class="p-4 text-center">Cargando…</div>');

    // 1.e) Petición AJAX GET y volcamos el resultado en modal-content
    $modalContent.load(url, function(response, status, xhr) {
      if (status !== 'success') {
        $modalContent.html('<div class="text-danger p-4">Error al cargar el formulario.</div>');
      } else {
        // Abrimos el modal (Bootstrap 5 / jQuery)
        $(targetId).modal('show');
      }
    });
  });


  // ───────────────────────────────────────────────────────────────
  // 2) “Auto‐submit” para filtros: al terminar de tipear o cambiar un select
  //    se envía el formulario automáticamente sin botón de “Filtrar”.
  // ───────────────────────────────────────────────────────────────
  const baseUrl = window.location.pathname;
  let typingTimer;
  const doneTypingInterval = 600; // milisegundos de espera antes de hacer submit
  const filterForm = document.getElementById('filterForm');

  // Si no existe form#filterForm, evitamos errores
  if (filterForm) {
    document.querySelectorAll('.auto-submit').forEach(field => {
      // Cuando el usuario deja de teclear durante doneTypingInterval, enviamos el formulario
      field.addEventListener('keyup', () => {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(() => filterForm.submit(), doneTypingInterval);
      });
      // Si cambia select, enviamos inmediatamente
      field.addEventListener('change', () => filterForm.submit());
    });

    // Función global para “Limpiar filtros” y recargar sin parámetros
    window.clearFilters = function() {
      filterForm.reset();
      window.location.href = baseUrl;
    };
  }
});
