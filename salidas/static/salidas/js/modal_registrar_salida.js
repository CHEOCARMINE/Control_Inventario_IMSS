    function formatOption(option) {
    if (!option.id) {
        // placeholder (valor vacío)
        return option.text;
    }
    const valid = $(option.element).data('valid');
    if (valid === false || valid === 'false') {
        return `<span class="text-muted">${option.text}</span>`;
    }
    return option.text;
    }

    $(function () {
    // Inicializar Select2
    $('#id_solicitante').select2({
    placeholder:    'Selecciona un solicitante',
    allowClear:     true,
    theme:          'bootstrap4',
    width:          '100%',
    dropdownParent: $('#modalRegistrarSalida'),
    templateResult: formatOption,
    escapeMarkup:   markup => markup
    });
    $('#id_solicitante option').data('valid', true);
    $('#id_solicitante').trigger('change.select2');

    $('#id_unidad').select2({
    placeholder:    'Selecciona una unidad',
    allowClear:     true,
    theme:          'bootstrap4',
    width:          '100%',
    dropdownParent: $('#modalRegistrarSalida'),
    templateResult: formatOption,
    escapeMarkup:   markup => markup
    });

    $('#id_departamento').select2({
    placeholder:    'Selecciona un departamento',
    allowClear:     true,
    theme:          'bootstrap4',
    width:          '100%',
    dropdownParent: $('#modalRegistrarSalida'),
    templateResult: formatOption,
    escapeMarkup:   markup => markup
    });

    // Lógica de carrito y cantidades (igual a como ya lo tenías)
    const $tabla = $('#tabla-carrito tbody');
    $tabla.empty();
    let carrito = JSON.parse(localStorage.getItem('carritoSalida') || '[]');
    if (carrito.length === 0) {
        $tabla.append('<tr><td colspan="7" class="text-center">No hay productos agregados.</td></tr>');
    } else {
        carrito.forEach(p => {
        const fila = `
            <tr data-id="${p.id}">
            <td>${p.nombre}</td>
            <td>${p.marca || ''}</td>
            <td>${p.modelo || ''}</td>
            <td>${p.color || ''}</td>
            <td>${p.numero_serie || ''}</td>
            <td>
                ${p.esHijo
                ? '<span class="text-muted">—</span>'
                : `<input type="number" class="form-control form-control-sm cantidad-input"
                            value="${p.cantidad}" min="1" max="${p.stock}"
                            data-id="${p.id}" data-stock="${p.stock}">`}
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-danger btn-eliminar-producto" data-id="${p.id}">&times;</button>
            </td>
            </tr>`;
        $tabla.append(fila);
        });
    }

    function actualizarContador() {
        const total = $('#tabla-carrito tbody tr').length;
        $('#contador-productos').text(total);
    }
    window.actualizarContadorSalida = actualizarContador;

    $('#tabla-carrito').on('click', '.btn-eliminar-producto', function () {
        const id = $(this).data('id');
        carrito = carrito.filter(p => p.id != id);
        localStorage.setItem('carritoSalida', JSON.stringify(carrito));
        $(this).closest('tr').remove();
        actualizarContador();
        if ($('#tabla-carrito tbody tr').length === 0) {
        $tabla.append('<tr><td colspan="7" class="text-center">No hay productos agregados.</td></tr>');
        }
        if (window.activarProducto) window.activarProducto(id);
    });

    $('#tabla-carrito').on('change', '.cantidad-input', function () {
        const $input = $(this);
        const id      = $input.data('id');
        const stock   = parseInt($input.attr('max'), 10) || Infinity;
        let nuevaCantidad = parseInt($input.val(), 10);
        if (isNaN(nuevaCantidad) || nuevaCantidad < 1 || nuevaCantidad > stock) {
        nuevaCantidad = 1;
        $input.val(nuevaCantidad);
        }
        carrito = carrito.map(p => {
        if (p.id == id && !p.esHijo) p.cantidad = nuevaCantidad;
        return p;
        });
        localStorage.setItem('carritoSalida', JSON.stringify(carrito));
        const $btn = $(`.btn-agregar-normal[data-id="${id}"]`);
        if ($btn.length) $btn.closest('tr').find('.input-cantidad').val(nuevaCantidad);
    });

    $('#modalRegistrarSalida').on('hidden.bs.modal', function() {
        $('.cantidad-input').each(function() {
        const $input = $(this);
        const stock  = parseInt($input.attr('max'), 10) || Infinity;
        let val      = parseInt($input.val(), 10);
        if (isNaN(val) || val < 1 || val > stock) {
            $input.val(1).trigger('change');
        }
        });
    });

    // Autollenado solicitante → unidad & departamento
    $('#id_solicitante').on('select2:select', function (e) {
        const solId = e.params.data.id;
        const datos = window.datosSolicitantes || {};
        const uniId = datos[solId]?.unidad_id;
        const depId = datos[solId]?.departamento_id;
        if (uniId) $('#id_unidad').val(uniId).trigger('change.select2');
        if (depId) $('#id_departamento').val(depId).trigger('change.select2');
    });

    // Al seleccionar DEPARTAMENTO → actualiza data-valid de cada opción de UNIDAD
    $('#id_departamento').on('select2:select', function(e) {
    const deptoId = Number(e.params.data.id);
    $('#id_unidad option').each(function() {
        const val = this.value;
        if (!val || isNaN(Number(val))) return;       // saltar placeholder u opciones vacías

        const uId    = Number(val);
        const unidad = window.todosUnidadesCompleto.find(u => u.id === uId);
        if (!unidad) return;                          // saltar si no existe en el array

        const valid = unidad.departamentos.includes(deptoId);
        $(this).data('valid', valid);
    });

    $('#id_unidad').trigger('change.select2');
    filtrarSolicitantes();
    });

    // Al borrar (clear) DEPARTAMENTO → marca todas las UNIDADES como válidas
    $('#id_departamento').on('select2:clear', function() {
    $('#id_unidad option').data('valid', true);
    $('#id_unidad').trigger('change.select2');
    filtrarSolicitantes();
    });

    // Al seleccionar UNIDAD → actualiza data-valid de cada opción de DEPARTAMENTO
    $('#id_unidad').on('select2:select', function(e) {
    const unidadId = Number(e.params.data.id);
    $('#id_departamento option').each(function() {
        const val = this.value;
        if (!val || isNaN(Number(val))) return;       // saltar placeholder

        const dId   = Number(val);
        const unidad = window.todosUnidadesCompleto.find(u => u.id === unidadId);
        if (!unidad) return;

        const valid = (unidad.departamentos || []).includes(dId);
        $(this).data('valid', valid);
    });

    $('#id_departamento').trigger('change.select2');
    filtrarSolicitantes();
    });

    // Al borrar (clear) UNIDAD → marca todos los DEPARTAMENTOS como válidos
    $('#id_unidad').on('select2:clear', function() {
    $('#id_departamento option').data('valid', true);
    $('#id_departamento').trigger('change.select2');
    filtrarSolicitantes();
    });

    // Si seleccionas una UNIDAD inválida para el departamento actual, limpia el departamento
    $('#id_unidad').on('select2:select', function(e) {
    if ($(e.params.data.element).data('valid') === false) {
        $('#id_departamento').val(null).trigger('change.select2');
    }
    });

    // Si seleccionas un DEPARTAMENTO inválido para la unidad actual, limpia la unidad
    $('#id_departamento').on('select2:select', function(e) {
    if ($(e.params.data.element).data('valid') === false) {
        $('#id_unidad').val(null).trigger('change.select2');
    }
    });

    // Función para filtrar solicitantes según unidad/departamento
    function filtrarSolicitantes() {
    const unidadId = $('#id_unidad').val();
    const deptoId  = $('#id_departamento').val();

    // Marca data-valid en cada <option>
    $('#id_solicitante option').each(function() {
        const $opt = $(this);
        const sUni = $opt.data('unidad-id');
        const sDep = $opt.data('departamento-id');
        const valid =
        (!unidadId || sUni == unidadId) &&
        (!deptoId  || sDep == deptoId);
        $opt.data('valid', valid);
    });

    // Si la opción actualmente seleccionada ya no es válida, la limpia
    const selVal = $('#id_solicitante').val();
    if (selVal) {
        const selValid = $('#id_solicitante option:selected').data('valid');
        if (selValid === false) {
        $('#id_solicitante').val(null);
        }
    }

    // Refresca el dropdown para que templateResult pinte en gris
    $('#id_solicitante').trigger('change.select2');
    }

    // Capturar el submit y enviarlo por AJAX
    $('#formSalida').on('submit', function(e) {
    e.preventDefault();

    // Inyectar el carrito actual en el hidden
    $('#id_carrito_json').val(JSON.stringify(carrito));

    // Serializar y enviar
    const url  = $(this).attr('action');
    const data = $(this).serialize();
    $.ajax({
        url:    url,
        method: 'POST',
        data:   data,
        success(resp) {
        if (resp.success) {
            // Aquí borramos el carrito de localStorage
            localStorage.removeItem('carritoSalida');
            // También reseteamos la variable en memoria
            carrito = [];
            // Y actualizamos el contador (badges) en la UI
            if (window.actualizarContadorSalida) {
            window.actualizarContadorSalida();
            }
            // Ahora cerramos el modal y redirigimos
            $('#modalRegistrarSalida').modal('hide');
            window.location.href = resp.redirect_url;
        } else {
            // errores de validación: pintamos el fragmento con errores
            $('#modalRegistrarSalida .modal-body').html(resp.html_form);
        }
        }
    });
    });
});  