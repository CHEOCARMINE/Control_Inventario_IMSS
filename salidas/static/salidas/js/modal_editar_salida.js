    function bloquearSelect2Visual($select) {
    const $container = $select.next('.select2-container');
    $container
        .find('.select2-selection')
        .css('pointer-events','none')
        .css('background-color','#eaecf4')
        .css('opacity','1')
        .css('cursor','not-allowed');
    }

$(document).ready(function () {

    inicializarSelectsProductos();
    inicializarSelectsSolicitudes();

    let totalForms = parseInt($('#id_form-TOTAL_FORMS').val());

    // Precargar datos de productos en las filas existentes
    $('.linea-form').each(function () {
        actualizarFilaPrecargada($(this));
        const $fila = $(this);
        const $select = $fila.find('.select2-producto-auto');
        const productoId = Number($fila.data('producto-id'));

        // Bloquear el select de producto
        bloquearSelect2Visual($select);

        // Buscar el producto en la lista global
        const producto = window.todosProductos.find(p => p.id === productoId);
        if (!producto) return;

        // Mostrar datos en las celdas
        $fila.find('.marca-cell').text(producto.marca?.nombre || '');
        $fila.find('.modelo-cell').text(producto.modelo || '');
        $fila.find('.color-cell').text(producto.color || '');

        if (producto.esHijo) {
            $fila.find('.serie-cell').text(producto.numero_serie || '');
            $fila.find('.cantidad-input')
                .val(1)
                .prop('readonly', true);

            // Agregar input hidden si no existe
            let inputHijo = $fila.find('input[name$="-producto_hijo_id"]');
            if (inputHijo.length === 0) {
                inputHijo = $('<input>', {
                    type: 'hidden',
                    name: `${$fila.data('form-index')}-producto_hijo_id`
                }).appendTo($fila.find('.serie-cell'));
            }
            inputHijo.val(producto.id);
        } else {
            $fila.find('.serie-cell').text(producto.numero_serie || '');
            $fila.find('.cantidad-input')
                .prop('readonly', false);
        }
    });

    // Refrescar opciones deshabilitadas al seleccionar o limpiar producto
    $('#tabla-editar-salida').on('select2:select select2:unselect', '.select2-producto-auto', function () {
        updateProductoOptions();
    });

    // Al cargar, aplicar deshabilitados iniciales
    updateProductoOptions();

    // Agregar fila nueva
    $('#btn-agregar-fila-edicion').on('click', function () {
        const nuevaFilaHtml = construirFilaVacia();
        $('#tabla-editar-salida tbody').append(nuevaFilaHtml);

        reindexarFormset();

        const $newRow = $('#tabla-editar-salida tbody tr.linea-form').last();
        $newRow.find('.select2-producto-auto').select2({
            theme: 'bootstrap4',
            width: 'resolve',
            placeholder: 'Selecciona producto...'
        });

        updateProductoOptions();

        $('.linea-form').each(function() {
            const $fila = $(this);
            if ($fila.data('producto-id')) {
                bloquearSelect2Visual($fila.find('.select2-producto-auto'));
            }
        });
    });

    // Eliminar fila
    $('#tabla-editar-salida').on('click', '.btn-eliminar-fila', function () {
        $(this).closest('tr').remove();
        reindexarFormset();
        updateProductoOptions();
    });

    // Al seleccionar producto
    $('#tabla-editar-salida').on('change', '.select2-producto-auto', function () {
        const $select = $(this);
        const $msg = $select.siblings('.mensaje-error-hijos');
        $msg.addClass('d-none');
        $select.removeClass('is-invalid');

        const fila = $select.closest('tr');
        const option = $select.find('option:selected');
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
            if (hijo) {
                fila.find('.serie-cell').text(hijo.numero_serie || '');
                fila.find('.cantidad-input').val(1).prop('readonly', true);
                let index = fila.data('form-index');
                let inputName = `form-${index}-producto_hijo_id`;
                let inputHijo = fila.find(`input[name="${inputName}"]`);
                if (inputHijo.length === 0) {
                    inputHijo = $('<input>', {
                        type: 'hidden',
                        name: inputName
                    }).appendTo(fila.find('.serie-cell'));
                }
                inputHijo.val(hijo.id);
        } else {
            fila.find('.serie-cell').text(option.data('serie') || '');
        }
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

        $('#id_solicitante option').data('valid', true);
        $('#id_unidad option').data('valid', true);
        $('#id_departamento option').data('valid', true);

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
        const index = $('.linea-form').length;

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
        <tr class="linea-form" data-form-index="${index}">
            <td>
                <select class="form-control select2-producto-auto" name="form-${index}-producto">
                    <option></option>
                    ${opciones}
                </select>
                <input type="hidden" name="form-${index}-producto_hijo_id">
                <div class="invalid-feedback d-none mensaje-error-hijos">
                    Este producto ya no tiene hijos disponibles.
                </div>
            </td>
            <td class="marca-cell"></td>
            <td class="modelo-cell"></td>
            <td class="color-cell"></td>
            <td class="serie-cell"></td>
            <td>
                <input type="number" class="form-control cantidad-input" name="form-${index}-cantidad" min="1">
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-danger btn-eliminar-fila">&times;</button>
            </td>
        </tr>`;
    }

    function seleccionarHijoDisponible(productoPadreId) {
        const hijosDeEsePadre = window.todosProductos.filter(p =>
            p.padre_id === Number(productoPadreId) &&
            p.estado === 'activo' &&  
            p.stock === 1            
        );
        const hijosYaUsados = $('input[name$="-producto_hijo_id"]')
            .map(function () {
                return parseInt($(this).val());
            })
            .get()
            .filter(id => !isNaN(id));
        const hijosFiltrados = hijosDeEsePadre.filter(hijo => !hijosYaUsados.includes(hijo.id));
        return hijosFiltrados.length > 0 ? hijosFiltrados[0] : null;
    }

    // Manejo del formulario de edición
    $(document).off('submit', '#form-editar-salida');
    $(document).on('submit', '#form-editar-salida', function(e) {
        e.preventDefault();

        reindexarFormset();

        var $form      = $(this);
        var actionUrl  = $form.attr('action');
        var formData   = $form.serialize();

        var numFilas = $('#tabla-editar-salida tbody tr.linea-form').length;
        if (numFilas < 1) {
            $('.cosma-flags-message').remove();
            $('#form-editar-salida .modal-body').prepend(
                `<div class="alert alert-danger alert-dismissible fade show cosma-flags-message" role="alert">
                    Debe agregar al menos una fila de productos.
                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                </div>`
            );
            return;
        }

        $.ajax({
            url:     actionUrl,
            method:  'POST',
            data:    formData,
            headers: {'X-Requested-With': 'XMLHttpRequest'},
            success: function(resp) {
                if (resp.success) {
                    $form.closest('.modal').modal('hide');
                    window.location.href = resp.redirect_url;
                } else {
                    const $modalBody = $form.closest('.modal').find('.modal-body');
                    $modalBody.html(resp.html_form);
                    inicializarSelectsProductos();
                    inicializarSelectsSolicitudes();
                    updateProductoOptions();
                    $modalBody.find('.linea-form').each(function () {
                        const $fila = $(this);
                        const productoId = $fila.data('producto-id');
                        const $select   = $fila.find('.select2-producto-auto');
                        if (productoId) {
                            $select.val(productoId).trigger('change');
                        }
                        actualizarFilaPrecargada($fila);
                    });
                    reindexarFormset();
                }
            },
            error: function() {
                alert('Error al guardar el vale.');
            }
        });
    });

    function actualizarFilaPrecargada($fila) {
        const productoId = Number($fila.find('.select2-producto-auto').val());
        const producto = window.todosProductos.find(p => p.id === productoId);
        if (!producto) return;

        bloquearSelect2Visual($fila.find('.select2-producto-auto'));
        $fila.find('.marca-cell').text(producto.marca?.nombre || '');
        $fila.find('.modelo-cell').text(producto.modelo || '');
        $fila.find('.color-cell').text(producto.color || '');
        $fila.find('.serie-cell').text(producto.numero_serie || '');

        const $cantidad = $fila.find('.cantidad-input');
        if (producto.esHijo || producto.tiene_serie) {
            $cantidad.val(1).prop('readonly', true);
            let index = $fila.data('form-index');
            let inputName = `form-${index}-producto_hijo_id`;
            let inputHijo = $fila.find(`input[name="${inputName}"]`);
            if (inputHijo.length === 0) {
                inputHijo = $('<input>', {
                    type: 'hidden',
                    name: inputName
                }).appendTo($fila.find('.serie-cell'));
            }
            inputHijo.val(producto.id);
        } else {
            $cantidad.prop('readonly', false);
        }
    }

    function reindexarFormset() {
        const filas = $('.linea-form');
        $('#id_form-TOTAL_FORMS').val(filas.length);
        filas.each(function (i) {
            $(this).attr('data-form-index', i);
            $(this).find(':input').each(function () {
                const name = $(this).attr('name');
                const id = $(this).attr('id');
                if (name) $(this).attr('name', name.replace(/form-\d+-/, `form-${i}-`));
                if (id) $(this).attr('id', id.replace(/id_form-\d+-/, `id_form-${i}-`));
            });
        });
    }
});