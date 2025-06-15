// inventario/static/inventario/js/formulario_entradas.js
$(function() {
  const $modal = $('#modalRegistrarEntrada');

  // 1) Al abrir el modal, asegurarnos de que la plantilla oculta NO muestre botones
  $modal.on('show.bs.modal', () => {
    const $tpl = $('#template-row');
    $tpl.find('.btn-nuevo-producto, .btn-eliminar-fila').hide();
  });

  // 2) Renombrar texto del botón principal
  $('#btn-agregar-fila').text('+ Agregar fila');

  // 3) Capturar submit del formulario de Crear Producto
  $(document).on('submit', '#modalCrearProducto form', function(e) {
    e.preventDefault();
    const $form = $(this);
    $.post($form.attr('action'), $form.serialize(), resp => {
      if (resp.success) {
        $('#modalCrearProducto').trigger('submitSuccess', resp);
      } else {
        // Sólo recargamos el cuerpo para no perder el footer
        $('#modalCrearProducto #modal-body-content').html(resp.html_form);
      }
    }).fail(() => alert('Error al crear producto. Intenta de nuevo.'));
  });

  // 4) AJAX submit de la Entrada
  function bindFormEntrada() {
    $(document).on('submit', '#form-entrada', function(e) {
      e.preventDefault();
      const $form = $(this);
      $.post($form.attr('action'), $form.serialize(), resp => {
        if (resp.success) {
          $modal.modal('hide');
          window.location = resp.redirect_url;
        } else {
          $('#entrada-form-fields').html(resp.html_form);
          bindAll();
        }
      }).fail(() => alert('Error de red. Intenta de nuevo.'));
    });
  }

  // 5) Agregar / eliminar filas
  function bindBtnsLinea() {
    // + Agregar fila
    $(document).on('click', '#btn-agregar-fila', function(e) {
      e.preventDefault();
      const $total = $('#id_form-TOTAL_FORMS');
      const idx = parseInt($total.val(), 10);

      // Clonar plantilla y preparar fila
      let $row = $($('#template-row').prop('outerHTML')
        .replace(/__INDEX__/g, idx));
      $row
        .removeAttr('id')
        .addClass('linea-form')
        .attr('data-index', idx)
        .show()               // quitar display:none
        .appendTo('#tabla-entradas tbody');

      // Limpiar inputs y mostrar botones
      $row.find('select, input[type="number"]').val('');
      $row.find('input[type="checkbox"]').prop('checked', false).hide();
      $row.find('.marca-cell, .color-cell, .modelo-cell, .serie-cell').text('');
      $row.find('.btn-nuevo-producto').show();    // botón al vuelo
      $row.find('.btn-eliminar-fila').show();     // botón eliminar

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

  // 6) Al cambiar de producto, rellenar celdas y ocultar botón “+ Nuevo Producto”
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

      // Ocultar el botón de creación de producto en esta fila
      $row.find('.btn-nuevo-producto').hide();
    });
  }

  // 7) “+ Nuevo Producto” por fila
  function bindNuevoProductoFila() {
    $(document).on('click', '.btn-nuevo-producto', function(e) {
      e.preventDefault();
      const $row = $(this).closest('tr.linea-form');
      $.get($(this).data('remote'), html => {
        $('#modalCrearProducto .modal-content').html(html);
        $('#modalCrearProducto').modal('show')
          .one('submitSuccess', (evt, data) => {
            // Insertar opción y dispara change
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

  // 8) “+ Nuevo Producto” global
  function bindNuevoProductoGeneral() {
    $(document).on('click', '#btn-nuevo-producto-general', function(e) {
      e.preventDefault();
      $.get($(this).data('remote'), html => {
        $('#modalCrearProducto .modal-content').html(html);
        $('#modalCrearProducto').modal('show')
          .one('submitSuccess', (evt, data) => {
            // Añade fila vacía
            $('#btn-agregar-fila').click();
            const $last = $('#tabla-entradas tbody tr.linea-form:visible').last();
            // Preseleccionar y dispara change
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

  // 9) Inicializar todos los bindings
  function bindAll() {
    bindFormEntrada();
    bindBtnsLinea();
    bindListenerCambioProducto();
    bindNuevoProductoFila();
    bindNuevoProductoGeneral();
  }

  bindAll();
});