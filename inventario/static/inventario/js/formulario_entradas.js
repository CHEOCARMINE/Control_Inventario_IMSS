$(function() {
  // Init Select2 para Marca y Tipo en modales de Producto
  function initSelect2ProductoModal($modal) {
    // Marca (tags)
    $modal.find('.select2-tags').each(function() {
      const $sel = $(this);
      if ($sel.hasClass('select2-hidden-accessible')) return;
      $sel.select2({
        theme: 'bootstrap4',
        tags: true,
        placeholder: $sel.data('placeholder') || 'Escribe o selecciona una marca…',
        width: '100%',
        dropdownParent: $modal,
        minimumResultsForSearch: 0,
        closeOnSelect: true
      }).on('select2:select', () => $sel.select2('close'));
    });
    // Tipo (select simple)
    $modal.find('.select2-tipo').each(function() {
      const $sel = $(this);
      if ($sel.hasClass('select2-hidden-accessible')) return;
      $sel.select2({
        theme: 'bootstrap4',
        placeholder: 'Selecciona un tipo…',
        width: '100%',
        dropdownParent: $modal,
        minimumResultsForSearch: 0,
        closeOnSelect: true
      }).on('select2:select', () => $sel.select2('close'));
    });
  }

  // Al mostrar modal Crear/Editar Producto
  $('body').on('shown.bs.modal', '#modalCrearProducto, #modalEditarProducto', function() {
    initSelect2ProductoModal($(this));
  });

  // Capturar submit Crear/Editar Producto y reinit Select2
  $(document)
    .off('submit', '#form-producto, #form-editar-producto')
    .on('submit', '#form-producto, #form-editar-producto', function(e) {
      e.preventDefault();
      const $form  = $(this),
            $modal = $form.closest('.modal');
      $.post($form.attr('action'), $form.serialize(), resp => {
        if (resp.success) {
          if ($form.is('#form-producto')) {
            $modal.trigger('submitSuccess', resp);
          } else {
            window.location = resp.redirect_url;
          }
        } else {
          // sólo reemplazar el body para conservar header+footer
          $modal.find('#modal-body-content').html(resp.html_form);
          initSelect2ProductoModal($modal);
        }
      }).fail(() => {
        alert('Error de red al crear/editar producto. Intenta de nuevo.');
      });
    });

 // Init Select2 para Productos en el formset
function initSelect2Productos($scope) {
  $scope.find('.select2-producto-auto').each(function() {
    const $sel = $(this);
    if ($sel.hasClass('select2-hidden-accessible')) return;

    $sel.select2({
      theme: 'bootstrap4',
      placeholder: $sel.data('placeholder') || 'Selecciona producto…',
      allowClear: true,
      closeOnSelect: true,
      width: '100%',
      dropdownParent: $scope.closest('.modal'),
      minimumResultsForSearch: 0
    });

    // Al seleccionar o deseleccionar, re-filtra duplicados y cierra
    $sel.on('select2:select select2:unselect', () => {
      updateProductoOptions();
      $sel.select2('close');
    });
  });
  // Primera pasada de filtrado
  updateProductoOptions();
}

// Filtrar duplicados deshabilitando opciones
function updateProductoOptions() {
  // lista de ids seleccionados
  const selected = $('.linea-form:visible .select2-producto-auto')
    .map((_, el) => $(el).val())
    .get()
    .filter(v => v);
  $('.select2-producto-auto').each(function() {
    const $sel = $(this),
          me  = $sel.val();
    // reactiva todas primero
    $sel.find('option').prop('disabled', false);
    // deshabilita las que otro select ya eligió
    selected.forEach(val => {
      if (val && val !== me) {
        $sel.find(`option[value="${val}"]`).prop('disabled', true);
      }
    });
    // refresca la UI de Select2
    $sel.trigger('change.select2');
  });
}

// Tras abrir el modal
$('#modalRegistrarEntrada').on('shown.bs.modal', () => {
  initSelect2Productos($('#tabla-entradas tbody'));
});
// Tras añadir cada fila
$('#btn-agregar-fila').on('click', function() {
  initSelect2Productos($newRow);
});

  // Al mostrar modal Registrar Entrada
  const $modalEntrada = $('#modalRegistrarEntrada');
  $modalEntrada
    .on('shown.bs.modal', () => initSelect2Productos($('#tabla-entradas tbody')))
    .on('show.bs.modal', () => $('#template-row').find('.btn-nuevo-producto, .btn-eliminar-fila').hide());
  $('#btn-agregar-fila').text('+ Agregar fila');

  // Submit AJAX de la Entrada
  function bindFormEntrada() {
    $(document).on('submit', '#form-entrada', function(e) {
      e.preventDefault();
      const $form = $(this);
      $.post($form.attr('action'), $form.serialize(), resp => {
        if (resp.success) {
          $modalEntrada.modal('hide');
          window.location = resp.redirect_url;
        } else {
          $('#entrada-form-fields').html(resp.html_form);
          bindAll();
        }
      }).fail(() => alert('Error de red. Intenta de nuevo.'));
    });
  }

  // Agregar / eliminar filas
  function bindBtnsLinea() {
    // + Agregar fila
  $(document).on('click', '#btn-agregar-fila', function(e) {
    e.preventDefault();
    const $total = $('#id_form-TOTAL_FORMS'),
          idx    = parseInt($total.val(), 10);
    const $row = $($('#template-row').prop('outerHTML')
                  .replace(/__INDEX__/g, idx))
      .removeAttr('id')
      .addClass('linea-form')
      .attr('data-index', idx)
      .show()
      .appendTo('#tabla-entradas tbody');
    // Limpia inputs / select
    $row.find('select, input[type="number"]').val('');
    // Elimina cualquier checkbox de DELETE heredado
    $row.find('input[name$="-DELETE"]').remove();
    $row.find('.marca-cell, .color-cell, .modelo-cell, .serie-cell').text('');
    $row.find('.btn-nuevo-producto, .btn-eliminar-fila').show();
    // Actualiza contador
    $total.val(idx + 1);
    // Inicia Select2 en esta nueva fila
    initSelect2Productos($row);
  });
    // × Eliminar fila
  $(document).on('click', '.btn-eliminar-fila', function(e) {
    e.preventDefault();
    $(this).closest('tr.linea-form').remove();
    // Reordena índices y TOTAL_FORMS
    reorderRows();
    updateProductoOptions();
  });
}

  // Rellenar celdas y filtrar duplicados al cambiar producto
  function bindListenerCambioProducto() {
    // Cuando seleccionas un item en el dropdown de Select2
    $(document).off('select2:select', '.select2-producto-auto')
      .on('select2:select', '.select2-producto-auto', function() {
        const $sel  = $(this),
              data  = $sel.find(':selected').data(),
              $row  = $sel.closest('tr.linea-form');
        // rellena las celdas
        $row.find('.marca-cell').text(data.marca  || '');
        $row.find('.color-cell').text(data.color  || '');
        $row.find('.modelo-cell').text(data.modelo || '');
        $row.find('.serie-cell').text(data.serie || '');
        $row.find('.btn-nuevo-producto').hide();
        // cierra el dropdown
        $sel.select2('close');
        // vuelve a filtrar duplicados
        updateProductoOptions();
      });
    // Si usas allowClear tú también debes escuchar el evento clear
    $(document).off('select2:clear', '.select2-producto-auto')
      .on('select2:clear', '.select2-producto-auto', function() {
        updateProductoOptions();
      });
  }

// “+ Nuevo Producto” por fila
function bindNuevoProductoFila() {
  const $modal = $('#modalCrearProducto');
  $(document).off('click', '.btn-nuevo-producto');
  $(document).on('click', '.btn-nuevo-producto', function(e) {
    e.preventDefault();
    const $row = $(this).closest('tr.linea-form');
    const url  = $(this).data('remote');
    $.get(url, html => {
      // Inyecta el form en el modal y prepara Select2
      $modal.find('.modal-content').html(html);
      initSelect2ProductoModal($modal);
      $modal.modal('show')
        .one('submitSuccess', (evt, data) => {
          // atributos del producto
          const val   = data.producto_id;
          const txt   = data.producto_label;
          const attrs = {
            'data-marca':  data.producto_marca,
            'data-color':  data.producto_color,
            'data-modelo': data.producto_modelo,
            'data-serie':  data.producto_serie || ''
          };
          // Creamos el <option> nuevo
          const opt = new Option(txt, val, false, false);
          Object.entries(attrs)
            .forEach(([k, v]) => opt.setAttribute(k, v));
          // Lo añadimos a todos los selects (incluida la plantilla oculta)
          $('.select2-producto-auto').each(function() {
            const $s = $(this);
            $s.append(opt.cloneNode(true));
            $s.trigger('change.select2');
          });
          // Ocultamos “+ Nuevo Producto” en esta fila
          $row.find('.btn-nuevo-producto').hide();
          // Desmarcamos cualquier DELETE heredado y lo ocultamos
          const $del = $row.find('input[name$="-DELETE"]');
          $del.prop('checked', false).hide();
          // Seleccionamos la nueva opción en el <select> de la fila
          const $sel = $row.find('select[name$="-producto"]');
          $sel.val(val).trigger('change.select2');
          // Rellenamos ya las celdas de marca/color/modelo/serie
          $row.find('.marca-cell').text(attrs['data-marca']);
          $row.find('.color-cell').text(attrs['data-color']);
          $row.find('.modelo-cell').text(attrs['data-modelo']);
          $row.find('.serie-cell').text(attrs['data-serie']);
          // Refresca el bloqueo de duplicados
          updateProductoOptions();
          // Reindexa todas las filas y actualiza TOTAL_FORMS
          reorderRows();
          // Cierra el modal
          $modal.modal('hide');
        });
    });
  });
}

// “+ Nuevo Producto” global
function bindNuevoProductoGeneral() {
  const $modal = $('#modalCrearProducto');
  $(document).off('click', '#btn-nuevo-producto-general')
    .on('click', '#btn-nuevo-producto-general', function(e) {
      e.preventDefault();
      const url = $(this).data('remote');
      $.get(url, html => {
        // Inyecta el formulario y muestra el modal
        $modal.find('.modal-content').html(html);
        initSelect2ProductoModal($modal);
        $modal.modal('show')
          .one('submitSuccess', (evt, data) => {
            // Crea una nueva fila
            $('#btn-agregar-fila').click();
            const $row = $('#tabla-entradas tbody tr.linea-form:visible').last();
            const val   = data.producto_id;
            const txt   = data.producto_label;
            const attrs = {
              'data-marca':  data.producto_marca,
              'data-color':  data.producto_color,
              'data-modelo': data.producto_modelo,
              'data-serie':  data.producto_serie || ''
            };
            // Construye el <option> nuevo
            const opt = new Option(txt, val, false, false);
            Object.entries(attrs).forEach(([k, v]) => opt.setAttribute(k, v));
            // Añádelo a todos los selects y refresca Select2
            $('.select2-producto-auto').each(function() {
              const $s = $(this);
              $s.append(opt.cloneNode(true));
              $s.trigger('change.select2');
            });
            // Oculta el botón sólo en esta nueva fila
            $row.find('.btn-nuevo-producto').hide();
            // Limpia el checkbox DELETE heredado
            $row.find('input[name$="-DELETE"]')
                .prop('checked', false)
                .hide();
            // Selecciona y rellena la fila
            const $sel = $row.find('select[name$="-producto"]');
            $sel.val(val).trigger('change.select2');
            $row.find('.marca-cell').text(attrs['data-marca']);
            $row.find('.color-cell').text(attrs['data-color']);
            $row.find('.modelo-cell').text(attrs['data-modelo']);
            $row.find('.serie-cell').text(attrs['data-serie']);
            // Actualiza bloqueo de duplicados
            updateProductoOptions();
            // Reindexa filas y TOTAL_FORMS
            reorderRows();
            // Cierra el modal
            $modal.modal('hide');
          });
      });
    });
}

// Reordena los índices de fila y actualiza TOTAL_FORMS
function reorderRows() {
  const $rows = $('#tabla-entradas tbody tr.linea-form:visible');
  $rows.each((i, tr) => {
    const $tr = $(tr).attr('data-index', i);
    // Solo reindexa selects y cantidad
    $tr.find('select, input[type="number"]').each(function() {
      const old = this.name;
      const neu = old.replace(/-\d+-/, `-${i}-`);
      $(this).attr({ name: neu, id: 'id_' + neu });
    });
  });
  $('#id_form-TOTAL_FORMS').val($rows.length);
}

  // Bind all
  function bindAll() {
    bindFormEntrada();
    bindBtnsLinea();
    bindListenerCambioProducto();
    bindNuevoProductoFila();
    bindNuevoProductoGeneral();
  }
  bindAll();
});