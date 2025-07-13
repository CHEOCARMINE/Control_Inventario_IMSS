// salidas/static/salidas/js/lista_salidas.js
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
});
