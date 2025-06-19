$(function() {
  // Función de inicialización de Select2 para Marca y Tipo
  function initSelect2ProductoModal($modal) {
    $modal.find('.select2-tags').select2({
      theme: 'bootstrap4',
      tags: true,
      placeholder: $modal.find('.select2-tags').data('placeholder') || 'Escribe o selecciona una marca…',
      width: '100%',
      dropdownParent: $modal,
      minimumResultsForSearch: 0
    });
    $modal.find('.select2-tipo').select2({
      theme: 'bootstrap4',
      placeholder: 'Selecciona un tipo…',
      width: '100%',
      dropdownParent: $modal,
      minimumResultsForSearch: 0
    });
  }

  // Al mostrar el modal Crear/Editar Producto 
  $('body').on('shown.bs.modal', '#modalCrearProducto, #modalEditarProducto', function(){
    initSelect2ProductoModal($(this));
  });

  // Capturar submit de Crear/Editar Producto y reinyectar con Select2 
  $(document)
    .off('submit', '#form-producto, #form-editar-producto')
    .on('submit', '#form-producto, #form-editar-producto', function(e) {
      e.preventDefault();
      const $form  = $(this);
      const $modal = $form.closest('.modal');

      $.post($form.attr('action'), $form.serialize(), resp => {
        if (resp.success) {
          // Si es creación, disparar evento; si es edición, redirigir
          if ($form.is('#form-producto')) {
            $modal.trigger('submitSuccess', resp);
          } else {
            window.location = resp.redirect_url;
          }
        } else {
          // Reemplaza TODO el modal-content
          $modal.find('.modal-content').html(resp.html_form);
          // Re-inicializa Select2
          initSelect2ProductoModal($modal);
        }
      }).fail(() => {
        alert('Error de red al crear/editar producto. Intenta de nuevo.');
      });
    });

  // Lógica de Entradas 
  const $modalEntrada = $('#modalRegistrarEntrada');

  // Ocultar botones en plantilla oculta
  $modalEntrada.on('show.bs.modal', () => {
    $('#template-row').find('.btn-nuevo-producto, .btn-eliminar-fila').hide();
  });

  // Cambia texto de "+ Agregar fila"
  $('#btn-agregar-fila').text('+ Agregar fila');

  // AJAX submit de la Entrada
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
      const $total = $('#id_form-TOTAL_FORMS');
      const idx = parseInt($total.val(), 10);
      let $row = $($('#template-row').prop('outerHTML').replace(/__INDEX__/g, idx));
      $row.removeAttr('id')
          .addClass('linea-form')
          .attr('data-index', idx)
          .show()
          .appendTo('#tabla-entradas tbody');
      $row.find('select, input[type="number"]').val('');
      $row.find('input[type="checkbox"]').prop('checked', false).hide();
      $row.find('.marca-cell, .color-cell, .modelo-cell, .serie-cell').text('');
      $row.find('.btn-nuevo-producto, .btn-eliminar-fila').show();
      $total.val(idx + 1);
    });

    // × Eliminar fila
    $(document).on('click', '.btn-eliminar-fila', function(e) {
      e.preventDefault();
      const $row = $(this).closest('tr.linea-form');
      const $del = $row.find('input[name$="-DELETE"]');
      if ($del.length) {
        $del.prop('checked', true);
        $row.hide();
      } else {
        $row.remove();
      }
      // Reindexar
      $('#tabla-entradas tbody tr.linea-form:visible').each((i, tr) => {
        const $tr = $(tr).attr('data-index', i);
        $tr.find('select, input').each(function() {
          const old = this.name || '';
          const neu = old.replace(/-\d+-/, `-${i}-`);
          $(this).attr({ name: neu, id: 'id_' + neu });
        });
      });
      $('#id_form-TOTAL_FORMS').val($('#tabla-entradas tbody tr.linea-form:visible').length);
    });
  }

  // Al cambiar de producto, rellenar celdas y ocultar "+ Nuevo Producto"
  function bindListenerCambioProducto() {
    $(document).on('change', '.select-producto-auto', function() {
      const $sel = $(this);
      const $opt = $sel.find(':selected');
      const props = {
        marca:  $opt.data('marca')  || '',
        color:  $opt.data('color')  || '',
        modelo: $opt.data('modelo') || '',
        serie:  $opt.data('serie')  || ''
      };
      const $row = $sel.closest('tr.linea-form');
      $row.find('.marca-cell').text(props.marca);
      $row.find('.color-cell').text(props.color);
      $row.find('.modelo-cell').text(props.modelo);
      $row.find('.serie-cell').text(props.serie);
      $row.find('.btn-nuevo-producto').hide();
    });
  }

  // “+ Nuevo Producto” por fila
  function bindNuevoProductoFila() {
    $(document).off('click', '.btn-nuevo-producto');
    $(document).on('click', '.btn-nuevo-producto', function(e) {
      e.preventDefault();
      const $row = $(this).closest('tr.linea-form');
      $.get($(this).data('remote'), html => {
        $('#modalCrearProducto .modal-content').html(html);
        $('#modalCrearProducto').modal('show')
          .one('submitSuccess', (evt, data) => {
            const opt = new Option(data.producto_label, data.producto_id, true, true);
            $(opt).attr({
              'data-marca':  data.producto_marca,
              'data-color':  data.producto_color,
              'data-modelo': data.producto_modelo,
              'data-serie':  data.producto_serie
            });
            $row.find('select[name$="-producto"]').append(opt).trigger('change');
            $('#modalCrearProducto').modal('hide');
          });
      });
    });
  }

  // “+ Nuevo Producto” global
  function bindNuevoProductoGeneral() {
    $(document).off('click', '#btn-nuevo-producto-general');
    $(document).on('click', '#btn-nuevo-producto-general', function(e) {
      e.preventDefault();
      $.get($(this).data('remote'), html => {
        $('#modalCrearProducto .modal-content').html(html);
        $('#modalCrearProducto').modal('show')
          .one('submitSuccess', (evt, data) => {
            $('#btn-agregar-fila').click();
            const $last = $('#tabla-entradas tbody tr.linea-form:visible').last();
            const opt = new Option(data.producto_label, data.producto_id, true, true);
            $(opt).attr({
              'data-marca':  data.producto_marca,
              'data-color':  data.producto_color,
              'data-modelo': data.producto_modelo,
              'data-serie':  data.producto_serie
            });
            $last.find('select[name$="-producto"]').append(opt).trigger('change');
            $('#modalCrearProducto').modal('hide');
          });
      });
    });
  }

  // Inicializar todos los bindings de Entradas
  function bindAll() {
    bindFormEntrada();
    bindBtnsLinea();
    bindListenerCambioProducto();
    bindNuevoProductoFila();
    bindNuevoProductoGeneral();
  }
  bindAll();

}); 