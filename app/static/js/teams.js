/**
 * Teams Page JavaScript
 * Handles team filtering and delete confirmation modal
 */

// Team search/filter functionality
function filterTeams() {
    const input = document.getElementById('teamSearch');
    if (!input) return;

    const filter = input.value.toUpperCase();
    const table = document.getElementById('teamsTable');
    if (!table) return;

    const tr = table.getElementsByTagName('tr');

    for (let i = 1; i < tr.length; i++) {
        const teamName = tr[i].getElementsByClassName('team-name')[0];
        if (teamName) {
            const textValue = teamName.textContent || teamName.innerText;
            if (textValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = '';
            } else {
                tr[i].style.display = 'none';
            }
        }
    }
}

// Delete confirmation modal - TOP-DOWN style
function confirmDelete(teamId, teamName) {
    const modal = document.getElementById('deleteModal');
    if (!modal) {
        if (window.showAlertModal) {
            showAlertModal({
                title: 'Error',
                message: 'Delete modal not found. Please refresh the page.',
                type: 'error'
            });
        } else {
            alert('Error: Delete modal not found. Please refresh the page.');
        }
        return;
    }

    // Update modal content
    const teamToDeleteSpan = document.getElementById('teamToDelete');
    if (teamToDeleteSpan) {
        teamToDeleteSpan.textContent = teamName;
    }

    // Update form action with correct team ID
    const deleteForm = document.getElementById('deleteForm');
    if (deleteForm) {
        deleteForm.action = `/admin/teams/delete/${teamId}`;
    }

    // Show modal
    modal.style.display = 'block';

    // Prevent body scrolling when modal is open
    document.body.style.overflow = 'hidden';
}

// Close modal function
function closeModal() {
    const modal = document.getElementById('deleteModal');
    if (!modal) return;

    modal.style.display = 'none';

    // Re-enable body scrolling
    document.body.style.overflow = 'auto';
}

// Initialize modal event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up search input event listener
    const searchInput = document.getElementById('teamSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', filterTeams);
    }

    // Set up delete button click handlers using event delegation
    const deleteButtons = document.querySelectorAll('.delete-team-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const teamId = this.dataset.teamId;
            const teamName = this.dataset.teamName;
            confirmDelete(teamId, teamName);
        });
    });

    // Modal initialization
    const modal = document.getElementById('deleteModal');
    if (!modal) return; // Only run if modal exists (admin users)

    // Close button (X)
    const closeBtn = modal.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            closeModal();
        });
    }

    // Cancel button in modal
    const cancelBtn = modal.querySelector('.cancel-delete-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            closeModal();
        });
    }

    // Close when clicking outside modal content
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // ESC key to close modal
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.style.display === 'block') {
            closeModal();
        }
    });

    // Handle form submission
    const deleteForm = document.getElementById('deleteForm');
    if (deleteForm) {
        deleteForm.addEventListener('submit', function(e) {
            // Let the form submit naturally
        });
    }
});

// Optional: Add smooth scroll to top when page loads
window.addEventListener('load', function() {
    // Scroll to top smoothly if there's a success message
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});