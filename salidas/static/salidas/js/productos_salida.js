$(function () {
    // Auto-submit de filtros (nombre, categoría, etc.)
    const baseUrl = window.location.pathname;
    let typingTimer;
    const doneTypingInterval = 600;
    const filterForm = document.getElementById('filterForm');

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

    // Acción para productos hijos (sin cantidad)
    window.agregarProductoHijo = function (productoId) {
        // Aquí puedes agregar lógica para añadir directamente al carrito
        // sin necesidad de cantidad (producto hijo)
        console.log('Agregar producto hijo ID:', productoId);

        // Ejemplo básico de acción (ajusta según tu estructura):
        alert('Producto hijo agregado al carrito (ID: ' + productoId + ')');
    };

    // Acción para productos normales (con cantidad)
    window.abrirModalAgregar = function (productoId, nombre, stock) {
        // Puedes personalizar esto para abrir tu modal personalizado
        console.log('Agregar producto normal ID:', productoId);

        // Ejemplo de comportamiento básico
        const cantidad = prompt(`¿Cuántas unidades deseas agregar de "${nombre}"? (máximo ${stock})`);
        if (cantidad !== null) {
        const qty = parseInt(cantidad, 10);
        if (!isNaN(qty) && qty > 0 && qty <= stock) {
            // Aquí podrías agregar al carrito o enviar por AJAX
            alert(`Agregado: ${qty} unidades de "${nombre}" (ID: ${productoId})`);
        } else {
            alert('Cantidad inválida.');
        }
        }
    };
});
