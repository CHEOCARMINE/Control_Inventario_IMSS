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
      if ($sel.prop('disabled')) {
        $sel.select2('enable', false);
      }
    });
    // Tipo 
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
      if ($sel.prop('disabled')) {
        $sel.select2('enable', false);
      }
    });
  }

  // Al mostrar modal Crear/Editar Producto
  $(document).on('shown.bs.modal', '#modalCrearProducto, #modalEditarProducto', function() {
    const $m      = $(this);
    const $field  = $m.find('[name="tiene_serie"]');      
    const $rowTS  = $field.closest('.col-md-6.mb-3');     
    const $rowNum = $m.find('#div_numero_serie').closest('.row');
    initSelect2ProductoModal($m);

    // función que decide qué mostrar
    function actualizarVista() {
      const esSelect = $field.is('select');
      const esHijo   = !esSelect; 
      if (esHijo) {
        // caso hijo: ocultar “¿Tiene Serie?” y mostrar siempre Nº Serie
        $rowTS.hide();
        $rowNum.show().find('input').prop('required', true);
        return;
      }
      // caso padre: mostramos el select y alternamos Number row
      $rowTS.show();
      if ($field.val() === 'True') {
        $rowNum.show().find('input').prop('required', true);
      } else {
        $rowNum.hide().find('input').val('').prop('required', false);
      }
    }
    // bind y trigger inicial
    $field.off('change.toggleSerie').on('change.toggleSerie', actualizarVista);
    actualizarVista();
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
          $modal.find('.modal-content').html(resp.html_form);
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
        minimumResultsForSearch: 0,

        // función que formatea cada opción del dropdown
        templateResult: function(item) {
          if (!item.id) return item.text;    
          const txt = item.text;
          return txt.length > 60
            ? txt.substr(0, 60) + '…'
            : txt;
        },
        // función que formatea el texto que se muestra una vez seleccionado
        templateSelection: function(item) {
          if (!item.id) return item.text;
          const txt = item.text;
          return txt.length > 60
            ? txt.substr(0, 60) + '…'
            : txt;
        }
      });

      // Ocultar productos hijos si no hay nada seleccionado todavía
      if (!$sel.val()) {
        $sel.find('option').each(function () {
          const $opt = $(this);
          const esHijo = String($opt.data('serie') || '') !== '';
          if (esHijo) {
            $opt.remove();  // Elimina del dropdown los productos con número de serie
          }
        });
      }

      // Al seleccionar o deseleccionar, re-filtra duplicados y cierra
      $sel.on('select2:select select2:unselect', () => {
        updateProductoOptions();
        $sel.select2('close');
      });
    });

    // Primera pasada de filtrado
    updateProductoOptions();

    // Ocultar botón "Crear Producto" si ya hay algo seleccionado
    $scope.find('.select2-producto-auto').each(function () {
      const $sel = $(this);
      const $row = $sel.closest('tr');
      const $btn = $row.find('.btn-nuevo-producto');
      if ($sel.val()) {
        $btn.hide();
      } else {
        $btn.show();
      }
    });
  }

  // Filtrar duplicados deshabilitando opciones
  function updateProductoOptions() {
    // Contar cuántas veces está seleccionado cada producto (sin serie)
    const counts = {};
    $('.linea-form:visible').each(function() {
      const $f      = $(this);
      const id      = $f.find('.select2-producto-auto').val();
      // Asegurarnos de que rawSerie sea siempre string
      const rawSerie = $f.find('.numero-serie-input').val() || '';
      const serie   = rawSerie.trim();
      if (id && !serie) {
        counts[id] = (counts[id] || 0) + 1;
      }
    });

    // Para cada select, activamos o desactivamos sus opciones
    $('.select2-producto-auto').each(function() {
      const $sel = $(this), me = $sel.val();
      $sel.find('option').each(function() {
        const $opt      = $(this),
              val       = $opt.val(),
              tieneSerie = String($opt.data('tiene-serie')) === 'true';
        if (!val) return;

        let disable = false;
        // Si NO tiene serie y ya está en counts, lo deshabilitamos (si no es este select)
        if (!tieneSerie && counts[val] >= 1 && me !== val) {
          disable = true;
        }

        $opt.prop('disabled', disable);
      });
      // Refrescar Select2
      $sel.trigger('change.select2');
    });
  }

  // Tras abrir el modal
  $('#modalRegistrarEntrada, #modalEditarEntrada').on('shown.bs.modal', () => {
    initSelect2Productos($('#tabla-entradas tbody'));
  });
  // Tras añadir cada fila
  $('#btn-agregar-fila').on('click', function () {
    const $total = $('#id_form-TOTAL_FORMS');
    const idx = parseInt($total.val(), 10);

    const $newRow = $($('#template-row').prop('outerHTML')
      .replace(/__INDEX__/g, idx))
      .removeAttr('id')
      .addClass('linea-form')
      .attr('data-index', idx)
      .show()
      .appendTo('#tabla-entradas tbody');

    $newRow.find('select, input[type="number"]').val('');
    $newRow.find('input[name$="-DELETE"]').remove();
    $newRow.find('.marca-cell, .color-cell, .modelo-cell').text('');
    $newRow.find('.serie-cell input.numero-serie-input').val('').show();
    $newRow.find('.btn-nuevo-producto, .btn-eliminar-fila').show();
    $total.val(idx + 1);

    initSelect2Productos($newRow);
    bindListenerCambioProducto();
    updateRowSerieQty($newRow);
  });

  // Al mostrar modal Registrar/Editar Entrada
  const $modalEntrada = $('#modalRegistrarEntrada, #modalEditarEntrada');
  $modalEntrada
    .on('shown.bs.modal', () => {
      initSelect2Productos($('#tabla-entradas tbody'));
      actualizarColumnasProductosExistentes(); // <- Actualiza columnas al abrir
      // Ajustar serie/cantidad en todas las filas
      $('#tabla-entradas tbody tr.linea-form').each(function() {
        updateRowSerieQty($(this));
      });
      // Fuerza eventos de Select2
      $('#tabla-entradas tbody .select2-producto-auto').each(function () {
        $(this).trigger('change');
      });
    })
    .on('show.bs.modal', () => {
      $('#template-row').find('.btn-nuevo-producto, .btn-eliminar-fila').hide();
    });
  $('#btn-agregar-fila').text('+ Agregar fila');

  $('#modalEditarEntrada').on('shown.bs.modal', function() {
    // Bloquear el select de producto en cada fila
    $('#tabla-entradas tbody tr.linea-form').each(function() {
      const $row = $(this);

      // No deshabilites el <select> real, solo el Select2 visual
      const $sel2 = $row.find('.select2-producto-auto');
      const $s2container = $sel2.next('.select2-container');
      $s2container.find('.select2-selection')
        .css('pointer-events', 'none')        
        .css('background-color', '#e9ecef')   
        .css('opacity', 0.7)                  
        .css('cursor', 'not-allowed');       

      // Para los hijos (tienen serie), bloquear también serie y cantidad;
      //    para los normales, ocultar número de serie y dejar cantidad editable.
      const data = $row.find('select[name$="-producto"] option:selected').data() || {};
      const $inpSerie = $row.find('input.numero-serie-input');
      const $inpQty   = $row.find('input[name$="-cantidad"]');

      if (data.serie) {
        // hijo: bloquea todo
        $inpSerie.show().prop({ readonly: true, disabled: true });
        $inpQty  .prop({ readonly: true, disabled: true });
      } else {
        // normal: oculta serie, mantiene cantidad editable
        $inpSerie.hide();
        $inpQty.prop({ readonly: false, disabled: false });
      }
    });
  });

  // Submit AJAX de la Entrada
  function bindFormEntrada() {
    $(document).off('submit', '#form-entrada, #form-editar-entrada');
    $(document).on('submit', '#form-entrada, #form-editar-entrada', function(e) {
      e.preventDefault();
      const $form   = $(this);
      const $modal  = $form.closest('.modal');

      // Backup de folio, series y cantidades
      const backupFolio      = $form.find('[name="folio"]').val() || '';
      const backupSeries     = {};
      const backupCantidades = {};
      $('#tabla-entradas tbody tr.linea-form').each(function(i) {
        backupSeries[i]     = $(this).find('input.numero-serie-input').val() || '';
        backupCantidades[i] = $(this).find('input[name$="-cantidad"]').val()    || '';
      });

      // Envío AJAX
      $.post($form.attr('action'), $form.serialize(), resp => {
        if (resp.success) {
          $modal.modal('hide');
          window.location = resp.redirect_url;
        } else {
          // Reemplazo del fragmento con errores
          $modal.find('#entrada-form-fields, #editar-form-fields').html(resp.html_form);

          // Restaurar folio
          $modal.find('[name="folio"]').val(backupFolio);

          // Reinicializar UI de filas y selects
          initSelect2Productos($('#tabla-entradas tbody'));
          bindAll();
          actualizarColumnasProductosExistentes();
          $('#tabla-entradas tbody .select2-producto-auto').each(function(){
            $(this).trigger('change.select2');
          });

          // Restaurar series y cantidades
          $('#tabla-entradas tbody tr.linea-form').each(function(i) {
            const $row = $(this);
            $row.find('input.numero-serie-input')
                .val( backupSeries[i] );
            $row.find('input[name$="-cantidad"]')
                .val( backupCantidades[i] );
          });

          // Reaplicar visibilidad de serie/cantidad
          $('#tabla-entradas tbody tr.linea-form').each(function() {
            updateRowSerieQty($(this));
          });
        }
      }).fail(() => {
        alert('Error de red. Intenta de nuevo.');
      });
    });
  }

  // Agregar / eliminar filas
  function bindBtnsLinea() {
    // + Agregar fila
  $(document).off("click", "#agregar-fila").on('click', '#btn-agregar-fila', function(e) {
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
    $row.find('.marca-cell, .color-cell, .modelo-cell').text('');
    $row.find('.serie-cell input.numero-serie-input').val('').hide();
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
        $row.find('.serie-cell').show();

        updateRowSerieQty($row);
        // Oculta “+ Nuevo Producto” en esta fila
        $row.find('.btn-nuevo-producto').hide();
        // vuelve a filtrar duplicados
        updateProductoOptions();
        // cierra el dropdown
        $sel.select2('close');
      });
    // Si usas allowClear tú también debes escuchar el evento clear
    $(document).off('select2:clear', '.select2-producto-auto')
      .on('select2:clear', '.select2-producto-auto', function() {
        updateProductoOptions();
      });
  }

  // Cuando se muestra el modal de edición, actualiza todas las columnas
  $('#modalEditarEntrada').on('shown.bs.modal', function() {
    actualizarColumnasProductosExistentes();
  });

  function actualizarColumnasProductosExistentes() {
    $('#tabla-entradas tbody tr.linea-form').each(function () {
      const $row  = $(this);
      const data  = $row
        .find('.select2-producto-auto option:selected')
        .data() || {};

      // Rellenar siempre las columnas
      $row.find('.marca-cell').text(data.marca   || '');
      $row.find('.color-cell').text(data.color   || '');
      $row.find('.modelo-cell').text(data.modelo || '');

      // Volcar la serie en el input, si existe
      const $serieInput = $row.find('input.numero-serie-input');
      $serieInput.val(data.serie || '');

      // Si es un hijo (ya trae serie), bloqueamos serie y cantidad
      if (data.serie) {
        $serieInput.prop('readonly', true);
        $row.find('input[name$="-cantidad"]').prop('readonly', true);
      }
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
            attrs['data-tiene-serie'] = data.producto_tiene_serie ? 'true' : 'false';
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
            // Hacemos visible la celda y el input de serie
            const $serieCelda  = $row.find('.serie-cell').show();
            const $serieInput  = $serieCelda
              .find('input.numero-serie-input')
              .show()
              .prop('required', true);
            // Asignamos el valor de serie **al input**, no al contenedor
            $serieInput.val(attrs['data-serie']);
            // Rellenamos las celdas de marca/color/modelo
            $row.find('.marca-cell').text(attrs['data-marca']);
            $row.find('.color-cell').text(attrs['data-color']);
            $row.find('.modelo-cell').text(attrs['data-modelo']);
            // Refresca el bloqueo de duplicados
            updateProductoOptions();
            updateRowSerieQty($row);
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
              attrs['data-tiene-serie'] = data.producto_tiene_serie ? 'true' : 'false';
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
              // Seleccionamos la nueva opción en el <select> de la fila
              const $sel = $row.find('select[name$="-producto"]');
              $sel.val(val).trigger('change.select2');
              // Hacemos visible la celda y el input de serie
              const $serieCelda  = $row.find('.serie-cell').show();
              const $serieInput  = $serieCelda
                .find('input.numero-serie-input')
                .show()
                .prop('required', true);
              // Asignamos el valor de serie **al input**, no al contenedor
              $serieInput.val(attrs['data-serie']);
              // Rellenamos las celdas de marca/color/modelo
              $row.find('.marca-cell').text(attrs['data-marca']);
              $row.find('.color-cell').text(attrs['data-color']);
              $row.find('.modelo-cell').text(attrs['data-modelo']);
              // Actualiza bloqueo de duplicados
              updateProductoOptions();
              // Reindexa filas y TOTAL_FORMS
              reorderRows();
              updateRowSerieQty($row);
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
      // Reindexa todo: selects, inputs y textareas
      $tr.find('select, input, textarea').each(function() {
        const old = this.name || '';
        const newName = old.replace(/-\d+-/, `-${i}-`);
        $(this).attr({ name: newName, id: 'id_' + newName });
      });
    });
    $('#id_form-TOTAL_FORMS').val($rows.length);
  }

  // Función que decide visibilidad de Serie / bloqueo de Cantidad
  function updateRowSerieQty($row) {
    const $select     = $row.find('.select2-producto-auto');
    const $selected   = $select.find('option:selected');
    const tieneSerie  = String($selected.data('tiene-serie')) === 'true';
    const serieFija   = $selected.data('serie') || '';  // hijos siempre traen una serie

    const $inputSerie = $row.find('.serie-cell input.numero-serie-input');
    const $inputQty   = $row.find('input[name$="-cantidad"]');

    if (serieFija) {
      // Producto hijo: ya tiene una serie asignada → readonly total
      $inputSerie
        .val(serieFija)
        .show()
        .prop({ readonly: true, disabled: true, required: true });
      $inputQty
        .val(1)
        .prop({ readonly: true, disabled: true });

    } else if (tieneSerie) {
      // Producto padre con serie activada → permitir escribir la serie (requerido), qty = 1
      $inputSerie
        .show()
        .prop({ required: true, readonly: false, disabled: false });
      $inputQty
        .val(1)
        .prop({ readonly: true, disabled: false });

    } else {
      // Producto normal (sin serie) → serie oculta, qty editable
      $inputSerie
        .val('')
        .hide()
        .prop({ required: false, readonly: false, disabled: false });
      $inputQty
        .prop({ readonly: false, disabled: false });
    }
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