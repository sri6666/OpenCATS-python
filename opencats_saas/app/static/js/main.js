/**
 * OpenCATS SaaS - Main JavaScript
 */

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Confirm delete actions
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// Table row click navigation
document.addEventListener('DOMContentLoaded', function() {
    const clickableRows = document.querySelectorAll('tr[data-href]');
    clickableRows.forEach(function(row) {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function(e) {
            // Don't navigate if clicking on a button or link
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || e.target.closest('button') || e.target.closest('a')) {
                return;
            }
            window.location.href = row.dataset.href;
        });
    });
});

// Drag and drop for pipeline
function initPipelineDragDrop() {
    const cards = document.querySelectorAll('.pipeline-card');
    const columns = document.querySelectorAll('.pipeline-column');

    cards.forEach(card => {
        card.addEventListener('dragstart', dragStart);
        card.addEventListener('dragend', dragEnd);
    });

    columns.forEach(column => {
        column.addEventListener('dragover', dragOver);
        column.addEventListener('drop', drop);
        column.addEventListener('dragleave', dragLeave);
    });
}

function dragStart(e) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
    e.dataTransfer.setData('candidateId', this.dataset.candidateId);
    e.dataTransfer.setData('entryId', this.dataset.entryId);
    this.classList.add('dragging');
}

function dragEnd(e) {
    this.classList.remove('dragging');
}

function dragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('drag-over');
    return false;
}

function dragLeave(e) {
    this.classList.remove('drag-over');
}

function drop(e) {
    e.preventDefault();
    this.classList.remove('drag-over');

    const entryId = e.dataTransfer.getData('entryId');
    const newStatus = this.dataset.status;
    const jobId = this.dataset.jobId;

    // Update status via AJAX
    fetch(`/joborders/${jobId}/pipeline/${entryId}/update-status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload page to show updated pipeline
            location.reload();
        } else {
            alert('Error updating status: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating status');
    });

    return false;
}

// Get CSRF token from meta tag or form
function getCsrfToken() {
    const token = document.querySelector('input[name="csrf_token"]');
    if (token) {
        return token.value;
    }

    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
        return meta.content;
    }

    return '';
}

// Search with debounce
let searchTimeout;
function searchWithDebounce(searchUrl, delay = 500) {
    const searchInput = document.querySelector('input[name="search"]');
    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value;

        searchTimeout = setTimeout(function() {
            if (query.length >= 3 || query.length === 0) {
                window.location.href = searchUrl + '?search=' + encodeURIComponent(query);
            }
        }, delay);
    });
}

// Toggle hot status
function toggleHot(endpoint, id, type) {
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating status');
    });
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Initialize popovers
document.addEventListener('DOMContentLoaded', function() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Form validation
(function() {
    'use strict';
    window.addEventListener('load', function() {
        const forms = document.getElementsByClassName('needs-validation');
        Array.prototype.filter.call(forms, function(form) {
            form.addEventListener('submit', function(event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show toast notification
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-success border-0 position-fixed bottom-0 end-0 m-3';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-check-circle me-2"></i>Copied to clipboard!
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        setTimeout(() => toast.remove(), 3000);
    });
}

// Export table to CSV
function exportTableToCSV(filename = 'export.csv') {
    const table = document.querySelector('table');
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');

        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ');
            data = data.replace(/"/g, '""');
            row.push('"' + data + '"');
        }

        csv.push(row.join(','));
    }

    // Download CSV
    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Init drag and drop if pipeline exists
    if (document.querySelector('.pipeline-column')) {
        initPipelineDragDrop();
    }
});
