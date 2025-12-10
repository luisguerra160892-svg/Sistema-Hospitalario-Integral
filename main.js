// ============================================
// SISTEMA HOSPITALARIO - JAVASCRIPT PRINCIPAL
// ============================================

$(document).ready(function() {
    // ============================================
    // INICIALIZACION GENERAL
    // ============================================
    
    // Activar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            delay: { show: 500, hide: 100 }
        });
    });
    
    // Activar popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // ============================================
    // ANIMACIONES DE ENTRADA
    // ============================================
    
    // Animar elementos al hacer scroll
    function animateOnScroll() {
        $('.animate-on-scroll').each(function() {
            var elementTop = $(this).offset().top;
            var elementBottom = elementTop + $(this).outerHeight();
            var viewportTop = $(window).scrollTop();
            var viewportBottom = viewportTop + $(window).height();
            
            if (elementBottom > viewportTop && elementTop < viewportBottom) {
                $(this).addClass('animate__animated animate__fadeInUp');
            }
        });
    }
    
    // Ejecutar al cargar y al hacer scroll
    animateOnScroll();
    $(window).scroll(animateOnScroll);
    
    // ============================================
    // MANEJO DE FORMULARIOS MEJORADO
    // ============================================
    
    // Validación en tiempo real
    $('.needs-validation').on('submit', function(event) {
        if (!this.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Mostrar/ocultar contraseña
    $('.toggle-password').click(function() {
        var input = $(this).closest('.input-group').find('input');
        var icon = $(this).find('i');
        
        if (input.attr('type') === 'password') {
            input.attr('type', 'text');
            icon.removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            input.attr('type', 'password');
            icon.removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });
    
    // Contador de caracteres para textareas
    $('textarea[maxlength]').each(function() {
        var maxLength = $(this).attr('maxlength');
        var $counter = $('<small class="text-muted float-end character-counter"></small>');
        $(this).after($counter);
        
        function updateCounter() {
            var currentLength = $(this).val().length;
            var remaining = maxLength - currentLength;
            $counter.text(remaining + ' caracteres restantes');
            
            if (remaining < 0) {
                $counter.addClass('text-danger');
            } else if (remaining < 50) {
                $counter.addClass('text-warning');
            } else {
                $counter.removeClass('text-danger text-warning');
            }
        }
        
        $(this).on('input', updateCounter);
        updateCounter.call(this);
    });
    
    // ============================================
    // TABLAS MEJORADAS
    // ============================================
    
    // Ordenamiento de tablas
    $('.sortable-table th.sortable').click(function() {
        var table = $(this).closest('table');
        var rows = table.find('tbody tr').toArray();
        var column = $(this).index();
        var direction = $(this).hasClass('asc') ? -1 : 1;
        
        // Cambiar icono de ordenamiento
        table.find('th.sortable i').removeClass('fa-sort-up fa-sort-down').addClass('fa-sort');
        if (direction === 1) {
            $(this).find('i').removeClass('fa-sort').addClass('fa-sort-up');
            $(this).addClass('asc').removeClass('desc');
        } else {
            $(this).find('i').removeClass('fa-sort').addClass('fa-sort-down');
            $(this).addClass('desc').removeClass('asc');
        }
        
        // Ordenar filas
        rows.sort(function(a, b) {
            var aVal = $(a).find('td').eq(column).text().trim();
            var bVal = $(b).find('td').eq(column).text().trim();
            
            // Intentar convertir a números si es posible
            if ($.isNumeric(aVal) && $.isNumeric(bVal)) {
                return (parseFloat(aVal) - parseFloat(bVal)) * direction;
            }
            
            return aVal.localeCompare(bVal) * direction;
        });
        
        // Reorganizar tabla
        $.each(rows, function(index, row) {
            table.find('tbody').append(row);
        });
    });
    
    // Búsqueda en tablas
    $('.table-search').on('input', function() {
        var searchTerm = $(this).val().toLowerCase();
        var tableId = $(this).data('table');
        
        $('#' + tableId + ' tbody tr').each(function() {
            var rowText = $(this).text().toLowerCase();
            $(this).toggle(rowText.indexOf(searchTerm) > -1);
        });
    });
    
    // ============================================
    // SISTEMA DE NOTIFICACIONES
    // ============================================
    
    // Mostrar notificación toast
    window.showNotification = function(title, message, type) {
        var toastHtml = `
            <div class="toast align-items-center text-bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <strong>${title}</strong><br>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        var $toast = $(toastHtml);
        $('#toast-container').append($toast);
        
        var toast = new bootstrap.Toast($toast[0], {
            delay: 5000,
            autohide: true
        });
        
        toast.show();
        
        // Remover después de ocultar
        $toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    };
    
    // ============================================
    // DASHBOARD - ACTUALIZACIONES EN TIEMPO REAL
    // ============================================
    
    // Actualizar estadísticas periódicamente (cada 60 segundos)
    if ($('.dashboard-stats').length) {
        setInterval(function() {
            $.ajax({
                url: '/api/dashboard/stats',
                method: 'GET',
                success: function(data) {
                    updateDashboardStats(data);
                }
            });
        }, 60000);
    }
    
    function updateDashboardStats(stats) {
        for (var key in stats) {
            var element = $('[data-stat="' + key + '"]');
            if (element.length) {
                var current = parseInt(element.text().replace(/,/g, ''));
                var target = stats[key];
                
                // Animar el cambio
                animateCounter(element[0], current, target, 1000);
            }
        }
    }
    
    function animateCounter(element, start, end, duration) {
        var range = end - start;
        var startTime = null;
        
        function updateCounter(timestamp) {
            if (!startTime) startTime = timestamp;
            var progress = timestamp - startTime;
            var percentage = Math.min(progress / duration, 1);
            
            var value = Math.floor(start + (range * percentage));
            element.textContent = value.toLocaleString();
            
            if (percentage < 1) {
                requestAnimationFrame(updateCounter);
            }
        }
        
        requestAnimationFrame(updateCounter);
    }
    
    // ============================================
    // CALENDARIO INTERACTIVO
    // ============================================
    
    $('.calendar-day').click(function() {
        var date = $(this).data('date');
        if (date) {
            $.ajax({
                url: '/citas/dia/' + date,
                method: 'GET',
                success: function(data) {
                    $('#appointments-modal .modal-body').html(data);
                    var modal = new bootstrap.Modal(document.getElementById('appointments-modal'));
                    modal.show();
                }
            });
        }
    });
    
    // ============================================
    // SISTEMA DE CARGAS Y ESTADOS
    // ============================================
    
    // Mostrar loader en botones de acción
    $(document).on('click', '.btn-loading', function() {
        var $btn = $(this);
        var originalText = $btn.html();
        
        $btn.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...');
        $btn.prop('disabled', true);
        
        // Restaurar después de 30 segundos por si hay error
        setTimeout(function() {
            $btn.html(originalText);
            $btn.prop('disabled', false);
        }, 30000);
    });
    
    // ============================================
    // MANEJO DE ARCHIVOS
    // ============================================
    
    // Mostrar vista previa de imagen
    $('#file-upload').change(function() {
        var file = this.files[0];
        if (file && file.type.match('image.*')) {
            var reader = new FileReader();
            
            reader.onload = function(e) {
                $('#image-preview').attr('src', e.target.result).show();
            };
            
            reader.readAsDataURL(file);
        }
    });
    
    // ============================================
    // SISTEMA DE BUSQUEDA AVANZADA
    // ============================================
    
    $('#advanced-search-toggle').click(function() {
        $('#advanced-search').slideToggle(300);
        $(this).find('i').toggleClass('fa-chevron-down fa-chevron-up');
    });
    
    // ============================================
    // SELECT2 INTEGRATION (si está cargado)
    // ============================================
    
    if ($.fn.select2) {
        $('.select2').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Seleccione una opción',
            allowClear: true
        });
    }
    
    // ============================================
    // CHARTS - Inicialización
    // ============================================
    
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    function initializeCharts() {
        // Gráfico de pacientes por mes
        var patientChartCtx = document.getElementById('patientChart');
        if (patientChartCtx) {
            new Chart(patientChartCtx, {
                type: 'line',
                data: {
                    labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Pacientes Nuevos',
                        data: [65, 59, 80, 81, 56, 55],
                        borderColor: '#2c6c9c',
                        backgroundColor: 'rgba(44, 108, 156, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    }
                }
            });
        }
        
        // Gráfico de tipos de consulta
        var consultationChartCtx = document.getElementById('consultationChart');
        if (consultationChartCtx) {
            new Chart(consultationChartCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Control', 'Urgencia', 'Primera Vez', 'Especialidad'],
                    datasets: [{
                        data: [35, 25, 20, 20],
                        backgroundColor: [
                            '#28a745',
                            '#ff6b6b',
                            '#2c6c9c',
                            '#ffc107'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    cutout: '70%',
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }
    
    // ============================================
    // SISTEMA DE FILTROS DINÁMICOS
    // ============================================
    
    $('.filter-option').change(function() {
        applyFilters();
    });
    
    function applyFilters() {
        var filters = {};
        
        $('.filter-option').each(function() {
            var name = $(this).data('filter');
            var value = $(this).val();
            
            if (value && value !== 'all') {
                filters[name] = value;
            }
        });
        
        // Enviar filtros al servidor o filtrar localmente
        if (Object.keys(filters).length > 0) {
            window.location.search = $.param(filters);
        } else {
            window.location.search = '';
        }
    }
    
    // ============================================
    // MANEJO DE ESTADOS (URGENTE, COMPLETADO, ETC)
    // ============================================
    
    $('.status-toggle').click(function() {
        var $btn = $(this);
        var id = $btn.data('id');
        var currentStatus = $btn.data('status');
        var newStatus = $btn.data('target-status');
        var url = $btn.data('url');
        
        $.ajax({
            url: url,
            method: 'POST',
            data: {
                id: id,
                status: newStatus,
                _token: $('meta[name="csrf-token"]').attr('content')
            },
            success: function(response) {
                if (response.success) {
                    // Actualizar botón
                    $btn.data('status', newStatus);
                    $btn.removeClass('btn-' + getStatusClass(currentStatus))
                        .addClass('btn-' + getStatusClass(newStatus))
                        .html('<i class="fas ' + getStatusIcon(newStatus) + '"></i> ' + getStatusText(newStatus));
                    
                    // Actualizar badge si existe
                    var $badge = $('[data-status-id="' + id + '"]');
                    if ($badge.length) {
                        $badge.removeClass('badge-' + getStatusClass(currentStatus))
                              .addClass('badge-' + getStatusClass(newStatus))
                              .text(getStatusText(newStatus));
                    }
                    
                    showNotification('Estado Actualizado', 'El estado ha sido cambiado exitosamente', 'success');
                }
            }
        });
    });
    
    function getStatusClass(status) {
        var classes = {
            'pending': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
            'in_progress': 'info'
        };
        return classes[status] || 'secondary';
    }
    
    function getStatusIcon(status) {
        var icons = {
            'pending': 'fa-clock',
            'completed': 'fa-check-circle',
            'cancelled': 'fa-times-circle',
            'in_progress': 'fa-spinner'
        };
        return icons[status] || 'fa-circle';
    }
    
    function getStatusText(status) {
        var texts = {
            'pending': 'Pendiente',
            'completed': 'Completado',
            'cancelled': 'Cancelado',
            'in_progress': 'En Progreso'
        };
        return texts[status] || status;
    }
    
    // ============================================
    // EXPORTACIÓN DE DATOS
    // ============================================
    
    $('.export-btn').click(function() {
        var format = $(this).data('format');
        var url = $(this).data('url');
        
        // Mostrar modal de exportación
        $('#exportModal').modal('show');
        
        // Configurar formulario de exportación
        $('#exportFormat').val(format);
        $('#exportForm').attr('action', url);
    });
    
    // ============================================
    // IMPRESIÓN MEJORADA
    // ============================================
    
    $('.print-btn').click(function() {
        var $printSection = $($(this).data('target'));
        
        // Crear ventana de impresión
        var printWindow = window.open('', '_blank');
        printWindow.document.write('<html><head><title>Impresión</title>');
        
        // Incluir estilos básicos
        printWindow.document.write(`
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .print-header { margin-bottom: 30px; }
                .print-footer { margin-top: 30px; font-size: 12px; color: #666; }
            </style>
        `);
        
        printWindow.document.write('</head><body>');
        printWindow.document.write($printSection.html());
        printWindow.document.write('</body></html>');
        printWindow.document.close();
        
        // Esperar a que cargue y luego imprimir
        printWindow.onload = function() {
            printWindow.print();
            printWindow.close();
        };
    });
    
    // ============================================
    // SISTEMA DE COPIADO AL PORTAPAPELES
    // ============================================
    
    $('.copy-btn').click(function() {
        var text = $(this).data('text');
        var $temp = $('<input>');
        $('body').append($temp);
        $temp.val(text).select();
        document.execCommand('copy');
        $temp.remove();
        
        // Mostrar feedback
        var $original = $(this).html();
        $(this).html('<i class="fas fa-check"></i> Copiado');
        
        setTimeout(function() {
            $(this).html($original);
        }.bind(this), 2000);
    });
    
    // ============================================
    // AUTOCOMPLETADO DE BÚSQUEDA
    // ============================================
    
    $('.autocomplete-input').each(function() {
        var $input = $(this);
        var url = $input.data('url');
        
        $input.autocomplete({
            source: function(request, response) {
                $.ajax({
                    url: url,
                    dataType: 'json',
                    data: {
                        term: request.term
                    },
                    success: function(data) {
                        response(data);
                    }
                });
            },
            minLength: 2,
            select: function(event, ui) {
                $input.val(ui.item.label);
                $('#' + $input.data('target')).val(ui.item.value);
                return false;
            }
        });
    });
    
    // ============================================
    // MANEJO DE SESIÓN Y TIMEOUT
    // ==========
     // Mostrar advertencia antes de que expire la sesión
    var idleTime = 0;
    
    function resetIdleTime() {
        idleTime = 0;
    }
    
    $(document).on('mousemove keypress scroll click', resetIdleTime);
    
    setInterval(function() {
        idleTime++;
        
        if (idleTime > 25 * 60) { // 25 minutos
            showNotification('Sesión a punto de expirar', 'Tu sesión expirará en 5 minutos', 'warning');
        }
        
        if (idleTime > 30 * 60) { // 30 minutos
            window.location.href = '/auth/logout?timeout=1';
        }
    }, 60000); // Verificar cada minuto
    
    // ============================================
    // RESPONSIVE MENU MEJORADO
    // ============================================
    
    // Ajustar menú para móviles
    function adjustMenuForMobile() {
        if ($(window).width() < 768) {
            $('.dropdown-menu').addClass('dropdown-menu-mobile');
            $('.nav-item.dropdown').addClass('mobile-dropdown');
        } else {
            $('.dropdown-menu').removeClass('dropdown-menu-mobile');
            $('.nav-item.dropdown').removeClass('mobile-dropdown');
        }
    }
    
    adjustMenuForMobile();
    $(window).resize(adjustMenuForMobile);
    
    // ============================================
    // ANIMACIONES DE CARGA PAGINADA
    // ============================================
    
    // Carga infinita para listas largas
    var loading = false;
    var page = 1;
    
    $(window).scroll(function() {
        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 100) {
            if (!loading && $('#load-more').length) {
                loadMoreItems();
            }
        }
    });
    
    function loadMoreItems() {
        loading = true;
        page++;
        
        $.ajax({
            url: $('#load-more').data('url') + '?page=' + page,
            method: 'GET',
            success: function(data) {
                if (data.html) {
                    $('#items-container').append(data.html);
                    if (!data.has_more) {
                        $('#load-more').hide();
                    }
                }
                loading = false;
            }
        });
    }
    
    // ============================================
    // FINAL - INICIALIZACIONES FINALES
    // ============================================
    
    // Actualizar hora actual
    function updateCurrentTime() {
        var now = new Date();
        var timeString = now.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
        var dateString = now.toLocaleDateString('es-ES', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        $('.current-time').text(timeString);
        $('.current-date').text(dateString);
    }
    
    updateCurrentTime();
    setInterval(updateCurrentTime, 60000); // Actualizar cada minuto
    
    // Inicializar todos los componentes
    console.log('Sistema Hospitalario - JavaScript inicializado correctamente');
});
```