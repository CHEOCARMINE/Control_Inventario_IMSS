$(function() {
  $('#template-row').hide();
  console.log('[lista_entradas] template-row oculto al cargar.');

  function agregarFilaEntrada(productoId, productoLabel, productoMarca, productoColor, productoModelo, productoSerie) {
    console.log('[lista_entradas] agregarFilaEntrada llamado con:',
      productoId, productoLabel, productoMarca, productoColor, productoModelo, productoSerie
    );

    const totalFilas = $('#tabla-entradas tbody tr.linea-form').length;
    const nuevoIndex = totalFilas;

    const $template = $('#template-row');
    const htmlRaw = $template.prop('outerHTML').replace(/__INDEX__/g, nuevoIndex);
    const $nuevaFila = $(htmlRaw);

    $('#tabla-entradas tbody').append($nuevaFila);
    console.log('[lista_entradas] Fila clonada e insertada con índice:', nuevoIndex);

    if (productoId) {
      const $select = $nuevaFila.find('select.select-producto-auto');

      if ($select.find(`option[value="${productoId}"]`).length === 0) {
        const $opt = $('<option>', {
          value: productoId,
          text: productoLabel,
          'data-marca':  productoMarca,
          'data-color':  productoColor,
          'data-modelo': productoModelo,
          'data-serie':  productoSerie
        });
        $select.append($opt);
        console.log('[lista_entradas] Nueva <option> agregada al select:', productoLabel);
      }

      $select.val(productoId);
      $select.trigger('change');
    }

    $nuevaFila.find(`input[name="form-${nuevoIndex}-cantidad"]`).focus();
  }

  $('body').on('change', '.select-producto-auto', function() {
    const $select = $(this);
    const $fila   = $select.closest('tr.linea-form');
    const sel     = $select.find('option:selected');

    const marca  = sel.data('marca')  || '';
    const color  = sel.data('color')  || '';
    const modelo = sel.data('modelo') || '';
    const serie  = sel.data('serie')  || '';

    $fila.find('.marca-cell').text(marca);
    $fila.find('.color-cell').text(color);
    $fila.find('.modelo-cell').text(modelo);
    $fila.find('.serie-cell').text(serie);
  });

  $('body').on('click', '#btn-agregar-fila', function(e) {
    e.preventDefault();
    console.log('[lista_entradas] Botón +Agregar Producto clickeado.');
    agregarFilaEntrada(); // sin parámetros → fila vacía
  });

  $(document).on('submitSuccess', function(event, data) {
    console.log('[lista_entradas] evento submitSuccess capturado. Data:', data);

    const productoId     = data.producto_id;
    const productoLabel  = data.producto_label;
    const productoMarca  = data.producto_marca;
    const productoColor  = data.producto_color;
    const productoModelo = data.producto_modelo;
    const productoSerie  = data.producto_serie;

    $('.select-producto-auto').each(function() {
      if ($(this).find(`option[value="${productoId}"]`).length === 0) {
        $(this).append($('<option>', {
          value: productoId,
          text: productoLabel,
          'data-marca':  productoMarca,
          'data-color':  productoColor,
          'data-modelo': productoModelo,
          'data-serie':  productoSerie
        }));
        console.log('[lista_entradas] <option> agregado a select existente:', productoLabel);
      }
    });

    agregarFilaEntrada(
      productoId,
      productoLabel,
      productoMarca,
      productoColor,
      productoModelo,
      productoSerie
    );
  });

  $('body').on('click', '.btn-eliminar-fila', function(e) {
    e.preventDefault();
    const $fila = $(this).closest('tr.linea-form');
    $fila.find('input[type="checkbox"][name$="-DELETE"]').prop('checked', true);
    $fila.remove();
    console.log('[lista_entradas] Fila eliminada.');
  });
});