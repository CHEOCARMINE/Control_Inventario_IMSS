$(document).ready(function () {

    $('.fila-existente').each(function () {
        const $fila = $(this);
        const $select = $fila.find('.select2-producto-auto');
        const productoId = Number($fila.data('producto-id'));

        // Bloquear el select de producto
        $select.prop('disabled', true);

        // Buscar el producto en la lista global
        const producto = window.todosProductos.find(p => p.id === productoId);
        if (!producto) return;

        // Si es hijo → bloquear input cantidad y poner en 1
        if (producto.esHijo) {
            $fila.find('.cantidad-input')
                .val(1)
                .prop('readonly', true);
        } else {
            // Si es normal → dejar editable (por si acaso desbloquear)
            $fila.find('.cantidad-input')
                .prop('readonly', false);
        }
    });

    inicializarSelectsProductos();
    inicializarSelectsSolicitudes();

    // Refrescar opciones deshabilitadas al seleccionar o limpiar producto
    $('#tabla-editar-salida').on('select2:select select2:unselect', '.select2-producto-auto', function () {
        updateProductoOptions();
    });

    // Al cargar, aplicar deshabilitados iniciales
    updateProductoOptions();

    // Agregar fila nueva
    $('#btn-agregar-fila-edicion').on('click', function () {
        const nuevaFila = construirFilaVacia();
        $('#tabla-editar-salida tbody').append(nuevaFila);
        inicializarSelectsProductos();
    });

    // Eliminar fila
    $('#tabla-editar-salida').on('click', '.btn-eliminar-fila', function () {
        $(this).closest('tr').remove();
    });

    // Al seleccionar producto
    $('#tabla-editar-salida').on('change', '.select2-producto-auto', function () {
        const fila = $(this).closest('tr');
        const option = $(this).find('option:selected');
        const productoId = option.val();

        fila.find('.marca-cell, .modelo-cell, .color-cell, .serie-cell').text('');
        fila.find('.cantidad-input').val('').prop('readonly', false);

        if (!productoId) return;

        const tieneSerie = option.data('tiene-serie') == true || option.data('tiene-serie') == 'true';
        const tieneHijos = option.data('tiene-hijos') == true || option.data('tiene-hijos') == 'true';

        fila.find('.marca-cell').text(option.data('marca') || '');
        fila.find('.modelo-cell').text(option.data('modelo') || '');
        fila.find('.color-cell').text(option.data('color') || '');

        if (tieneHijos) {
            const hijo = seleccionarHijoDisponible(productoId);
            if (tieneHijos) {
                const hijo = seleccionarHijoDisponible(productoId);
                if (hijo) {
                    fila.find('.serie-cell').text(hijo.numero_serie || '');
                    fila.find('.cantidad-input').val(1).prop('readonly', true);
                    let inputHijo = fila.find('input[name="producto_hijo_id[]"]');
                    if (inputHijo.length === 0) {
                        inputHijo = $('<input>', {
                            type: 'hidden',
                            name: 'producto_hijo_id[]'
                        }).appendTo(fila.find('.serie-cell'));
                    }
                    inputHijo.val(hijo.id);
                } else {
                    alert('No hay hijos disponibles para este producto.');
                    $(this).val('').trigger('change');
                }
            }
        } else {
            fila.find('.serie-cell').text(option.data('serie') || '');
        }
    });

    // Validación de cantidad
    $('#tabla-editar-salida').on('input', '.cantidad-input', function () {
        const input = $(this);
        const fila = input.closest('tr');
        const option = fila.find('.select2-producto-auto option:selected');
        const stock = option.data('stock');
        const val = parseInt(input.val());
        if (isNaN(val) || val < 1) {
            input.val(1);
        } else if (val > stock) {
            input.val(stock);
        }
    });

    // SELECT2 CON VALIDACIONES Y ESTILO GRIS
    function formatOption(option) {
        if (!option.id) return option.text;
        const valid = $(option.element).data('valid');
        if (valid === false || valid === 'false') {
            return `<span class="text-muted">${option.text}</span>`;
        }
        return option.text;
    }

    function inicializarSelectsSolicitudes() {
        const $modal = $('#form-editar-salida');

        $('#id_solicitante', $modal).select2({
            placeholder: 'Selecciona un solicitante',
            allowClear: true,
            theme: 'bootstrap4',
            width: '100%',
            dropdownParent: $modal,
            templateResult: formatOption,
            escapeMarkup: m => m
        });

        $('#id_unidad, #id_departamento', $modal).select2({
            placeholder: 'Selecciona…',
            allowClear: true,
            theme: 'bootstrap4',
            width: '100%',
            dropdownParent: $modal,
            templateResult: formatOption,
            escapeMarkup: m => m
        });

        // Triggers para autollenado y validación cruzada
        $('#id_solicitante').on('select2:select', function (e) {
            const datos = window.datosSolicitantes || {};
            const id = e.params.data.id;
            const u = datos[id]?.unidad_id;
            const d = datos[id]?.departamento_id;
            if (u) $('#id_unidad').val(u).trigger('change.select2');
            if (d) $('#id_departamento').val(d).trigger('change.select2');
        });

        $('#id_departamento').on('select2:select select2:clear', function () {
            actualizarValidacionesUnidad();
            filtrarSolicitantes();
        });

        $('#id_unidad').on('select2:select select2:clear', function () {
            actualizarValidacionesDepartamento();
            filtrarSolicitantes();
        });

        $('#id_unidad').on('select2:select', function (e) {
            if ($(e.params.data.element).data('valid') === false) {
                $('#id_departamento').val(null).trigger('change.select2');
            }
        });

        $('#id_departamento').on('select2:select', function (e) {
            if ($(e.params.data.element).data('valid') === false) {
                $('#id_unidad').val(null).trigger('change.select2');
            }
        });

        $('#id_solicitante option').data('valid', true);
        $('#id_unidad option').data('valid', true);
        $('#id_departamento option').data('valid', true);
    }

    function actualizarValidacionesUnidad() {
        const deptoId = Number($('#id_departamento').val());
        $('#id_unidad option').each(function () {
            const val = Number(this.value);
            const unidad = window.todosUnidadesCompleto.find(u => u.id === val);
            const valid = !deptoId || (unidad?.departamentos || []).includes(deptoId);
            $(this).data('valid', valid);
        });
        $('#id_unidad').trigger('change.select2');
    }

    function actualizarValidacionesDepartamento() {
        const unidadId = Number($('#id_unidad').val());
        $('#id_departamento option').each(function () {
            const val = Number(this.value);
            const unidad = window.todosUnidadesCompleto.find(u => u.id === unidadId);
            const valid = !unidadId || (unidad?.departamentos || []).includes(val);
            $(this).data('valid', valid);
        });
        $('#id_departamento').trigger('change.select2');
    }

    function filtrarSolicitantes() {
        const unidadId = $('#id_unidad').val();
        const deptoId  = $('#id_departamento').val();

        $('#id_solicitante option').each(function () {
            const sUni = $(this).data('unidad-id');
            const sDep = $(this).data('departamento-id');
            const valid = (!unidadId || sUni == unidadId) && (!deptoId || sDep == deptoId);
            $(this).data('valid', valid);
        });

        const selVal = $('#id_solicitante').val();
        const selValid = $('#id_solicitante option:selected').data('valid');
        if (selVal && selValid === false) {
            $('#id_solicitante').val(null).trigger('change.select2');
        }

        $('#id_solicitante').trigger('change.select2');
    }

    // SELECT2 PARA PRODUCTOS
    function inicializarSelectsProductos() {
        $('.select2-producto-auto').select2({
            theme: 'bootstrap4',
            width: 'resolve',
            placeholder: 'Selecciona producto...'
        });
    }

    // Actualizar opciones de productos al cargar
    function updateProductoOptions() {
        const counts = {};
        $('.select2-producto-auto').each(function () {
            const $sel = $(this);
            const val = $sel.val();
            const opt = $sel.find(`option[value="${val}"]`);
            const tieneSerie = opt.data('tiene-serie') === true || opt.data('tiene-serie') === 'true';

            if (val && !tieneSerie) {
                counts[val] = (counts[val] || 0) + 1;
            }
        });

        $('.select2-producto-auto').each(function () {
            const $sel = $(this);
            const current = $sel.val();

            $sel.find('option').each(function () {
                const $opt = $(this);
                const val = $opt.val();
                const tieneSerie = $opt.data('tiene-serie') === true || $opt.data('tiene-serie') === 'true';

                if (!val) return;

                let disable = false;
                if (!tieneSerie && counts[val] >= 1 && current !== val) {
                    disable = true;
                }
                $opt.prop('disabled', disable);
            });

            $sel.trigger('change.select2');
        });
    }

    // Construcción de fila
    function construirFilaVacia() {
        const usadosNormales = new Set();

        $('.select2-producto-auto').each(function () {
            const selectedId = Number($(this).val());
            const prod = window.todosProductos.find(p => p.id === selectedId);
            if (prod && !prod.esHijo && !prod.padre_id) {
                usadosNormales.add(selectedId);
            }
        });

        const opciones = window.todosProductos
            .filter(p => !p.esHijo)
            .map(p => {
                const esNormal = !p.tiene_hijos;
                const deshabilitar = esNormal && usadosNormales.has(p.id);
                return `
                    <option value="${p.id}" 
                            data-marca="${p.marca?.nombre || ''}"
                            data-modelo="${p.modelo || ''}"
                            data-color="${p.color || ''}"
                            data-serie="${p.numero_serie || ''}"
                            data-tiene-serie="${p.tiene_serie}"
                            data-tiene-hijos="${p.tiene_hijos}"
                            data-stock="${p.stock}"
                            data-padre-id="${p.padre_id || ''}"
                            data-estado="${p.estado}"
                            data-es-hijo="${p.esHijo || false}"
                            ${deshabilitar ? 'disabled' : ''}>
                        ${p.tipo?.nombre || 'Sin tipo'} – ${p.nombre}
                    </option>`;
            }).join('');

        return `
        <tr class="linea-form">
            <td>
                <select class="form-control select2-producto-auto" name="producto_id[]">
                    <option></option>
                    ${opciones}
                </select>
            </td>
            <td class="marca-cell"></td>
            <td class="modelo-cell"></td>
            <td class="color-cell"></td>
            <td class="serie-cell"></td>
            <td><input type="number" class="form-control cantidad-input" name="cantidad[]" min="1"></td>
            <td class="text-center"><button type="button" class="btn btn-sm btn-danger btn-eliminar-fila">&times;</button></td>
        </tr>`;
    }

        function seleccionarHijoDisponible(productoPadreId) {
            const hijosDeEsePadre = window.todosProductos.filter(p =>
                p.padre_id === Number(productoPadreId) &&
                p.estado === 'activo' &&  
                p.stock === 1            
            );
            const hijosYaUsados = $('input[name="producto_hijo_id[]"]')
                .map(function () {
                    return parseInt($(this).val());
                })
                .get()
                .filter(id => !isNaN(id));
            const hijosFiltrados = hijosDeEsePadre.filter(hijo => !hijosYaUsados.includes(hijo.id));
            return hijosFiltrados.length > 0 ? hijosFiltrados[0] : null;
        }
});