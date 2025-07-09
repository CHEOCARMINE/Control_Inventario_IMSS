$(function () {
    // Inicializar Select2
    $('.select2-solicitante, .select2-unidad, .select2-departamento').select2({
        theme: 'bootstrap4',
        width: '100%',
        dropdownParent: $('#modalRegistrarSalida')
    });

    // Cargar productos del carrito
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
                        ${p.esHijo ? '<span class="text-muted">—</span>' :
                        `<input type="number" class="form-control form-control-sm cantidad-input" value="${p.cantidad}" min="1" data-id="${p.id}">`}
                    </td>
                    <td class="text-center">
                        <button type="button" class="btn btn-sm btn-danger btn-eliminar-producto" data-id="${p.id}">&times;</button>
                    </td>
                </tr>`;
            $tabla.append(fila);
        });
    }

    // Eliminar producto del carrito
    $('#tabla-carrito').on('click', '.btn-eliminar-producto', function () {
        const id = $(this).data('id');
        carrito = carrito.filter(p => p.id != id);
        localStorage.setItem('carritoSalida', JSON.stringify(carrito));
        $(this).closest('tr').remove();
        actualizarContador();

        // Mostrar mensaje si está vacío
        if ($('#tabla-carrito tbody tr').length === 0) {
            $tabla.append('<tr><td colspan="7" class="text-center">No hay productos agregados.</td></tr>');
        }

        // Llamar a función global para reactivar el botón del producto eliminado
        if (window.activarProducto) {
            window.activarProducto(id);
        }
    });

    // Cambiar cantidad en el modal
    $('#tabla-carrito').on('change', '.cantidad-input', function () {
        const id = $(this).data('id');
        const nuevaCantidad = parseInt($(this).val(), 10);

        if (!isNaN(nuevaCantidad) && nuevaCantidad > 0) {
            carrito = carrito.map(p => {
                if (p.id == id && !p.esHijo) {
                    p.cantidad = nuevaCantidad;
                }
                return p;
            });
            localStorage.setItem('carritoSalida', JSON.stringify(carrito));

            // Actualizar cantidad también en botón de productos si está presente
            const $btn = $(`.btn-agregar-normal[data-id="${id}"]`);
            if ($btn.length) {
                $btn.closest('tr').find('.input-cantidad').val(nuevaCantidad);
            }

        } else {
            $(this).val(1).trigger('change');
        }
    });

    // Auto-llenado de Unidad y Departamento al seleccionar un Solicitante
    $('#id_solicitante').on('select2:select', function(e) {
    const solId = e.params.data.id;
    const datos = window.datosSolicitantes || {};
    const uniId = datos[solId]?.unidad_id;
    const depId = datos[solId]?.departamento_id;

    if (uniId) {
        // Asigna el valor y refresca solo el widget Select2 de Unidad
        $('#id_unidad')
        .val(uniId)
        .trigger('change.select2');
    }
    if (depId) {
        // Asigna el valor y refresca solo el widget Select2 de Departamento
        $('#id_departamento')
        .val(depId)
        .trigger('change.select2');
    }
    });

    // Al cambiar DEPARTAMENTO → actualizar UNIDADES
    $('#id_departamento').on('select2:select', function(e) {
    const deptoId       = parseInt(e.params.data.id, 10);
    const todasUnidades = window.todosUnidades || [];
    const $unidad       = $('#id_unidad').empty().append('<option value="">---------</option>');

    todasUnidades.forEach(u => {
        // u.departamentos es un array de IDs de departamentos
        if (u.departamentos.includes(deptoId)) {
        $unidad.append(`<option value="${u.id}">${u.nombre}</option>`);
        }
    });

    // refrescamos solo la UI de Select2
    $unidad.val('').trigger('change.select2');
    });

    // Al cambiar UNIDAD o DEPARTAMENTO → actualizar SOLICITANTES
    $('#id_unidad, #id_departamento').on('select2:select', function() {
    const unidadId     = $('#id_unidad').val();
    const deptoId      = $('#id_departamento').val();
    const todos        = window.todosSolicitantes || [];
    const $solicitante = $('#id_solicitante').empty().append('<option value="">---------</option>');
    const prev         = $('#id_solicitante').val();
    let sigueValido    = false;

    todos.forEach(s => {
        if (( !unidadId || s.unidad_id == unidadId ) &&
            ( !deptoId  || s.departamento_id == deptoId )) {
        $solicitante.append(`<option value="${s.id}">${s.nombre}</option>`);
        if (s.id == prev) sigueValido = true;
        }
    });

    $solicitante
        .val(sigueValido ? prev : '')
        .trigger('change.select2');
    });

    // Al cambiar unidad/departamento → actualizar solicitantes
    $('#id_unidad, #id_departamento').on('change', function () {
        const unidadId = $('#id_unidad').val();
        const deptoId = $('#id_departamento').val();
        const todos = window.todosSolicitantes || [];
        const $solicitante = $('#id_solicitante');
        const valorAnterior = $solicitante.val();
        let sigueSiendoValido = false;

        $solicitante.empty().append('<option value="">---------</option>');
        todos.forEach(s => {
            if ((unidadId === '' || s.unidad_id == unidadId) &&
                (deptoId === '' || s.departamento_id == deptoId)) {
                $solicitante.append(`<option value="${s.id}">${s.nombre}</option>`);
                if (s.id == valorAnterior) sigueSiendoValido = true;
            }
        });

        $solicitante.val(sigueSiendoValido ? valorAnterior : '').trigger('change');
    });

    // Actualizar contador
    function actualizarContador() {
        const total = $('#tabla-carrito tbody tr').length;
        $('#contador-productos').text(total);
    }

    window.actualizarContadorSalida = actualizarContador;
});