    $(function () {
    // Inicializar Select2
    $('.select2-solicitante, .select2-unidad, .select2-departamento').select2({
        theme: 'bootstrap4',
        width: '100%',
        dropdownParent: $('#modalRegistrarSalida')
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

    // Al cambiar DEPARTAMENTO → repuebla UNIDADES sin perder selección válida
    $('#id_departamento').on('select2:select', function (e) {
        const deptoId       = parseInt(e.params.data.id, 10);
        const todasUnidades = window.todosUnidades || [];
        const $unidad       = $('#id_unidad');
        const prevUni       = $unidad.val();

        $unidad.empty().append('<option value="">---------</option>');
        todasUnidades.forEach(u => {
        if (u.departamentos.includes(deptoId)) {
            $unidad.append(`<option value="${u.id}">${u.nombre}</option>`);
        }
        });

        // Restaurar unidad previa si sigue siendo válida
        if (prevUni && $unidad.find(`option[value="${prevUni}"]`).length) {
        $unidad.val(prevUni);
        } else {
        $unidad.val('');
        }
        $unidad.trigger('change.select2');
    });

    // Al cambiar UNIDAD → repuebla DEPARTAMENTOS sin perder selección válida
    $('#id_unidad').on('select2:select', function (e) {
        const unidadId  = parseInt(e.params.data.id, 10);
        const datosDeps  = window.datosUnidades || {};
        const $depto    = $('#id_departamento');
        const prevDepto = $depto.val();

        $depto.empty().append('<option value="">---------</option>');
        (datosDeps[unidadId] || []).forEach(dep => {
        $depto.append(`<option value="${dep.id}">${dep.nombre}</option>`);
        });

        // Restaurar depto previo si sigue siendo válido
        if (prevDepto && $depto.find(`option[value="${prevDepto}"]`).length) {
        $depto.val(prevDepto);
        } else {
        $depto.val('');
        }
        $depto.trigger('change.select2');
    });

    // Filtrar SOLICITANTES al cambiar unidad o departamento
    function filtrarSolicitantes() {
        const unidadId = $('#id_unidad').val();
        const deptoId  = $('#id_departamento').val();
        const todos    = window.todosSolicitantes || [];
        const $sol     = $('#id_solicitante').empty().append('<option value="">---------</option>');
        const prevSol  = $('#id_solicitante').val();
        let valid      = false;

        todos.forEach(s => {
        if ((!unidadId || s.unidad_id == unidadId) &&
            (!deptoId  || s.departamento_id == deptoId)) {
            $sol.append(`<option value="${s.id}">${s.nombre}</option>`);
            if (s.id == prevSol) valid = true;
        }
        });

        $sol.val(valid ? prevSol : '').trigger('change.select2');
    }
    $('#id_unidad').on('select2:select', filtrarSolicitantes);
    $('#id_departamento').on('select2:select', filtrarSolicitantes);

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