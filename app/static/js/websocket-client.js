/**
 * WebSocket Client for Real-Time Collaborative Scoring
 * Handles live updates, edit locks, and multi-timer coordination
 */

class GameSocketClient {
    constructor(gameId, roundId = null) {
        this.gameId = gameId;
        this.roundId = roundId; // Optional round ID for round-based games
        this.socket = null;
        this.connected = false;
        this.activeLocks = new Map(); // teamId_field -> boolean
        this.updateDebounceTimers = new Map();
        this.init();
    }

    init() {
        // Initialize Socket.IO connection
        this.socket = io({
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5
        });

        // Connection event handlers
        this.socket.on('connect', () => {
            this.connected = true;
            this.updateConnectionStatus(true);
            this.joinGame();
        });

        this.socket.on('disconnect', () => {
            this.connected = false;
            this.updateConnectionStatus(false);
            this.clearAllLockIndicators();
        });

        this.socket.on('connect_error', (error) => {
            console.error('[WS] Connection error:', error);
            this.updateConnectionStatus(false);
        });

        // Game event handlers
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // Field lock events
        this.socket.on('lock_acquired', (data) => {
            // We got the lock, ensure input is enabled for us
            const input = document.querySelector('#score-input');
            if (input && String(currentTeamId) === String(data.team_id)) {
                input.disabled = false;
                input.classList.remove('locked');
            }
        });

        this.socket.on('field_locked', (data) => {
            this.showLockIndicator(data.team_id, data.field, data.display_name);
        });

        this.socket.on('field_unlocked', (data) => {
            this.hideLockIndicator(data.team_id, data.field);

            // Update score and rankings with the final value
            if (data.score !== undefined && data.points !== undefined) {
                this.updateScoreDisplay(data.team_id, data.score, data.points);
            }
        });

        this.socket.on('lock_denied', (data) => {
            // Field is locked by someone else, show indicator
            this.showLockIndicator(data.team_id, data.field, data.locked_by);
        });

        // Score update events
        this.socket.on('score_updated', (data) => {
            this.updateScoreDisplay(data.team_id, data.score, data.points);
        });

        // Timer events
        this.socket.on('timer_started', (data) => {
            // Could show indicator that someone is timing this team
        });

        this.socket.on('timer_stopped', (data) => {
            this.updateTimerDisplay(
                data.team_id,
                data.time,
                data.average,
                data.all_times,
                data.timer_count,
                data.timers  // Pass full timer details
            );
        });

        this.socket.on('timers_cleared', (data) => {
            this.clearTimerDisplay(data.team_id);
        });

        // Game state events
        this.socket.on('game_state', (data) => {
            // Update UI with current state
            if (data.scores) {
                Object.entries(data.scores).forEach(([teamId, scoreData]) => {
                    // Server sends 'score_value', not 'score'
                    this.updateScoreDisplay(teamId, scoreData.score_value, scoreData.points);
                });
            }
            if (data.locks) {
                data.locks.forEach(lock => {
                    this.showLockIndicator(lock.team_id, lock.field);
                });
            }
        });

        // Error handling
        this.socket.on('error', (data) => {
            console.error('[WS] Error:', data);
        });
    }

    joinGame() {
        if (!this.connected || !this.gameId) return;

        const payload = {
            game_id: this.gameId
        };

        // Include round_id if this is a round-based game
        if (this.roundId !== null && this.roundId !== undefined) {
            payload.round_id = this.roundId;
        }

        this.socket.emit('join_game', payload);
    }

    requestLock(teamId, field) {
        if (!this.connected) return false;

        this.socket.emit('request_edit_lock', {
            game_id: this.gameId,
            team_id: teamId,
            field: field
        });

        return true;
    }

    releaseLock(teamId, field, score, points) {
        if (!this.connected) return;

        this.socket.emit('release_edit_lock', {
            game_id: this.gameId,
            team_id: teamId,
            field: field,
            score: score,
            points: points
        });
    }

    updateScore(teamId, score, points) {
        if (!this.connected) return;

        // Debounce updates to avoid flooding the server
        const key = `${teamId}_score`;
        if (this.updateDebounceTimers.has(key)) {
            clearTimeout(this.updateDebounceTimers.get(key));
        }

        this.updateDebounceTimers.set(key, setTimeout(() => {
            const payload = {
                game_id: this.gameId,
                team_id: teamId,
                score: score,
                points: points
            };

            // Include round_id if this is a round-based game
            if (this.roundId !== null && this.roundId !== undefined) {
                payload.round_id = this.roundId;
            }

            this.socket.emit('update_score', payload);
            this.updateDebounceTimers.delete(key);
        }, 300)); // 300ms debounce
    }

    startTimer(teamId) {
        if (!this.connected) return;

        this.socket.emit('start_timer', {
            game_id: this.gameId,
            team_id: teamId
        });
    }

    stopTimer(teamId, time) {
        if (!this.connected) return;

        this.socket.emit('stop_timer', {
            game_id: this.gameId,
            team_id: teamId,
            time_value: time  // Changed from 'time' to 'time_value' to match server expectation
        });
    }

    clearTimers(teamId) {
        if (!this.connected) return;

        this.socket.emit('clear_timers', {
            game_id: this.gameId,
            team_id: teamId
        });
    }

    // UI update methods
    updateConnectionStatus(connected) {
        const indicator = document.querySelector('.ws-status-indicator');
        if (indicator) {
            indicator.classList.toggle('connected', connected);
            indicator.classList.toggle('disconnected', !connected);
            indicator.title = connected ? 'Live updates active' : 'Reconnecting...';
        }
    }

    showLockIndicator(teamId, field, displayName) {
        const lockKey = `${teamId}_${field}`;
        this.activeLocks.set(lockKey, true);

        // Find the input field - use strict string comparison for team IDs
        const input = document.querySelector(`#score-input[data-team-id="${teamId}"]`) ||
                     (String(currentTeamId) === String(teamId) ? document.querySelector('#score-input') : null);

        if (!input) return;

        // Add lock indicator
        let lockIndicator = input.parentElement.querySelector('.lock-indicator');
        if (!lockIndicator) {
            lockIndicator = document.createElement('div');
            lockIndicator.className = 'lock-indicator';
            input.parentElement.appendChild(lockIndicator);
        }

        // Update lock indicator text with user name
        const userName = displayName || 'Someone';
        lockIndicator.innerHTML = `<i class="fas fa-lock"></i> <span>${userName} is editing</span>`;
        lockIndicator.style.display = 'flex';

        // Disable input if we don't have the lock
        input.disabled = true;
        input.classList.add('locked');
    }

    hideLockIndicator(teamId, field) {
        const lockKey = `${teamId}_${field}`;
        this.activeLocks.delete(lockKey);

        // Find the input field - use strict string comparison for team IDs
        const input = document.querySelector(`#score-input[data-team-id="${teamId}"]`) ||
                     (String(currentTeamId) === String(teamId) ? document.querySelector('#score-input') : null);

        if (!input) return;

        // Remove lock indicator
        const lockIndicator = input.parentElement.querySelector('.lock-indicator');
        if (lockIndicator) {
            lockIndicator.style.display = 'none';
        }

        // Re-enable input
        input.disabled = false;
        input.classList.remove('locked');
    }

    clearAllLockIndicators() {
        this.activeLocks.clear();
        document.querySelectorAll('.lock-indicator').forEach(indicator => {
            indicator.style.display = 'none';
        });
        document.querySelectorAll('input.locked').forEach(input => {
            input.disabled = false;
            input.classList.remove('locked');
        });
    }

    updateScoreDisplay(teamId, score, points) {
        // Validate score before processing
        if (score === undefined || score === null || isNaN(parseFloat(score))) {
            console.warn('[WS] Invalid score received for team', teamId, '- skipping update. Score:', score);
            return;
        }

        // Update the team scores in memory
        if (window.teamScores && window.teamScores[teamId]) {
            // Score parameter now represents BASE score (not final score)
            // Update base score and points in memory
            window.teamScores[teamId].baseScore = parseFloat(score);
            window.teamScores[teamId].points = parseInt(points);

            // Recalculate penalty total and final score for this team
            let penaltyTotal = 0;
            if (window.penaltiesData && window.teamPenalties && window.teamPenalties[teamId]) {
                window.penaltiesData.forEach(penalty => {
                    const count = window.teamPenalties[teamId][penalty.id] || 0;
                    penaltyTotal += count * penalty.value;
                });
            }
            window.teamScores[teamId].penaltyTotal = penaltyTotal;
            window.teamScores[teamId].finalScore = window.teamScores[teamId].baseScore + penaltyTotal;

            // If this is the current team being viewed, update the input field
            // (but only if we don't have the lock - to avoid overwriting while actively editing)
            // Use strict string comparison to avoid type mismatch issues
            if (String(window.currentTeamId) === String(teamId)) {
                const lockKey = `${teamId}_score`;
                const hasLock = this.activeLocks.has(lockKey);

                // Debug logging to help diagnose issues

                // Only update input if we DON'T have the lock (someone else made the change)
                if (!hasLock) {
                    const input = document.querySelector('#score-input');
                    if (input) {
                        // Update base score input
                        input.value = score;

                        // Recalculate penalty totals and final score
                        if (typeof window.updatePenaltyTotals === 'function') {
                            window.updatePenaltyTotals();
                        }
                        if (typeof window.updateCurrentTeamDisplay === 'function') {
                            window.updateCurrentTeamDisplay();
                        }
                    } else {
                        console.warn('[WS] Could not find score input element');
                    }
                } else {
                }
            }

            // Always recalculate and update rankings for all teams
            if (window.calculateRankingsAndPoints) {
                window.calculateRankingsAndPoints();
            }

            // Always update rankings display
            if (window.updateRankingsOverview) {
                window.updateRankingsOverview();
            }
        }
    }

    updateTimerDisplay(teamId, time, average, allTimes, timerCount, timers) {
        // Only update if this is the currently selected team
        if (!window.currentTeamId || String(window.currentTeamId) !== String(teamId)) return;

        const statsPanel = document.getElementById('multi-timer-stats');
        const countDisplay = document.getElementById('multi-timer-count');
        const averageDisplay = document.getElementById('multi-timer-average');
        const timerList = document.getElementById('multi-timer-list');

        if (!statsPanel || !countDisplay || !averageDisplay || !timerList) return;

        // Show the stats panel if we have multiple timers or any timer data
        if (timerCount > 0) {
            statsPanel.style.display = 'block';

            // Update count
            const countText = timerCount === 1 ? '1 timer' : `${timerCount} timers`;
            countDisplay.textContent = countText;

            // Update average
            averageDisplay.textContent = `Avg: ${parseFloat(average).toFixed(3)}s`;

            // Update list of individual times with full details
            if (timers && timers.length > 0) {
                timerList.innerHTML = '';
                timers.forEach((timer, index) => {
                    const timerItem = document.createElement('div');
                    timerItem.className = 'multi-timer-item';
                    timerItem.dataset.timerId = timer.id;

                    const adminBadge = timer.is_admin
                        ? '<span class="timer-item-admin-badge"><i class="fas fa-shield-alt"></i> Admin</span>'
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
            } else if (allTimes && allTimes.length > 0) {
                // Fallback for old format (just times without full details)
                timerList.innerHTML = '';
                allTimes.forEach((timeValue, index) => {
                    const timerItem = document.createElement('div');
                    timerItem.className = 'multi-timer-item';
                    timerItem.innerHTML = `
                        <div class="timer-item-info">
                            <span class="timer-item-number">#${index + 1}</span>
                            <span class="timer-item-value">${parseFloat(timeValue).toFixed(3)}s</span>
                        </div>
                    `;
                    timerList.appendChild(timerItem);
                });
            }
        } else {
            statsPanel.style.display = 'none';
        }
    }

    clearTimerDisplay(teamId) {
        // Only clear if this is the currently selected team
        if (!window.currentTeamId || String(window.currentTeamId) !== String(teamId)) return;

        const statsPanel = document.getElementById('multi-timer-stats');
        const countDisplay = document.getElementById('multi-timer-count');
        const averageDisplay = document.getElementById('multi-timer-average');
        const timerList = document.getElementById('multi-timer-list');

        if (statsPanel) {
            statsPanel.style.display = 'none';
        }

        if (countDisplay) {
            countDisplay.textContent = '0 timers';
        }

        if (averageDisplay) {
            averageDisplay.textContent = '';
        }

        if (timerList) {
            timerList.innerHTML = '';
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Export for use in other scripts
window.GameSocketClient = GameSocketClient;
