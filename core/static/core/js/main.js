// Loading overlay management
const loadingOverlay = document.createElement('div');
loadingOverlay.className = 'loading-overlay';
loadingOverlay.innerHTML = `
    <div class="spinner-border text-primary loading-spinner" role="status">
        <span class="visually-hidden">Loading...</span>
    </div>
`;
document.body.appendChild(loadingOverlay);

// Form management for dynamic formsets
function addForm(prefix) {
    showLoading();
    try {
        const totalForms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
        const currentForms = document.querySelectorAll(`.${prefix}-form`);
        const formNum = currentForms.length;
        const template = document.querySelector(`.${prefix}-form`).cloneNode(true);

        // Update form count
        totalForms.value = formNum + 1;

        // Update IDs and names
        template.innerHTML = template.innerHTML.replace(
            new RegExp(`${prefix}-\\d+`, 'g'),
            `${prefix}-${formNum}`
        );

        // Clear values
        template.querySelectorAll('input:not([type="hidden"])').forEach(input => {
            input.value = '';
        });
        template.querySelectorAll('select').forEach(select => {
            select.selectedIndex = 0;
        });

        // Add new form with animation
        template.style.opacity = '0';
        if (prefix === 'activity') {
            document.getElementById(`${prefix}-forms`).appendChild(template);
        } else {
            document.querySelector(`#${prefix}-table tbody`).appendChild(template);
        }

        // Fade in the new form
        setTimeout(() => {
            template.style.transition = 'opacity 0.3s ease-in';
            template.style.opacity = '1';
        }, 10);

        // Initialize any Bootstrap components in the new form
        template.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            new bootstrap.Tooltip(el);
        });

        // Add delete confirmation
        template.querySelectorAll('.delete-row').forEach(btn => {
            btn.addEventListener('click', function (e) {
                if (!confirm('Are you sure you want to remove this item?')) {
                    e.preventDefault();
                }
            });
        });

    } finally {
        hideLoading();
    }
}

// Initialize all components
document.addEventListener('DOMContentLoaded', function () {
    // Initialize Bootstrap components
    var tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    var popoverTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="popover"]')
    );
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Form submission loading state
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function () {
            if (!this.classList.contains('no-loading')) {
                showLoading();
            }
        });
    });

    // Add confirmation dialogs
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function (e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Form validation enhancement
    document.querySelectorAll('form:not(.no-validation)').forEach(form => {
        form.addEventListener('submit', function (e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    });

    // Auto-hide alerts after 5 seconds
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Add active states to navigation
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Prevent double form submission
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function (e) {
            if (this.hasAttribute('data-submitted')) {
                e.preventDefault();
            } else {
                this.setAttribute('data-submitted', 'true');
            }
        });
    });
});

// Expose loading overlay controls
window.showLoading = function () {
    loadingOverlay.classList.add('active');
};

window.hideLoading = function () {
    loadingOverlay.classList.remove('active');
};
