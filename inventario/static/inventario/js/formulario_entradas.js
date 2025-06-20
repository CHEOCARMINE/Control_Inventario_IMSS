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
      const $row = $($('#template-row').prop('outerHTML').replace(/__INDEX__/g, idx))
        .removeAttr('id').addClass('linea-form')
        .attr('data-index', idx).show()
        .appendTo('#tabla-entradas tbody');
      // limpia
      $row.find('select, input[type="number"]').val('');
      $row.find('input[type="checkbox"]').prop('checked', false).hide();
      $row.find('.marca-cell, .color-cell, .modelo-cell, .serie-cell').text('');
      $row.find('.btn-nuevo-producto, .btn-eliminar-fila').show();
      $total.val(idx + 1);
      initSelect2Productos($row);
    });
    // × Eliminar fila
    $(document).on('click', '.btn-eliminar-fila', function(e) {
      e.preventDefault();
      const $row = $(this).closest('tr.linea-form'),
            $del = $row.find('input[name$="-DELETE"]');
      if ($del.length) { $del.prop('checked', true); $row.hide(); }
      else { $row.remove(); }
      // reindexa
      $('#tabla-entradas tbody tr.linea-form:visible').each((i, tr) => {
        const $tr = $(tr).attr('data-index', i);
        $tr.find('select, input').each(function() {
          const old = this.name||'', neu = old.replace(/-\d+-/, `-${i}-`);
          $(this).attr({ name: neu, id: 'id_' + neu });
        });
      });
      $('#id_form-TOTAL_FORMS').val($('#tabla-entradas tbody tr.linea-form:visible').length);
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
  $(document).off('click', '.btn-nuevo-producto');
  $(document).on('click', '.btn-nuevo-producto', function(e) {
    e.preventDefault();
    const $row   = $(this).closest('tr.linea-form');
    const $modal = $('#modalCrearProducto');

    $.get($(this).data('remote'), html => {
      // Inyecta el formulario completo
      $modal.find('.modal-content').html(html);
      // Inicializa Select2 en marca y tipo **antes** de mostrar
      initSelect2ProductoModal($modal);
      // Muestra el modal
      $modal.modal('show')
        .one('submitSuccess', (evt, data) => {
          const opt = new Option(data.producto_label, data.producto_id, true, true);
          $(opt).attr({
            'data-marca':  data.producto_marca,
            'data-color':  data.producto_color,
            'data-modelo': data.producto_modelo,
            'data-serie':  data.producto_serie
          });
          // Añade al select de la fila y dispara change para rellenar datos
          $row.find('select[name$="-producto"]')
              .append(opt)
              .trigger('change');
          $modal.modal('hide');
        });
    });
  });
}

// “+ Nuevo Producto” global
function bindNuevoProductoGeneral() {
  $(document).off('click', '#btn-nuevo-producto-general');
  $(document).on('click', '#btn-nuevo-producto-general', function(e) {
    e.preventDefault();
    const $modal = $('#modalCrearProducto');

    $.get($(this).data('remote'), html => {
      // Inyecta formulario
      $modal.find('.modal-content').html(html);
      // Inicializa Select2
      initSelect2ProductoModal($modal);
      // Muestra modal
      $modal.modal('show')
        .one('submitSuccess', (evt, data) => {
          // Al crear exitoso, añade nueva fila
          $('#btn-agregar-fila').click();
          const $last = $('#tabla-entradas tbody tr.linea-form:visible').last();
          const opt = new Option(data.producto_label, data.producto_id, true, true);
          $(opt).attr({
            'data-marca':  data.producto_marca,
            'data-color':  data.producto_color,
            'data-modelo': data.producto_modelo,
            'data-serie':  data.producto_serie
          });
          $last.find('select[name$="-producto"]')
                .append(opt)
                .trigger('change');
          $modal.modal('hide');
        });
    });
  });
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