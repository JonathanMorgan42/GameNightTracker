/**
 * Leaderboard View Toggle and Mobile Menu
 */

document.addEventListener('DOMContentLoaded', function() {
    // Leaderboard view toggle
    const tableViewBtn = document.getElementById('tableViewBtn');
    const cardViewBtn = document.getElementById('cardViewBtn');
    const tableView = document.getElementById('tableView');
    const cardView = document.getElementById('cardView');

    if (tableViewBtn && cardViewBtn && tableView && cardView) {
        const savedView = localStorage.getItem('leaderboardView') || 'table';
        switchView(savedView);

        tableViewBtn.addEventListener('click', () => switchView('table'));
        cardViewBtn.addEventListener('click', () => switchView('card'));

        function switchView(view) {
            if (view === 'card') {
                cardView.classList.remove('hidden');
                tableView.classList.add('hidden');
                cardViewBtn.classList.add('active');
                tableViewBtn.classList.remove('active');
                localStorage.setItem('leaderboardView', 'card');
            } else {
                tableView.classList.remove('hidden');
                cardView.classList.add('hidden');
                tableViewBtn.classList.add('active');
                cardViewBtn.classList.remove('active');
                localStorage.setItem('leaderboardView', 'table');
            }
        }
    }

    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.getElementById('navMenu');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            navMenu.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
            }
        });

        // Close menu when clicking a link
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
            });
        });
    }

    // Flash message dismiss functionality
    const dismissButtons = document.querySelectorAll('.flash-dismiss');
    dismissButtons.forEach(button => {
        button.addEventListener('click', function() {
            const flashMessage = this.closest('.flash-message');
            flashMessage.style.animation = 'slideOutUp 0.3s ease-out';
            setTimeout(() => {
                flashMessage.remove();
            }, 300);
        });
    });

    // Auto-dismiss success messages after 5 seconds
    const successMessages = document.querySelectorAll('.flash-message.success');
    successMessages.forEach(message => {
        setTimeout(() => {
            const dismissBtn = message.querySelector('.flash-dismiss');
            if (dismissBtn) dismissBtn.click();
        }, 5000);
    });

    // Info tooltip functionality
    const tooltipTriggers = document.querySelectorAll('.info-tooltip-trigger');
    tooltipTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const tooltip = this.parentElement.parentElement.querySelector('.info-tooltip');
            if (tooltip) {
                tooltip.classList.toggle('active');
            }
        });
    });

    // Close tooltip when clicking close button
    const tooltipCloseButtons = document.querySelectorAll('.tooltip-close');
    tooltipCloseButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const tooltip = this.closest('.info-tooltip');
            if (tooltip) {
                tooltip.classList.remove('active');
            }
        });
    });

    // Close tooltip when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.info-tooltip') && !e.target.closest('.info-tooltip-trigger')) {
            const activeTooltips = document.querySelectorAll('.info-tooltip.active');
            activeTooltips.forEach(tooltip => {
                tooltip.classList.remove('active');
            });
        }
    });
});

// Logout confirmation
const logoutLink = document.getElementById('logoutLink');
const cancelLogout = document.getElementById('cancelLogout');

if (logoutLink) {
    logoutLink.addEventListener('click', function(e) {
        e.preventDefault();
        const confirmBar = document.getElementById('logoutConfirmBar');
        if (confirmBar) {
            confirmBar.classList.remove('display-none');
            confirmBar.style.display = 'block';
        }
    });
}

if (cancelLogout) {
    cancelLogout.addEventListener('click', closeLogoutConfirm);
}

function closeLogoutConfirm() {
    const confirmBar = document.getElementById('logoutConfirmBar');
    if (confirmBar) {
        confirmBar.style.display = 'none';
        confirmBar.classList.add('display-none');
    }
}
