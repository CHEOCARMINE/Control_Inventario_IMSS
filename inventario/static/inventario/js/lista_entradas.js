$(function() {
  // 1) Al cargar la página, ocultamos #template-row
  $('#template-row').hide();
  console.log('[lista_entradas] template-row oculto al cargar.');

  // 2) Función para clonar “template-row” y rellenar datos si vienen
  function agregarFilaEntrada(productoId, productoLabel, productoMarca, productoColor, productoModelo, productoSerie) {
    console.log('[lista_entradas] agregarFilaEntrada llamado con:',
      productoId, productoLabel, productoMarca, productoColor, productoModelo, productoSerie
    );

    // Índice de la nueva fila
    const totalFilas = $('#tabla-entradas tbody tr.linea-form').length;
    const nuevoIndex = totalFilas;

    // Clonamos la fila oculta
    const $template = $('#template-row');
    const htmlRaw = $template.prop('outerHTML').replace(/__INDEX__/g, nuevoIndex);
    const $nuevaFila = $(htmlRaw);

    $('#tabla-entradas tbody').append($nuevaFila);
    console.log('[lista_entradas] Fila clonada e insertada con índice:', nuevoIndex);

    // Si vienen datos desde el “Crear Producto”:
    if (productoId) {
      const $select = $nuevaFila.find('select.select-producto-auto');

      // 2.a) Si no existía esta <option> en el <select>, la agregamos:
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

      // 2.b) Seleccionamos esa opción y disparamos “change” para rellenar las celdas
      $select.val(productoId);
      $select.trigger('change');
    }

    // 2.c) Poner foco en “cantidad” de la fila creada
    $nuevaFila.find(`input[name="form-${nuevoIndex}-cantidad"]`).focus();
  }

  // 3) Cuando cambie cualquier <select class="select-producto-auto">, rellenar Marca/Color/Modelo/Serie
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

  // 4) Al pulsar “+ Agregar Producto” (botón #btn-agregar-fila), clonamos una fila vacía
  $('body').on('click', '#btn-agregar-fila', function(e) {
    e.preventDefault();
    console.log('[lista_entradas] Botón +Agregar Producto clickeado.');
    agregarFilaEntrada(); // sin parámetros → fila vacía
  });

  // 5) Escuchar evento “submitSuccess” disparado desde el modal “Crear Producto”
  //    NOTA: este evento debe dispararse desde el propio modal de creación de producto:
  //          $('#modalCrearProducto').trigger('submitSuccess', {...});
  $(document).on('submitSuccess', function(event, data) {
    console.log('[lista_entradas] evento submitSuccess capturado. Data:', data);

    const productoId     = data.producto_id;
    const productoLabel  = data.producto_label;
    const productoMarca  = data.producto_marca;
    const productoColor  = data.producto_color;
    const productoModelo = data.producto_modelo;
    const productoSerie  = data.producto_serie;

    // 5.a) Insertar la nueva <option> en cada <select> que aún no la tenga
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

    // 5.b) Finalmente, crear una nueva fila **ya seleccionada** en ese producto
    agregarFilaEntrada(
      productoId,
      productoLabel,
      productoMarca,
      productoColor,
      productoModelo,
      productoSerie
    );
  });

  // 6) “×” elimina la fila (marca DELETE y la quita del DOM)
  $('body').on('click', '.btn-eliminar-fila', function(e) {
    e.preventDefault();
    const $fila = $(this).closest('tr.linea-form');
    $fila.find('input[type="checkbox"][name$="-DELETE"]').prop('checked', true);
    $fila.remove();
    console.log('[lista_entradas] Fila eliminada.');
  });
});