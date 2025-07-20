$(document).ready(function () {
    inicializarSelects();

    // Agregar fila nueva
    $('#btn-agregar-fila-edicion').on('click', function () {
        const nuevaFila = construirFilaVacia();
        $('#tabla-editar-salida tbody').append(nuevaFila);
        inicializarSelects();
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

        // Vaciar campos
        fila.find('.marca-cell').text('');
        fila.find('.modelo-cell').text('');
        fila.find('.color-cell').text('');
        fila.find('.serie-cell').text('');
        fila.find('.cantidad-input').val('').prop('readonly', false);

        if (!productoId) return;

        const tieneSerie = option.data('tiene-serie') === true || option.data('tiene-serie') === 'true';
        const tieneHijos = option.data('tiene-hijos') === true || option.data('tiene-hijos') === 'true';

        // Pintar datos base
        fila.find('.marca-cell').text(option.data('marca') || '');
        fila.find('.modelo-cell').text(option.data('modelo') || '');
        fila.find('.color-cell').text(option.data('color') || '');

        // Si es producto padre
        if (tieneHijos) {
        const hijo = seleccionarHijoDisponible(productoId);
        if (hijo) {
            fila.find('.serie-cell').text(hijo.numero_serie || '');
            fila.find('.cantidad-input').val(1).prop('readonly', true);
            fila.attr('data-producto-hijo-id', hijo.id);
        } else {
            alert('No hay hijos disponibles para este producto.');
            $(this).val('').trigger('change');
        }
        } else {
        // Producto normal
        fila.find('.serie-cell').text(option.data('serie') || '');
        fila.find('.cantidad-input').prop('readonly', false);
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
    });

    function inicializarSelects() {
    $('.select2-producto-auto').select2({
        theme: 'bootstrap4',
        width: 'resolve',
        placeholder: 'Selecciona producto...'
    });
    }

    function construirFilaVacia() {
    return `
        <tr class="linea-form">
        <td>
            <select class="form-control select2-producto-auto">
            <option></option>
            ${window.todosProductos.map(p => `
                <option value="${p.id}"
                data-marca="${p.marca.nombre}"
                data-modelo="${p.modelo}"
                data-color="${p.color}"
                data-serie="${p.numero_serie || ''}"
                data-tiene-serie="${p.tiene_serie}"
                data-tiene-hijos="${p.tiene_hijos}"
                data-stock="${p.stock}">
                ${p.tipo.nombre} – ${p.nombre}
                </option>
            `).join('')}
            </select>
        </td>
        <td class="marca-cell"></td>
        <td class="modelo-cell"></td>
        <td class="color-cell"></td>
        <td class="serie-cell"></td>
        <td><input type="number" class="form-control cantidad-input" min="1"></td>
        <td class="text-center"><button type="button" class="btn btn-sm btn-danger btn-eliminar-fila">&times;</button></td>
        </tr>
    `;
    }

    function seleccionarHijoDisponible(productoPadreId) {
    // Buscar hijo activo y con stock 1 del padre
    for (let prod of window.todosProductos) {
        if (prod.padre_id === productoPadreId && prod.estado === 'activo' && prod.stock === 1) {
        return prod;
        }
    }
    return null;
}