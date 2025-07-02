$(function() {
    // Inicializador de Select2 para Subcategoría y Unidad
    function initSelect2Tipo($container) {
    $container.find('.select2-subcategoria, .select2-unidad').each(function() {
        const $sel = $(this);
        const curr = $sel.val();             
        $sel.select2({
        theme: 'bootstrap4',
        placeholder: $sel.hasClass('select2-subcategoria')
            ? 'Selecciona subcategoría…'
            : 'Selecciona unidad…',
        width: '100%',
        dropdownParent: $container.closest('.modal'),
        minimumResultsForSearch: 0
        });
        if (!curr) {
        $sel.val(null).trigger('change');
        }
    });
    }

    // GET AJAX: abrir modal y cargar formulario
    $('body').on('click', '[data-remote]', function(e) {
        e.preventDefault();
        const url = $(this).data('remote');
        const $modalContent = $('#modal .modal-content');

        $modalContent
        .html('<div class="p-4 text-center">Cargando…</div>')
        .load(url, function(response, status) {
            if (status !== 'success') {
            $modalContent.html('<div class="text-danger p-4">Error al cargar el formulario.</div>');
            } else {
            // tras carga exitosa:
            initSelect2Tipo($modalContent);
            bindFormTipo();
            $('#modal').modal('show');
            }
        });
    });

    // POST AJAX: captura submit y re-render en errores
    function bindFormTipo() {
    $('#form-tipo')
        .off('submit')
        .on('submit', function(e) {
        e.preventDefault();
        const form = $(this);
        $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: form.serialize(),
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).done(res => {
            if (res.success) {
            $('#modal').modal('hide');
            window.location = res.redirect_url;
            } else {
            // **Reemplazamos sólo los campos, no todo el modal-content**
            $('#tipo-form-fields').html(res.html_form);

            // Re-inicializamos Select2 y el binding sobre el nuevo contenido
            initSelect2Tipo($('#modal .modal-content'));
            bindFormTipo();
            }
        }).fail(() => {
            alert('Error de red. Intenta de nuevo.');
        });
        });
    }

    // Lanzar binding inicial (por si hay un formulario ya en DOM)
    bindFormTipo();

    // Filtros auto-submit (si aplican)
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
        window.clearFilters = () => {
        filterForm.reset();
        window.location.href = baseUrl;
        };
    }
});
