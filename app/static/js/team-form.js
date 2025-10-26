/**
 * Team Form JavaScript - Add/Edit Team Pages
 * Handles color picker preview and dynamic participant management
 */

// Color picker functionality
function initializeColorPicker() {
    const colorInput = document.getElementById('color');
    const colorPreview = document.getElementById('colorPreview');
    const colorValue = document.getElementById('colorValue');

    if (colorInput && colorPreview && colorValue) {
        function updatePreview() {
            const color = colorInput.value;
            colorPreview.style.backgroundColor = color;
            colorValue.textContent = color.toUpperCase();
        }

        colorInput.addEventListener('input', updatePreview);
        updatePreview();
    }
}

// Dynamic participant management
let nextParticipantIndex = 3; // Start from participant 3
let visibleParticipants = [1, 2]; // Track which participants are visible

function addParticipant() {
    if (nextParticipantIndex > 6) {
        if (window.showAlertModal) {
            showAlertModal({
                title: 'Maximum Reached',
                message: 'Maximum of 6 team members allowed.',
                type: 'info'
            });
        } else {
            alert('Maximum of 6 team members allowed');
        }
        return;
    }

    // Show the next hidden participant section
    const section = document.getElementById(`participant-section-${nextParticipantIndex}`);
    if (section) {
        section.style.display = 'block';
        visibleParticipants.push(nextParticipantIndex);
        nextParticipantIndex++;

        // Hide the add button if we've reached the maximum
        if (nextParticipantIndex > 6) {
            const addBtn = document.getElementById('add-participant-btn');
            if (addBtn) addBtn.style.display = 'none';
        }
    }
}

function removeParticipant(index) {
    const section = document.getElementById(`participant-section-${index}`);
    if (section) {
        // Clear the input fields
        const firstNameInput = document.getElementById(`participant${index}FirstName`);
        const lastNameInput = document.getElementById(`participant${index}LastName`);

        if (firstNameInput) firstNameInput.value = '';
        if (lastNameInput) lastNameInput.value = '';

        // Hide the section
        section.style.display = 'none';

        // Remove from visible participants
        visibleParticipants = visibleParticipants.filter(p => p !== index);

        // Update nextParticipantIndex to the lowest hidden participant
        nextParticipantIndex = 3;
        for (let i = 3; i <= 6; i++) {
            if (!visibleParticipants.includes(i)) {
                nextParticipantIndex = i;
                break;
            }
        }

        // Show the add button again
        const addBtn = document.getElementById('add-participant-btn');
        if (addBtn) addBtn.style.display = 'inline-flex';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize color picker
    initializeColorPicker();

    // Set up add participant button
    const addBtn = document.getElementById('add-participant-btn');
    if (addBtn) {
        addBtn.addEventListener('click', addParticipant);
    }

    // Set up remove participant buttons using event delegation
    document.addEventListener('click', function(e) {
        if (e.target.closest('.remove-participant-btn')) {
            const btn = e.target.closest('.remove-participant-btn');
            const participantIndex = parseInt(btn.dataset.participantIndex);
            removeParticipant(participantIndex);
        }
    });

    // For edit page: Show existing participants
    for (let i = 3; i <= 6; i++) {
        const firstNameInput = document.getElementById(`participant${i}FirstName`);
        const lastNameInput = document.getElementById(`participant${i}LastName`);

        if (firstNameInput && firstNameInput.value && firstNameInput.value.trim()) {
            const section = document.getElementById(`participant-section-${i}`);
            if (section) {
                section.classList.remove('display-none');
                section.style.display = 'block';
                visibleParticipants.push(i);
                nextParticipantIndex = i + 1;
            }
        }
    }

    // Hide add button if at max
    if (nextParticipantIndex > 6) {
        if (addBtn) addBtn.style.display = 'none';
    }
});
