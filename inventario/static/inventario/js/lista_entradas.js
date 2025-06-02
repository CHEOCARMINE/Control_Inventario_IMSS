$(function() {
  // Ocultar la fila “template-row” al cargar la página
  $('#template-row').hide();
  console.log('[lista_entradas] template-row oculto al cargar.');

  // Función para clonar la plantilla de fila (#template-row) y rellenar Marca/Color/Modelo/Serie si se pasan datos.
  function agregarFilaEntrada(productoId, productoLabel, productoMarca, productoColor, productoModelo, productoSerie) {
    console.log('[lista_entradas] agregarFilaEntrada llamado con:', 
      productoId, productoLabel, productoMarca, productoColor, productoModelo, productoSerie
    );

    // Calcular el índice de la nueva fila
    const totalFilas = $('#tabla-entradas tbody tr.linea-form').length;
    const nuevoIndex = totalFilas;

    // Tomar el <tr id="template-row">, convertirlo a cadena, reemplazar "__INDEX__" y crear el elemento
    const $template = $('#template-row');
    const htmlRaw = $template.prop('outerHTML').replace(/__INDEX__/g, nuevoIndex);
    const $nuevaFila = $(htmlRaw);

    // Añadir la nueva fila al <tbody>
    $('#tabla-entradas tbody').append($nuevaFila);
    console.log('[lista_entradas] Fila clonada e insertada con índice:', nuevoIndex);

    // Si vienen datos de un producto recién creado, inyectarlos en el <select> y en las celdas
    if (productoId) {
      const $select = $nuevaFila.find('select.select-producto-auto');

      // Si el <select> no tiene ya esa opción, la creamos
      if ($select.find(`option[value="${productoId}"]`).length === 0) {
        const $opt = $('<option>', {
          value: productoId,
          text: productoLabel,
          'data-marca': productoMarca,
          'data-color': productoColor,
          'data-modelo': productoModelo,
          'data-serie': productoSerie
        });
        $select.append($opt);
        console.log('[lista_entradas] Nueva <option> agregada al select:', productoLabel);
      }

      // Marcar el <select> en ese producto y disparar el cambio para llenar las celdas
      $select.val(productoId);
      $select.trigger('change');
    }

    // Poner el foco en la columna de cantidad de la nueva fila
    $nuevaFila.find(`input[name="form-${nuevoIndex}-cantidad"]`).focus();
  }

  // Al cambiar cualquier select de producto (“.select-producto-auto”), actualizar Marca/Color/Modelo/Serie en esa fila.
  $('body').on('change', '.select-producto-auto', function() {
    const $select   = $(this);
    const $fila     = $select.closest('tr.linea-form');
    const selected  = $select.find('option:selected');

    const marca  = selected.data('marca')  || '';
    const color  = selected.data('color')  || '';
    const modelo = selected.data('modelo') || '';
    const serie  = selected.data('serie')  || '';

    $fila.find('.marca-cell').text(marca);
    $fila.find('.color-cell').text(color);
    $fila.find('.modelo-cell').text(modelo);
    $fila.find('.serie-cell').text(serie);
  });

  // Al pulsar “+ Agregar Producto” (botón #btn-agregar-fila), clonamos una fila vacía (sin seleccionar producto).
  $('body').on('click', '#btn-agregar-fila', function(e) {
    e.preventDefault();
    console.log('[lista_entradas] Botón +Agregar Producto clickeado.');
    agregarFilaEntrada();
  });

  // Capturar el evento “submitSuccess” proveniente del modal de “Crear Producto al vuelo” (#modalCrearProducto). El modal debe hacer: $('#modalCrearProducto').trigger('submitSuccess', {...});
  $('#modalCrearProducto').on('submitSuccess', function(event, data) {
    console.log('[lista_entradas] evento submitSuccess capturado. Data:', data);

    // Obtenemos todos los datos que devolvió la vista:
    const productoId     = data.producto_id;
    const productoLabel  = data.producto_label;
    const productoMarca  = data.producto_marca;
    const productoColor  = data.producto_color;
    const productoModelo = data.producto_modelo;
    const productoSerie  = data.producto_serie;

    // Añadimos esa <option> al último <select> existente (si no estaba ya)
    $('.select-producto-auto').each(function() {
      if ($(this).find(`option[value="${productoId}"]`).length === 0) {
        $(this).append($('<option>', {
          value: productoId,
          text: productoLabel,
          'data-marca': productoMarca,
          'data-color': productoColor,
          'data-modelo': productoModelo,
          'data-serie': productoSerie
        }));
        console.log('[lista_entradas] Nueva <option> agregado a un select existente:', productoLabel);
      }
    });

    // Finalmente, agregamos una fila nueva **seleccionada** en ese producto
    agregarFilaEntrada(
      productoId,
      productoLabel,
      productoMarca,
      productoColor,
      productoModelo,
      productoSerie
    );
  });

  // Al pulsar la “×” dentro de una fila, marcamos DELETE y eliminamos la fila
  $('body').on('click', '.btn-eliminar-fila', function(e) {
    e.preventDefault();
    const $fila = $(this).closest('tr.linea-form');
    $fila.find('input[type="checkbox"][name$="-DELETE"]').prop('checked', true);
    $fila.remove();
    console.log('[lista_entradas] Fila eliminada.');
  });
});
