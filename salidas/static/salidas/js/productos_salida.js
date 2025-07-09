$(function () {
    const baseUrl = window.location.pathname;
    let typingTimer;
    const doneTypingInterval = 600;
    const filterForm = document.getElementById('filterForm');

    // Auto-submit de filtros
    if (filterForm) {
        document.querySelectorAll('.auto-submit').forEach(field => {
            field.addEventListener('keyup', () => {
                clearTimeout(typingTimer);
                typingTimer = setTimeout(() => filterForm.submit(), doneTypingInterval);
            });
            field.addEventListener('change', () => filterForm.submit());
        });

        window.clearFilters = function () {
            filterForm.reset();
            window.location.href = baseUrl;
        };
    }

    // Carrito de productos como array
    let carrito = JSON.parse(localStorage.getItem('carritoSalida') || '[]');

    function guardarCarrito() {
        localStorage.setItem('carritoSalida', JSON.stringify(carrito));
    }

    function actualizarContador() {
        $('#contador-productos').text(carrito.length);
    }

    function desactivarProducto(id, cantidad, esHijo) {
        const $btn = esHijo
            ? $(`.btn-agregar-hijo[data-id="${id}"]`)
            : $(`.btn-agregar-normal[data-id="${id}"]`);

        $btn.prop('disabled', true).text('Agregado');

        if (!esHijo) {
            $btn.closest('tr').find('.input-cantidad').val(cantidad).prop('disabled', true);
        }
    }

    function activarProducto(id) {
        const $btn = $(`.btn-agregar-normal[data-id="${id}"], .btn-agregar-hijo[data-id="${id}"]`);
        $btn.prop('disabled', false).text('Agregar');
        $btn.closest('tr').find('.input-cantidad').prop('disabled', false);
    }

    window.activarProducto = activarProducto;

    // Restaurar estado visual al iniciar
    setTimeout(() => {
        carrito.forEach(p => desactivarProducto(p.id, p.cantidad, p.esHijo));
    }, 100);

    // Agregar producto normal
    $('body').on('click', '.btn-agregar-normal', function () {
        const $btn = $(this);
        const $row = $btn.closest('tr');

        const id = $btn.data('id');
        const nombre = $btn.data('nombre');
        const stock = parseInt($btn.data('stock'), 10);
        const marca = $btn.data('marca') || '';
        const modelo = $btn.data('modelo') || '';
        const color = $btn.data('color') || '';
        const numero_serie = $btn.data('numero-serie') || '';

        const $input = $row.find('.input-cantidad');
        const cantidad = parseInt($input.val(), 10);

        // Refrescar carrito desde localStorage antes de verificar
        carrito = JSON.parse(localStorage.getItem('carritoSalida') || '[]');
        if (carrito.find(p => p.id == id)) {
            mostrarToast('Este producto ya fue agregado.');
            return;
        }

        if (isNaN(cantidad) || cantidad <= 0 || cantidad > stock) {
            $input.addClass('is-invalid');
            return;
        } else {
            $input.removeClass('is-invalid');
        }

        carrito.push({
            id, nombre, cantidad, stock, esHijo: false,
            marca, modelo, color, numero_serie
        });

        guardarCarrito();
        desactivarProducto(id, cantidad, false);
        actualizarContador();
    });

    // Agregar producto hijo
    $('body').on('click', '.btn-agregar-hijo', function () {
        const $btn = $(this);
        const id = $btn.data('id');
        const nombre = $btn.data('nombre');
        const marca = $btn.data('marca') || '';
        const modelo = $btn.data('modelo') || '';
        const color = $btn.data('color') || '';
        const numero_serie = $btn.data('numero-serie') || '';

        // Refrescar carrito desde localStorage antes de verificar
        carrito = JSON.parse(localStorage.getItem('carritoSalida') || '[]');
        if (carrito.find(p => p.id == id)) {
            mostrarToast('Este producto hijo ya fue agregado.');
            return;
        }

        carrito.push({
            id, nombre, cantidad: 1, esHijo: true,
            marca, modelo, color, numero_serie
        });

        guardarCarrito();
        desactivarProducto(id, 1, true);
        actualizarContador();
    });

    // Exponer para otros scripts
    window.carritoSalida = carrito;

    // Mostrar toast
    function mostrarToast(mensaje) {
        const toast = $('<div class="toast bg-warning text-dark" role="alert" style="position: fixed; top: 1rem; right: 1rem; z-index: 9999;">' +
            '<div class="toast-body">' + mensaje + '</div></div>');
        $('body').append(toast);
        toast.toast({ delay: 2500 });
        toast.toast('show');
        setTimeout(() => toast.remove(), 3000);
    }

    // Modal por AJAX
    $('body').on('click', '[data-remote]', function (e) {
        e.preventDefault();
        const url = $(this).data('remote');
        const targetId = $(this).attr('data-bs-target');
        const $modalContent = $(`${targetId} .modal-content`);
        $modalContent.html('<div class="p-4 text-center">Cargando…</div>');

        $modalContent.load(url, function (response, status) {
            if (status !== 'success') {
                $modalContent.html('<div class="text-danger p-4">Error al cargar el formulario.</div>');
            } else {
                $(targetId).modal('show');
            }
        });
    });

    actualizarContador();
});