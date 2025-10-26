/**
 * Games Page JavaScript
 * Handles game filtering and delete confirmation modal
 */

// Simple tooltip toggle function
function toggleTooltip(event, button) {
    event.preventDefault();
    event.stopPropagation();

    const container = button.closest('.tooltip-container') || button.closest('.form-group');
    const tooltip = container ? container.querySelector('.info-tooltip') : null;

    if (!tooltip) {
        return;
    }

    // Close all other tooltips
    document.querySelectorAll('.info-tooltip.active').forEach(t => {
        if (t !== tooltip) {
            t.classList.remove('active');
        }
    });

    // Toggle this tooltip
    tooltip.classList.toggle('active');
}

// Game search/filter functionality
function filterGames() {
    const input = document.getElementById('gameSearch');
    if (!input) return;

    const filter = input.value.toUpperCase();
    const table = document.getElementById('gamesTable');
    if (!table) return;

    const tr = table.getElementsByTagName('tr');

    for (let i = 1; i < tr.length; i++) {
        const gameName = tr[i].getElementsByClassName('game-name')[0];
        if (gameName) {
            const textValue = gameName.textContent || gameName.innerText;
            if (textValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = '';
            } else {
                tr[i].style.display = 'none';
            }
        }
    }
}


// Delete confirmation modal
function confirmDelete(gameId, gameName) {
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
    const gameToDeleteSpan = document.getElementById('gameToDelete');
    if (gameToDeleteSpan) {
        gameToDeleteSpan.textContent = gameName;
    }

    // Update form action with correct game ID
    const deleteForm = document.getElementById('deleteForm');
    if (deleteForm) {
        deleteForm.action = `/admin/games/delete/${gameId}`;
    } else {
        if (window.showAlertModal) {
            showAlertModal({
                title: 'Error',
                message: 'Delete form not found. Please refresh the page.',
                type: 'error'
            });
        } else {
            alert('Error: Delete form not found. Please refresh the page.');
        }
        return;
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

function updateMultiplierExample() {
    const pointSchemeElement = document.getElementById('point_scheme');
    if (!pointSchemeElement) return;

    const multiplier = parseInt(pointSchemeElement.value) || 1;
    const helpText = pointSchemeElement.parentElement.querySelector('.help-text');

    if (helpText) {
        // Create simple example showing the multiplier effect
        const examples = [];
        for (let i = 1; i <= 6; i++) {
            examples.push(i * multiplier);
        }
        helpText.textContent = `Example: ${examples.join(' ')}`;
    }
}

const pointSchemeElement = document.getElementById('point_scheme');
if (pointSchemeElement) {
    updateMultiplierExample();
    // Update on 'input' for real-time feedback as user types
    pointSchemeElement.addEventListener('input', updateMultiplierExample);
    // Also update on 'change' for compatibility
    pointSchemeElement.addEventListener('change', updateMultiplierExample);
}

// Penalty management
let penaltyCount = 0;

function addPenalty(name = '', value = '', stackable = false) {
    const container = document.getElementById('penalties-container');
    if (!container) return;

    const penaltyDiv = document.createElement('div');
    penaltyDiv.className = 'penalty-item';
    penaltyDiv.dataset.penaltyId = penaltyCount;

    penaltyDiv.innerHTML = `
        <div class="form-row penalty-row">
            <div class="form-group">
                <label>Description</label>
                <input type="text" name="penalties[${penaltyCount}][name]"
                       class="form-control" placeholder="e.g., False start"
                       value="${name}" maxlength="100" required>
            </div>
            <div class="form-group">
                <label>Value</label>
                <input type="number" name="penalties[${penaltyCount}][value]"
                       class="form-control" placeholder="e.g., 5"
                       value="${value}" min="-999999" max="999999" required>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" name="penalties[${penaltyCount}][stackable]"
                           value="true" ${stackable ? 'checked' : ''}>
                    Stackable (can apply multiple times)
                </label>
            </div>
            <div class="form-group penalty-actions">
                <button type="button" class="btn btn-danger btn-sm remove-penalty-btn"
                        onclick="removePenalty(${penaltyCount})">
                    <i class="fas fa-trash"></i> Remove
                </button>
            </div>
        </div>
    `;

    container.appendChild(penaltyDiv);
    penaltyCount++;
}

function removePenalty(penaltyId) {
    const penaltyItem = document.querySelector(`[data-penalty-id="${penaltyId}"]`);
    if (penaltyItem) {
        penaltyItem.remove();
    }
}

// Scoring direction tile management
function initializeScoringTiles() {
    const tiles = document.querySelectorAll('.scoring-tile');
    const hiddenInput = document.getElementById('scoring_direction');

    if (!tiles.length || !hiddenInput) return;

    // Set initial active tile based on hidden input value
    const currentValue = hiddenInput.value || 'lower_better';
    tiles.forEach(tile => {
        if (tile.dataset.value === currentValue) {
            tile.classList.add('active');
        }
    });

    // Add click handlers
    tiles.forEach(tile => {
        tile.addEventListener('click', function() {
            // Remove active class from all tiles
            tiles.forEach(t => t.classList.remove('active'));

            // Add active class to clicked tile
            this.classList.add('active');

            // Update hidden input value
            hiddenInput.value = this.dataset.value;
        });
    });
}

// Toggle custom type input field
function toggleCustomType() {
    const typeSelect = document.getElementById('game-type-select');
    const customTypeGroup = document.getElementById('custom-type-group');
    const customTypeInput = document.getElementById('custom_type');

    if (!typeSelect || !customTypeGroup) return;

    if (typeSelect.value === 'custom') {
        customTypeGroup.style.display = 'block';
    } else {
        customTypeGroup.style.display = 'none';
        // Clear custom type if switching away from custom
        if (customTypeInput) customTypeInput.value = '';
    }
}

// Toggle between tournament mode and regular scoring
function toggleGameMode() {
    const tournamentCheckbox = document.getElementById('create_as_tournament');
    const scoringSection = document.getElementById('scoring-section');
    const penaltiesSection = document.getElementById('penalties-section');
    const roundsSection = document.getElementById('rounds-section');

    if (!tournamentCheckbox) return;

    if (tournamentCheckbox.checked) {
        if (scoringSection) scoringSection.style.display = 'none';
        if (penaltiesSection) penaltiesSection.style.display = 'none';
        if (roundsSection) roundsSection.style.display = 'none';
    } else {
        if (scoringSection) scoringSection.style.display = 'block';
        if (penaltiesSection) penaltiesSection.style.display = 'block';
        if (roundsSection) roundsSection.style.display = 'block';
    }
}

// Initialize game form-specific functionality
function initializeGameForm() {
    // Check if we're on an edit page and need to pre-fill custom type
    const typeSelect = document.getElementById('game-type-select');
    const customTypeInput = document.getElementById('custom_type');

    if (typeSelect && window.gameType) {
        // Check if current game type is not in standard options
        const standardTypes = ['trivia', 'physical', 'strategy', 'custom'];
        if (!standardTypes.includes(window.gameType)) {
            // Set to custom and show the field with the current value
            typeSelect.value = 'custom';
            if (customTypeInput) {
                customTypeInput.value = window.gameType;
            }
        }
    }

    // Initialize toggles
    toggleCustomType();
    toggleGameMode();

    // Set up event listeners for type select
    if (typeSelect) {
        typeSelect.addEventListener('change', toggleCustomType);
    }

    // Set up event listener for tournament checkbox
    const tournamentCheckbox = document.getElementById('create_as_tournament');
    if (tournamentCheckbox) {
        tournamentCheckbox.addEventListener('change', toggleGameMode);
    }
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up search input event listener
    const searchInput = document.getElementById('gameSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', filterGames);
    }

    // Set up delete button click handlers using event delegation
    const deleteButtons = document.querySelectorAll('.delete-game-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const gameId = this.dataset.gameId;
            const gameName = this.dataset.gameName;
            confirmDelete(gameId, gameName);
        });
    });

    // Also use event delegation on the table as a fallback
    const gamesTable = document.getElementById('gamesTable');
    if (gamesTable) {
        gamesTable.addEventListener('click', function(e) {
            // Check if the clicked element or its parent is a delete button
            const deleteBtn = e.target.closest('.delete-game-btn');
            if (deleteBtn) {
                e.preventDefault();
                e.stopPropagation();
                const gameId = deleteBtn.dataset.gameId;
                const gameName = deleteBtn.dataset.gameName;
                confirmDelete(gameId, gameName);
            }
        });
    }

    // Modal initialization
    const modal = document.getElementById('deleteModal');
    if (modal) {
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
                // Form will submit naturally
            });
        }
    }

    // Penalty management initialization
    const addPenaltyBtn = document.getElementById('add-penalty-btn');
    if (addPenaltyBtn) {
        addPenaltyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            addPenalty();
        });
    }

    // Load existing penalties if on edit page
    const existingPenalties = window.existingPenalties || [];
    existingPenalties.forEach(penalty => {
        addPenalty(penalty.name, penalty.value, penalty.stackable);
    });

    // Initialize scoring direction tiles
    initializeScoringTiles();

    // Initialize game form if on add/edit page
    initializeGameForm();

    // Info tooltip functionality
    initializeInfoTooltips();
});

// Initialize info tooltips (for help icons)
function initializeInfoTooltips() {
    const tooltipTriggers = document.querySelectorAll('.info-tooltip-trigger');
    tooltipTriggers.forEach((trigger, index) => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            // More robust tooltip finding - check both .tooltip-container and .form-group
            const container = this.closest('.tooltip-container') || this.closest('.form-group') || this.closest('.game-info-item-with-tooltip');

            const tooltip = container ? container.querySelector('.info-tooltip') : null;

            if (!tooltip) {
                return;
            }

            // Close all other tooltips first
            document.querySelectorAll('.info-tooltip.active').forEach(t => {
                if (t !== tooltip) {
                    t.classList.remove('active');
                }
            });

            // Toggle this tooltip
            const isActive = tooltip.classList.contains('active');
            tooltip.classList.toggle('active');
            console.log('Tooltip toggled, active:', !isActive);

            // Set up outside click handler only when opening
            if (!isActive) {
                setTimeout(() => {
                    const closeHandler = function(event) {
                        if (!tooltip.contains(event.target) && event.target !== trigger && !trigger.contains(event.target)) {
                            tooltip.classList.remove('active');
                            document.removeEventListener('click', closeHandler);
                        }
                    };
                    document.addEventListener('click', closeHandler);
                }, 0);
            }
        });
    });

    // Close button in tooltips
    const tooltipCloseButtons = document.querySelectorAll('.tooltip-close');
    tooltipCloseButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const tooltip = this.closest('.info-tooltip');
            if (tooltip) {
                tooltip.classList.remove('active');
            }
        });
    });
}
