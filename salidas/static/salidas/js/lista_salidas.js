$(function(){
  const filterForm = document.getElementById('filterForm');
  let typingTimer;
  const doneTyping = 300;

  // Init Select2 en solicitante, unidad, departamento y producto
  $('.select2-solicitante, .select2-unidad, .select2-departamento, .select2-producto')
    .select2({ theme: 'bootstrap4', width: '100%' })
    .on('change', function(){
      console.log('Filtro change:', $(this).attr('name'), $(this).val());
      filterForm.submit();
    });

  // Auto‐submit para el input de folio
  if (filterForm) {
    $(filterForm).find('input.auto-submit').on('keyup', function(){
      clearTimeout(typingTimer);
      typingTimer = setTimeout(()=> filterForm.submit(), doneTyping);
    });
  }

  // Limpiar filtros
  window.clearFilters = function(){
    filterForm.reset();
    window.location.href = window.location.pathname;
  };

  // Captura clicks en cada acción (sin interferir con dropdown)
  $('table').on('click', '.dropdown-item', function(e){
    e.preventDefault();
    const acción = $(this).data('action');
    const id     = $(this).data('id');
    console.log('Acción:', acción, 'ID:', id);
  });

  // Helper para obtener el CSRF token de la cookie (Django)
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      document.cookie.split(';').forEach(cookie => {
        const c = cookie.trim();
        if (c.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(c.substring(name.length + 1));
        }
      });
    }
    return cookieValue;
  }

  // Handler AJAX para marcar un vale como entregado
  $('table').on('click', '.btn-entregar', function(e) {
    e.preventDefault();
    const url = $(this).data('url');

    $.ajax({
      url: url,
      type: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCookie('csrftoken')
      },
      success(response) {
        if (response.success) {
          // recarga para ver el nuevo estado
          location.reload();
        } else {
          alert(response.error || 'No se pudo marcar como entregado.');
        }
      },
      error() {
        alert('Error en la petición de entrega.');
      }
    });
  });

  // Handler para abrir modal de cancelación
  $('table').on('click', '.btn-cancelar', function(e) {
    e.preventDefault();
    const url = $(this).data('url');
    // Carga el fragmento con el form en el modal
    $('#modalCancelar .modal-content').load(url, function() {
      // BS4: mostrar el modal vía jQuery
      $('#modalCancelar').modal('show');
    });
  });

  // Handler para enviar cancelación
  $(document).on('submit', '#form-cancelar', function(e) {
    e.preventDefault();
    const $form = $(this);
    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      data: $form.serialize(),
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCookie('csrftoken')
      },
      success(response) {
        if (response.success) {
          // BS4: cerrar modal y recargar para ver el mensaje
          $('#modalCancelar').modal('hide');
          location.reload();
        } else {
          alert(response.error || 'Error al cancelar el vale.');
        }
      },
      error() {
        alert('Error en la petición de cancelación.');
      }
    });
  });
});
