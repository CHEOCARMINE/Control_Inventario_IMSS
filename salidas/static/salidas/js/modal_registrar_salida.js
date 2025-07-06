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

    // Autocompletar unidad y depto al elegir solicitante
    $('#id_solicitante').on('change', function () {
        const solicitanteId = $(this).val();
        const datos = window.datosSolicitantes || {};
        if (datos[solicitanteId]) {
            $('#id_unidad').val(datos[solicitanteId].unidad_id).trigger('change');
            $('#id_departamento').val(datos[solicitanteId].departamento_id).trigger('change');
        }
    });

    // Al cambiar unidad → actualizar departamentos
    $('#id_unidad').on('change', function () {
        const unidadId = $(this).val();
        const datos = window.datosUnidades || {};
        const $depto = $('#id_departamento');
        $depto.empty().append('<option value="">---------</option>');
        if (datos[unidadId]) {
            datos[unidadId].forEach(dep => {
                $depto.append(`<option value="${dep.id}">${dep.nombre}</option>`);
            });
        }
        $depto.val('').trigger('change');
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