$(function() {
    $('body').on('click', '[data-remote]', function(e) {
        e.preventDefault();

        const url = $(this).data('remote');

        let targetId = $(this).data('bsTarget');
        if (!targetId) {
        targetId = $(this).attr('data-bs-target');
        }

        const $modalContent = $(`${targetId} .modal-content`);

        $modalContent.html('<div class="p-4 text-center">Cargando…</div>');

        $modalContent.load(url, function(response, status, xhr) {
        if (status !== 'success') {
            $modalContent.html('<div class="text-danger p-4">Error al cargar el formulario.</div>');
        } else {
            $(targetId).modal('show');
        }
        });
    });

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

        window.clearFilters = function() {
        filterForm.reset();
        window.location.href = baseUrl;
        };
    }
});

$(function() {
    // Cuando cambie la categoría, limpiamos subcategoria y tipo
    $('#id_categoria').on('change', function() {
        $('#id_subcategoria').val('');
        $('#id_tipo').val('');
    });

    // Cuando cambie la subcategoría, limpiamos tipo
    $('#id_subcategoria').on('change', function() {
        $('#id_tipo').val('');
    });
});
