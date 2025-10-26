/**
 * Live Scoring JavaScript
 * Mobile-optimized single-team scoring with penalties
 */

// Global state
// Variables that need to be accessed by websocket-client.js must be on window object
window.currentTeamId = null;
window.teamScores = {};
window.teamPenalties = {};
window.calculateRankingsAndPoints = null; // Will be assigned to function below
window.updateRankingsOverview = null; // Will be assigned to function below
window.updatePenaltyTotals = null; // Will be assigned to function below
window.updateCurrentTeamDisplay = null; // Will be assigned to function below

// Local variables (not needed by websocket-client.js)
let globalTimer = null;
let globalStartTime = 0;
let globalElapsed = 0;
let wsClient = null;
let currentEditLock = null; // Track current lock: {teamId, field}
let autoSaveTimer = null; // Debounce timer for auto-save
let autoSaveBannerTimeout = null; // Timeout for hiding auto-save banner

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeScores();

    window.calculateRankingsAndPoints(); // Calculate rankings from existing scores
    window.updateRankingsOverview(); // Display the rankings
    attachEventListeners();
    initializeWebSocket();
    restoreSavedTeamSelection(); // Restore team selection if page was refreshed
});

// Initialize WebSocket client
function initializeWebSocket() {
    if (window.gameData && window.gameData.id) {
        // For round-based games, pass the current round ID to the WebSocket client
        const roundId = (window.gameData.hasRounds && window.gameData.currentRoundId)
            ? window.gameData.currentRoundId
            : null;

        wsClient = new GameSocketClient(window.gameData.id, roundId);
    }
}

// Attach event listeners using data attributes
function attachEventListeners() {
    // Team selector
    const teamSelector = document.querySelector('[data-action="switch-team"]');
    if (teamSelector) {
        teamSelector.addEventListener('change', switchTeam);
    }

    // Score input
    const scoreInput = document.querySelector('[data-action="score-change"]');
    if (scoreInput) {
        scoreInput.addEventListener('input', onScoreChange);

        // Request lock when user focuses on input (before editing)
        scoreInput.addEventListener('focus', function() {
            if (window.currentTeamId && wsClient) {
                // Only request lock if we don't already have it
                if (!currentEditLock || currentEditLock.teamId !== window.currentTeamId || currentEditLock.field !== 'score') {
                    wsClient.requestLock(window.currentTeamId, 'score');
                    currentEditLock = {teamId: window.currentTeamId, field: 'score'};
                }
            }
        });

        // Release lock and auto-save when input loses focus
        scoreInput.addEventListener('blur', function() {
            if (currentEditLock && wsClient) {
                // Get current score values - send BASE score, not final score
                // (final score will be recalculated by each client based on their penalty data)
                const baseScore = window.teamScores[window.currentTeamId]?.baseScore || 0;
                const points = window.teamScores[window.currentTeamId]?.points || 0;

                // Release the lock with current score (this will also save and broadcast)
                wsClient.releaseLock(currentEditLock.teamId, currentEditLock.field, baseScore, points);
                currentEditLock = null;
            }
        });
    }

    // Score increment/decrement buttons
    const incrementBtn = document.querySelector('[data-action="increment-score"]');
    if (incrementBtn) {
        incrementBtn.addEventListener('click', incrementScore);
    }

    const decrementBtn = document.querySelector('[data-action="decrement-score"]');
    if (decrementBtn) {
        decrementBtn.addEventListener('click', decrementScore);
    }

    // Stopwatch buttons
    const startBtn = document.querySelector('[data-action="start-stopwatch"]');
    if (startBtn) {
        startBtn.addEventListener('click', startStopwatch);
    }

    const stopBtn = document.querySelector('[data-action="stop-stopwatch"]');
    if (stopBtn) {
        stopBtn.addEventListener('click', stopStopwatch);
    }

    const resetBtn = document.querySelector('[data-action="reset-stopwatch"]');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetStopwatch);
    }

    // Penalty increment/decrement buttons (stackable)
    document.querySelectorAll('[data-action="increment-penalty"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const penaltyId = this.getAttribute('data-penalty-id');
            const penaltyValue = parseFloat(this.getAttribute('data-penalty-value'));
            const penaltyUnit = this.getAttribute('data-penalty-unit');
            incrementPenalty(penaltyId, penaltyValue, penaltyUnit);
        });
    });

    document.querySelectorAll('[data-action="decrement-penalty"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const penaltyId = this.getAttribute('data-penalty-id');
            decrementPenalty(penaltyId);
        });
    });

    // Penalty tags (one-time)
    document.querySelectorAll('[data-action="toggle-penalty-tag"]').forEach(tag => {
        tag.addEventListener('click', function() {
            const penaltyId = this.getAttribute('data-penalty-id');
            const penaltyValue = parseFloat(this.getAttribute('data-penalty-value'));
            const penaltyUnit = this.getAttribute('data-penalty-unit');
            togglePenaltyTag(penaltyId, penaltyValue, penaltyUnit);
        });
    });

    // Clear team button
    const clearBtn = document.querySelector('[data-action="clear-team"]');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearCurrentTeam);
    }

    // Toggle timer list button
    const toggleTimersBtn = document.querySelector('[data-action="toggle-timer-list"]');
    if (toggleTimersBtn) {
        toggleTimersBtn.addEventListener('click', toggleTimerList);
    }
}

// Initialize scores from existing data
function initializeScores() {
    if (typeof window.existingScores !== 'undefined') {
        Object.keys(window.existingScores).forEach(teamId => {
            const score = window.existingScores[teamId];
            window.teamScores[teamId] = {
                baseScore: parseFloat(score.score_value) || 0,
                penaltyTotal: 0,
                finalScore: parseFloat(score.score_value) || 0,
                rank: 0,
                points: parseInt(score.points) || 0
            };
        });
    }

    // Initialize all teams
    if (typeof window.teamsData !== 'undefined') {
        window.teamsData.forEach(team => {
            if (!window.teamScores[team.id]) {
                window.teamScores[team.id] = {
                    baseScore: 0,
                    penaltyTotal: 0,
                    finalScore: 0,
                    rank: 0,
                    points: 0
                };
            }
            window.teamPenalties[team.id] = {};
        });
    }

    // Try to load persisted penalties from sessionStorage
    loadPenaltiesFromSession();
}

// Switch to selected team
function switchTeam() {
    // Release any existing lock before switching
    if (currentEditLock && wsClient && window.currentTeamId) {
        const baseScore = window.teamScores[window.currentTeamId]?.baseScore || 0;
        const points = window.teamScores[window.currentTeamId]?.points || 0;
        wsClient.releaseLock(currentEditLock.teamId, currentEditLock.field, baseScore, points);
        currentEditLock = null;
    }

    const selector = document.getElementById('team-selector');
    const teamId = selector.value;
    const scoringCard = document.getElementById('team-scoring-card');

    if (!teamId) {
        scoringCard.classList.add('display-none');
        window.currentTeamId = null;
        clearSavedTeamSelection();
        return;
    }

    window.currentTeamId = teamId;
    const team = window.teamsData.find(t => t.id == teamId);

    // Save team selection to sessionStorage
    saveTeamSelection(teamId);

    // Show scoring card
    scoringCard.classList.remove('display-none');

    // Update team header
    document.getElementById('selected-team-name').textContent = team.name;
    document.getElementById('team-color').style.backgroundColor = team.color;

    // Load team's current score
    const teamScore = window.teamScores[teamId];
    document.getElementById('score-input').value = teamScore.baseScore || '';

    // Reset timer when changing teams
    resetStopwatch();

    // Update rank and points display
    window.updateCurrentTeamDisplay();

    // Load penalties for this team
    loadTeamPenalties(teamId);

    // Load existing timer records for this team
    loadExistingTimers(teamId);

    // Scroll to scoring card
    document.getElementById('team-scoring-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Update current team's rank and points display
window.updateCurrentTeamDisplay = function() {
    if (!window.currentTeamId) return;

    const teamScore = window.teamScores[window.currentTeamId];
    const rankBadge = document.getElementById('rank-badge');
    const rankDisplay = document.getElementById('rank-display');
    const pointsDisplay = document.getElementById('points-display');

    // Update rank with medal styling
    rankDisplay.textContent = teamScore.rank > 0 ? getOrdinalSuffix(teamScore.rank) : '-';

    // Add medal class
    rankBadge.className = 'rank-badge';
    if (teamScore.rank === 1) rankBadge.classList.add('rank-1');
    else if (teamScore.rank === 2) rankBadge.classList.add('rank-2');
    else if (teamScore.rank === 3) rankBadge.classList.add('rank-3');

    // Update points
    pointsDisplay.textContent = teamScore.points;
}

// Load penalties for current team
function loadTeamPenalties(teamId) {
    if (!window.teamPenalties[teamId]) window.teamPenalties[teamId] = {};

    const penalties = window.teamPenalties[teamId];

    // Reset all penalty displays
    if (window.penaltiesData) {
        window.penaltiesData.forEach(penalty => {
            const count = penalties[penalty.id] || 0;

            if (penalty.stackable) {
                // Update counter
                const counterElement = document.getElementById(`penalty-count-${penalty.id}`);
                if (counterElement) {
                    counterElement.value = count;
                }
            } else {
                // Update tag selection
                const tagElement = document.getElementById(`penalty-tag-${penalty.id}`);
                if (tagElement) {
                    if (count > 0) {
                        tagElement.classList.add('selected');
                        tagElement.querySelector('.penalty-tag-icon').textContent = '🔵';
                    } else {
                        tagElement.classList.remove('selected');
                        tagElement.querySelector('.penalty-tag-icon').textContent = '⚪';
                    }
                }
            }
        });
    }

    window.updatePenaltyTotals();
}

// Unified score input handlers
function incrementScore() {
    if (!window.currentTeamId) return;

    const input = document.getElementById('score-input');
    const currentValue = parseFloat(input.value) || 0;
    input.value = (currentValue + 1).toFixed(2);
    onScoreChange();
}

function decrementScore() {
    if (!window.currentTeamId) return;

    const input = document.getElementById('score-input');
    const currentValue = parseFloat(input.value) || 0;
    if (currentValue > 0) {
        input.value = (currentValue - 1).toFixed(2);
        onScoreChange();
    }
}

function onScoreChange() {
    if (!window.currentTeamId) return;

    const baseScore = parseFloat(document.getElementById('score-input').value) || 0;
    window.teamScores[window.currentTeamId].baseScore = baseScore;

    window.updatePenaltyTotals();
    window.calculateRankingsAndPoints();
    window.updateCurrentTeamDisplay();
    window.updateRankingsOverview();
    saveToHiddenInputs();

    // Auto-save via WebSocket (debounced to prevent flooding)
    // Send BASE score, not final score (final score will be recalculated by each client)
    if (wsClient && window.currentTeamId) {
        const baseScore = window.teamScores[window.currentTeamId]?.baseScore || 0;
        const points = window.teamScores[window.currentTeamId]?.points || 0;
        wsClient.updateScore(window.currentTeamId, baseScore, points);
    }
}

// Auto-save functionality for public users
function triggerAutoSave() {
    // Check if user is public (not authenticated)
    // We check for the presence of the auto-save-info element as an indicator
    const isPublicUser = document.querySelector('.auto-save-info') !== null;

    if (!isPublicUser) {
        return; // Admin users don't need auto-save
    }

    // Clear existing timer
    if (autoSaveTimer) {
        clearTimeout(autoSaveTimer);
    }

    // Set new timer (debounce: wait 2 seconds after last change)
    autoSaveTimer = setTimeout(() => {
        performAutoSave();
    }, 2000);
}

async function performAutoSave() {
    if (!window.currentTeamId) return;

    const gameId = window.gameData ? window.gameData.id : null;
    if (!gameId) return;

    const formData = new FormData();

    // Add CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]');
    if (csrfToken) {
        formData.append('csrf_token', csrfToken.value);
    }

    // Add all team scores (same as form submission)
    Object.keys(window.teamScores).forEach(teamId => {
        const scoreValue = document.getElementById(`score-${teamId}`);
        const pointsValue = document.getElementById(`points-input-${teamId}`);
        const penaltiesValue = document.getElementById(`penalties-${teamId}`);

        if (scoreValue) formData.append(`score-${teamId}`, scoreValue.value);
        if (pointsValue) formData.append(`points-input-${teamId}`, pointsValue.value);
        if (penaltiesValue) formData.append(`penalties-${teamId}`, penaltiesValue.value);
    });

    try {
        const response = await fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'  // Identify as AJAX request
            }
        });

        if (response.ok) {
            showAutoSaveBanner('Changes saved automatically');
        } else {
            showAutoSaveBanner('Error saving changes', true);
        }
    } catch (error) {
        console.error('Auto-save error:', error);
        showAutoSaveBanner('Error saving changes', true);
    }
}

function showAutoSaveBanner(message, isError = false) {
    const banner = document.getElementById('auto-save-banner');
    const messageSpan = document.getElementById('auto-save-message');

    if (!banner || !messageSpan) return;

    // Update message
    messageSpan.textContent = message;

    // Update styling for errors
    if (isError) {
        banner.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
    } else {
        banner.style.background = 'linear-gradient(135deg, #10b981, #059669)';
    }

    // Clear existing timeout
    if (autoSaveBannerTimeout) {
        clearTimeout(autoSaveBannerTimeout);
    }

    // Show banner
    banner.style.display = 'flex';
    banner.classList.remove('hiding');

    // Hide after 3 seconds
    autoSaveBannerTimeout = setTimeout(() => {
        banner.classList.add('hiding');
        setTimeout(() => {
            banner.style.display = 'none';
        }, 300); // Match CSS transition duration
    }, 3000);
}

// Penalty handlers - Stackable
function incrementPenalty(penaltyId, value, unit) {
    if (!window.currentTeamId) return;

    if (!window.teamPenalties[window.currentTeamId][penaltyId]) {
        window.teamPenalties[window.currentTeamId][penaltyId] = 0;
    }

    window.teamPenalties[window.currentTeamId][penaltyId]++;

    const counterElement = document.getElementById(`penalty-count-${penaltyId}`);
    if (counterElement) {
        counterElement.value = window.teamPenalties[window.currentTeamId][penaltyId];
    }

    window.updatePenaltyTotals();
    window.calculateRankingsAndPoints();
    window.updateCurrentTeamDisplay();
    window.updateRankingsOverview();
    saveToHiddenInputs();
    savePenaltiesToSession();

    // Auto-save via WebSocket - send BASE score, not final score
    if (wsClient && window.currentTeamId) {
        const baseScore = window.teamScores[window.currentTeamId]?.baseScore || 0;
        const points = window.teamScores[window.currentTeamId]?.points || 0;
        wsClient.updateScore(window.currentTeamId, baseScore, points);
    }

    triggerAutoSave();
}

function decrementPenalty(penaltyId) {
    if (!window.currentTeamId) return;

    if (!window.teamPenalties[window.currentTeamId][penaltyId] || window.teamPenalties[window.currentTeamId][penaltyId] === 0) {
        return;
    }

    window.teamPenalties[window.currentTeamId][penaltyId]--;

    const counterElement = document.getElementById(`penalty-count-${penaltyId}`);
    if (counterElement) {
        counterElement.value = window.teamPenalties[window.currentTeamId][penaltyId];
    }

    window.updatePenaltyTotals();
    window.calculateRankingsAndPoints();
    window.updateCurrentTeamDisplay();
    window.updateRankingsOverview();
    saveToHiddenInputs();
    savePenaltiesToSession();

    // Auto-save via WebSocket - send BASE score, not final score
    if (wsClient && window.currentTeamId) {
        const baseScore = window.teamScores[window.currentTeamId]?.baseScore || 0;
        const points = window.teamScores[window.currentTeamId]?.points || 0;
        wsClient.updateScore(window.currentTeamId, baseScore, points);
    }

    triggerAutoSave();
}

function onPenaltyCountChange(penaltyId) {
    if (!window.currentTeamId) return;

    const counterElement = document.getElementById(`penalty-count-${penaltyId}`);
    if (!counterElement) return;

    // Get and validate the input value
    let newCount = parseInt(counterElement.value) || 0;

    // Enforce min/max bounds
    if (newCount < 0) newCount = 0;
    if (newCount > 99) newCount = 99;

    // Update the input field with the validated value
    counterElement.value = newCount;

    // Update the internal state
    if (!window.teamPenalties[window.currentTeamId]) {
        window.teamPenalties[window.currentTeamId] = {};
    }
    window.teamPenalties[window.currentTeamId][penaltyId] = newCount;

    // Recalculate everything
    window.updatePenaltyTotals();
    window.calculateRankingsAndPoints();
    window.updateCurrentTeamDisplay();
    window.updateRankingsOverview();
    saveToHiddenInputs();
    savePenaltiesToSession();

    // Auto-save via WebSocket
    if (wsClient && window.currentTeamId) {
        const baseScore = window.teamScores[window.currentTeamId]?.baseScore || 0;
        const points = window.teamScores[window.currentTeamId]?.points || 0;
        wsClient.updateScore(window.currentTeamId, baseScore, points);
    }

    triggerAutoSave();
}

// Penalty handlers - One-time (toggle)
function togglePenaltyTag(penaltyId, value, unit) {
    if (!window.currentTeamId) return;

    const tagElement = document.getElementById(`penalty-tag-${penaltyId}`);

    if (!window.teamPenalties[window.currentTeamId][penaltyId]) {
        window.teamPenalties[window.currentTeamId][penaltyId] = 0;
    }

    // Toggle
    if (window.teamPenalties[window.currentTeamId][penaltyId] === 0) {
        window.teamPenalties[window.currentTeamId][penaltyId] = 1;
        tagElement.classList.add('selected');
        tagElement.querySelector('.penalty-tag-icon').textContent = '🔵';
    } else {
        window.teamPenalties[window.currentTeamId][penaltyId] = 0;
        tagElement.classList.remove('selected');
        tagElement.querySelector('.penalty-tag-icon').textContent = '⚪';
    }

    window.updatePenaltyTotals();
    window.calculateRankingsAndPoints();
    window.updateCurrentTeamDisplay();
    window.updateRankingsOverview();
    saveToHiddenInputs();
    savePenaltiesToSession();

    // Auto-save via WebSocket - send BASE score, not final score
    if (wsClient && window.currentTeamId) {
        const baseScore = window.teamScores[window.currentTeamId]?.baseScore || 0;
        const points = window.teamScores[window.currentTeamId]?.points || 0;
        wsClient.updateScore(window.currentTeamId, baseScore, points);
    }

    triggerAutoSave();
}

// Update penalty totals display
window.updatePenaltyTotals = function() {
    if (!window.currentTeamId) return;

    const baseScore = window.teamScores[window.currentTeamId].baseScore || 0;
    let penaltyTotal = 0;

    // Calculate total penalties
    if (window.penaltiesData && window.teamPenalties[window.currentTeamId]) {
        window.penaltiesData.forEach(penalty => {
            const count = window.teamPenalties[window.currentTeamId][penalty.id] || 0;
            penaltyTotal += count * penalty.value;
        });
    }

    const finalScore = baseScore + penaltyTotal;

    // Update displays (only if elements exist - they won't exist when there are no penalties)
    const baseScoreDisplay = document.getElementById('base-score-display');
    const penaltyTotalDisplay = document.getElementById('penalty-total-display');
    const finalScoreDisplay = document.getElementById('final-score-display');

    if (baseScoreDisplay) baseScoreDisplay.textContent = baseScore.toFixed(2);
    if (penaltyTotalDisplay) penaltyTotalDisplay.textContent = penaltyTotal.toFixed(2);
    if (finalScoreDisplay) finalScoreDisplay.textContent = finalScore.toFixed(2);

    // Update team score (CRITICAL: Always update this regardless of whether penalty elements exist)
    window.teamScores[window.currentTeamId].penaltyTotal = penaltyTotal;
    window.teamScores[window.currentTeamId].finalScore = finalScore;
};

// Calculate rankings and points for all teams
window.calculateRankingsAndPoints = function() {
    const teamsWithScores = [];

    Object.keys(window.teamScores).forEach(teamId => {
        const teamScore = window.teamScores[teamId];

        if (teamScore.finalScore > 0 || teamScore.baseScore > 0) {
            teamsWithScores.push({
                id: teamId,
                score: teamScore.finalScore
            });
        }
    });


    // Sort teams by score
    const scoringDirection = window.gameData.scoringDirection;
    if (scoringDirection === 'lower_better') {
        teamsWithScores.sort((a, b) => a.score - b.score);
    } else {
        teamsWithScores.sort((a, b) => b.score - a.score);
    }

    // Assign ranks and calculate points
    const pointScheme = window.gameData.pointScheme;
    const totalTeams = window.gameData.teamsCount;

    teamsWithScores.forEach((team, index) => {
        const rank = index + 1;
        const points = (totalTeams - rank + 1) * pointScheme;

        window.teamScores[team.id].rank = rank;
        window.teamScores[team.id].points = points;
    });

    // Reset ranks for teams without scores
    Object.keys(window.teamScores).forEach(teamId => {
        const hasScore = teamsWithScores.some(t => t.id == teamId);
        if (!hasScore) {
            window.teamScores[teamId].rank = 0;
            window.teamScores[teamId].points = 0;
        }
    });
};

// Update rankings overview display
window.updateRankingsOverview = function() {
    const rankingsList = document.getElementById('rankings-list');
    if (!rankingsList) {
        return;
    }

    // Get teams with scores
    const teamsWithScores = [];

    Object.keys(window.teamScores).forEach(teamId => {
        const team = window.teamsData.find(t => t.id == teamId);
        const teamScore = window.teamScores[teamId];

        if (team && teamScore.rank > 0) {
            teamsWithScores.push({
                id: teamId,
                name: team.name,
                color: team.color,
                rank: teamScore.rank,
                score: teamScore.finalScore,
                points: teamScore.points
            });
        }
    });


    // Sort by rank
    teamsWithScores.sort((a, b) => a.rank - b.rank);

    // Build HTML
    let html = '';
    if (teamsWithScores.length === 0) {
        html = '<p class="no-scores">No scores entered yet</p>';
    } else {
        teamsWithScores.forEach(team => {
            const medalClass = team.rank <= 3 ? `rank-${team.rank}` : '';
            html += `
                <div class="ranking-item ${medalClass}">
                    <div class="ranking-position">
                        <span class="ranking-number">${team.rank}</span>
                        ${team.rank === 1 ? '<span class="medal">🥇</span>' : ''}
                        ${team.rank === 2 ? '<span class="medal">🥈</span>' : ''}
                        ${team.rank === 3 ? '<span class="medal">🥉</span>' : ''}
                    </div>
                    <div class="ranking-team">
                        <div class="ranking-color" style="background-color: ${team.color}"></div>
                        <span class="ranking-name">${team.name}</span>
                    </div>
                    <div class="ranking-stats">
                        <span class="ranking-score">${team.score.toFixed(2)}</span>
                        <span class="ranking-points">${Math.floor(team.points)} pts</span>
                    </div>
                </div>
            `;
        });
    }

    rankingsList.innerHTML = html;
};

// Save to hidden inputs for form submission
function saveToHiddenInputs() {
    Object.keys(window.teamScores).forEach(teamId => {
        const scoreInput = document.getElementById(`score-${teamId}`);
        const pointsInput = document.getElementById(`points-input-${teamId}`);
        const penaltiesInput = document.getElementById(`penalties-${teamId}`);

        if (scoreInput) {
            scoreInput.value = window.teamScores[teamId].finalScore || '';
        }

        if (pointsInput) {
            pointsInput.value = window.teamScores[teamId].points || 0;
        }

        if (penaltiesInput && window.teamPenalties[teamId]) {
            penaltiesInput.value = JSON.stringify(window.teamPenalties[teamId]);
        }
    });
}

// Clear current team
function clearCurrentTeam() {
    if (!window.currentTeamId) return;

    if (window.showConfirmModal) {
        showConfirmModal({
            title: 'Clear Team Data',
            message: 'Are you sure you want to clear this team\'s score and penalties?',
            warning: 'This cannot be undone!',
            confirmText: 'Clear',
            cancelText: 'Cancel',
            onConfirm: function() {
                performClearTeam();
            }
        });
    } else {
        if (!confirm('Are you sure you want to clear this team\'s score and penalties?')) {
            return;
        }
        performClearTeam();
    }
}

function performClearTeam() {
    if (!window.currentTeamId) return;

    const teamId = window.currentTeamId;

    // Reset score
    document.getElementById('score-input').value = '';
    window.teamScores[teamId].baseScore = 0;
    window.teamScores[teamId].penaltyTotal = 0;
    window.teamScores[teamId].finalScore = 0;

    // Reset penalties
    window.teamPenalties[teamId] = {};

    // Reload display
    loadTeamPenalties(teamId);
    window.updatePenaltyTotals();
    window.calculateRankingsAndPoints();
    window.updateCurrentTeamDisplay();
    window.updateRankingsOverview();
    saveToHiddenInputs();

    // Broadcast score update via WebSocket to other clients
    if (window.gameSocketClient && window.gameSocketClient.connected) {
        window.gameSocketClient.updateScore(
            teamId,
            0,  // cleared score
            window.teamScores[teamId].points || 0
        );
    }
}

// Stopwatch functions (for time-based games)
function startStopwatch() {
    if (!window.currentTeamId) {
        if (window.showAlertModal) {
            showAlertModal({
                title: 'Team Required',
                message: 'Please select a team first before starting the stopwatch.',
                type: 'warning'
            });
        } else {
            alert('Please select a team first');
        }
        return;
    }

    globalStartTime = Date.now() - globalElapsed;

    if (globalTimer) {
        clearInterval(globalTimer);
    }

    globalTimer = setInterval(() => {
        globalElapsed = Date.now() - globalStartTime;
        document.getElementById('timer-display').textContent = formatTimeWithMillis(globalElapsed);
    }, 10); // Update every 10ms for smooth milliseconds

    // Notify others that timer started
    if (wsClient) {
        wsClient.startTimer(window.currentTeamId);
    }
}

function stopStopwatch() {
    if (globalTimer) {
        clearInterval(globalTimer);
        globalTimer = null;

        if (window.currentTeamId) {
            const seconds = (globalElapsed / 1000).toFixed(3);
            document.getElementById('score-input').value = seconds;

            // Broadcast timer stop via WebSocket
            if (wsClient) {
                wsClient.stopTimer(window.currentTeamId, parseFloat(seconds));
            }

            onScoreChange(); // This auto-saves the score to the hidden inputs

            // Show a brief success message
            const timerDisplay = document.getElementById('timer-display');
            const originalColor = timerDisplay.style.color;
            timerDisplay.style.color = '#22c55e'; // Green color
            setTimeout(() => {
                timerDisplay.style.color = originalColor;
            }, 1000);
        }
    }
}

function resetStopwatch() {
    if (globalTimer) {
        clearInterval(globalTimer);
        globalTimer = null;
    }
    globalElapsed = 0;
    const timerDisplay = document.getElementById('timer-display');
    if (timerDisplay) {
        timerDisplay.textContent = '00:00.000';
    }

    // Also hide multi-timer stats when resetting
    const statsPanel = document.getElementById('multi-timer-stats');
    if (statsPanel) {
        statsPanel.style.display = 'none';
    }
}

function formatTime(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function formatTimeWithMillis(milliseconds) {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    const millis = Math.floor((milliseconds % 1000));

    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(3, '0')}`;
}

// Helper function for ordinal suffixes
function getOrdinalSuffix(num) {
    const j = num % 10;
    const k = num % 100;
    if (j === 1 && k !== 11) return num + "st";
    if (j === 2 && k !== 12) return num + "nd";
    if (j === 3 && k !== 13) return num + "rd";
    return num + "th";
}

// Penalty persistence functions
function savePenaltiesToSession() {
    if (window.gameData && window.gameData.id) {
        const key = `penalties_game_${window.gameData.id}`;
        sessionStorage.setItem(key, JSON.stringify(window.teamPenalties));
    }
}

function loadPenaltiesFromSession() {
    if (window.gameData && window.gameData.id) {
        const key = `penalties_game_${window.gameData.id}`;
        const stored = sessionStorage.getItem(key);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                Object.assign(window.teamPenalties, parsed);
            } catch (e) {
                console.error('Failed to parse stored penalties:', e);
            }
        }
    }
}

// Team selection persistence functions
function saveTeamSelection(teamId) {
    if (window.gameData && window.gameData.id) {
        const key = `selectedTeam_game_${window.gameData.id}`;
        sessionStorage.setItem(key, teamId);
    }
}

function clearSavedTeamSelection() {
    if (window.gameData && window.gameData.id) {
        const key = `selectedTeam_game_${window.gameData.id}`;
        sessionStorage.removeItem(key);
    }
}

function restoreSavedTeamSelection() {
    if (window.gameData && window.gameData.id) {
        const key = `selectedTeam_game_${window.gameData.id}`;
        const savedTeamId = sessionStorage.getItem(key);

        if (savedTeamId) {
            const selector = document.getElementById('team-selector');
            if (selector) {
                // Check if the team still exists
                const teamExists = window.teamsData && window.teamsData.some(t => t.id == savedTeamId);
                if (teamExists) {
                    selector.value = savedTeamId;
                    // Trigger the change event to load the team
                    switchTeam();
                } else {
                    // Team doesn't exist anymore, clear saved selection
                    clearSavedTeamSelection();
                }
            }
        }
    }
}

// Load existing timer records for a team
async function loadExistingTimers(teamId) {
    if (!window.gameData || !teamId) return;

    const gameId = window.gameData.id;

    try {
        const response = await fetch(`/api/timers/${gameId}/${teamId}`);
        const result = await response.json();

        if (result.success && result.timers && result.timers.length > 0) {
            // Show the multi-timer stats section
            const multiTimerStats = document.getElementById('multi-timer-stats');
            if (multiTimerStats) {
                multiTimerStats.style.display = 'block';
            }

            // Update timer count
            const timerCount = document.getElementById('multi-timer-count');
            if (timerCount) {
                const count = result.timers.length;
                timerCount.textContent = `${count} timer${count !== 1 ? 's' : ''}`;
            }

            // Calculate and display average
            const times = result.timers.map(t => t.time_value);
            const average = times.reduce((sum, time) => sum + time, 0) / times.length;
            const avgDisplay = document.getElementById('multi-timer-average');
            if (avgDisplay) {
                avgDisplay.textContent = `Avg: ${average.toFixed(3)}s`;
            }

            // Populate timer list
            const timerList = document.getElementById('multi-timer-list');
            if (timerList) {
                timerList.innerHTML = '';

                result.timers.forEach((timer, index) => {
                    const timerItem = document.createElement('div');
                    timerItem.classList.add('timer-item');

                    const adminBadge = timer.is_admin
                        ? '<span class="timer-admin-badge" title="Admin timer">Admin</span>'
                        : '';

                    // Only show delete button for admin users
                    const deleteBtn = window.isAdminUser
                        ? `<button type="button" class="btn-delete-timer" onclick="deleteTimerRecord(${timer.id})" title="Delete this timer">
                             <i class="fas fa-trash"></i>
                           </button>`
                        : '';

                    timerItem.innerHTML = `
                        <div class="timer-item-info">
                            <span class="timer-item-number">#${index + 1}</span>
                            <span class="timer-item-value">${parseFloat(timer.time_value).toFixed(3)}s</span>
                        </div>
                        <div class="timer-item-actions">
                            ${adminBadge}
                            ${deleteBtn}
                        </div>
                    `;

                    timerList.appendChild(timerItem);
                });
            }
        }
    } catch (error) {
        console.error('Error loading existing timers:', error);
    }
}

// Toggle timer list visibility
function toggleTimerList() {
    const timerList = document.getElementById('multi-timer-list');
    const toggleBtn = document.getElementById('toggle-timers-btn');

    if (!timerList || !toggleBtn) return;

    const isHidden = timerList.style.display === 'none' || !timerList.style.display;

    if (isHidden) {
        timerList.style.display = 'flex';
        toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i><span>Hide Times</span>';
    } else {
        timerList.style.display = 'none';
        toggleBtn.innerHTML = '<i class="fas fa-eye"></i><span>Show Times</span>';
    }
}

// Delete a timer record
async function deleteTimerRecord(timerId) {
    if (window.showConfirmModal) {
        showConfirmModal({
            title: 'Delete Timer Record',
            message: 'Are you sure you want to delete this timer record?',
            warning: 'This cannot be undone!',
            confirmText: 'Delete',
            cancelText: 'Cancel',
            onConfirm: function() {
                performDeleteTimer(timerId);
            }
        });
    } else {
        if (!confirm('Are you sure you want to delete this timer record?')) {
            return;
        }
        performDeleteTimer(timerId);
    }
}

async function performDeleteTimer(timerId) {
    try {
        const response = await fetch(`/admin/timer/${timerId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            // Emit WebSocket event to refresh timer display for all users
            if (wsClient && wsClient.socket) {
                // The backend will have already recalculated and we need to fetch updated data
                // For now, just remove the timer item from the UI and let the next timer update refresh
                const timerItem = document.querySelector(`[data-timer-id="${timerId}"]`);
                if (timerItem) {
                    timerItem.remove();
                }

                // If no more timers, hide the stats panel
                const timerList = document.getElementById('multi-timer-list');
                if (timerList && timerList.children.length === 0) {
                    const statsPanel = document.getElementById('multi-timer-stats');
                    if (statsPanel) {
                        statsPanel.style.display = 'none';
                    }
                }
            }
        } else {
            if (window.showAlertModal) {
                showAlertModal({
                    title: 'Delete Failed',
                    message: 'Failed to delete timer record: ' + (result.error || 'Unknown error'),
                    type: 'error'
                });
            } else {
                alert('Failed to delete timer record: ' + (result.error || 'Unknown error'));
            }
        }
    } catch (error) {
        console.error('[Timer] Error deleting timer record:', error);
        if (window.showAlertModal) {
            showAlertModal({
                title: 'Error',
                message: 'An error occurred while deleting the timer record',
                type: 'error'
            });
        } else {
            alert('An error occurred while deleting the timer record');
        }
    }
}

// Make functions available globally
window.toggleTimerList = toggleTimerList;
window.deleteTimerRecord = deleteTimerRecord;
