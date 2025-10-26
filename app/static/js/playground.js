/**
 * Simulation Playground - Dynamic Game Night Scenario Simulator
 *
 * This module provides a comprehensive simulation tool for Game Night scenarios,
 * dynamically adapting to any number of teams and games. Features include:
 * - Real-time win possibility analysis
 * - Automated path-to-victory calculations
 * - Responsive mobile-first design
 * - Plain-language explanations
 */

// ============================================================================
// UI UTILITY FUNCTIONS
// ============================================================================

/**
 * Show a success banner notification
 * @param {string} title - Banner title
 * @param {string} message - Banner message
 */
function showSuccessBanner(title, message) {
    // Remove any existing banner
    const existingBanner = document.querySelector('.banner-toast');
    if (existingBanner) {
        existingBanner.remove();
    }

    // Create new banner
    const banner = document.createElement('div');
    banner.className = 'banner banner-success banner-toast banner-dismissible';
    banner.innerHTML = `
        <i class="fas fa-check-circle banner-icon"></i>
        <div class="banner-content">
            <div class="banner-title">${title}</div>
            <div class="banner-message">${message}</div>
        </div>
        <button class="banner-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    document.body.appendChild(banner);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (banner.parentElement) {
            banner.style.opacity = '0';
            banner.style.transform = 'translateY(20px)';
            setTimeout(() => banner.remove(), 300);
        }
    }, 5000);
}

/**
 * Show an info banner notification
 * @param {string} title - Banner title
 * @param {string} message - Banner message
 */
function showInfoBanner(title, message) {
    const existingBanner = document.querySelector('.banner-toast');
    if (existingBanner) {
        existingBanner.remove();
    }

    const banner = document.createElement('div');
    banner.className = 'banner banner-info banner-toast banner-dismissible';
    banner.innerHTML = `
        <i class="fas fa-info-circle banner-icon"></i>
        <div class="banner-content">
            <div class="banner-title">${title}</div>
            <div class="banner-message">${message}</div>
        </div>
        <button class="banner-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    document.body.appendChild(banner);

    setTimeout(() => {
        if (banner.parentElement) {
            banner.style.opacity = '0';
            banner.style.transform = 'translateY(20px)';
            setTimeout(() => banner.remove(), 300);
        }
    }, 5000);
}

// ============================================================================
// CORE CALCULATION UTILITIES
// ============================================================================

/**
 * Calculate base points for a placement (dynamic, not hardcoded)
 * Formula: teamCount + 1 - place
 * Example: 7 teams, 1st place = 7+1-1 = 7 pts, 7th place = 7+1-7 = 1 pt
 */
function basePoints(place, teamCount) {
    if (place < 1 || place > teamCount) return 0;
    return teamCount + 1 - place;
}

/**
 * Calculate game score with multiplier
 */
function calculateGameScore(place, multiplier, teamCount) {
    return basePoints(place, teamCount) * multiplier;
}

/**
 * Simulate final results given placement assignments
 * @param {Array} teams - Array of team objects with {id, name, color, totalPoints}
 * @param {Array} games - Array of game objects with {id, name, point_scheme}
 * @param {Object} placements - Map of gameId -> teamId -> placement
 * @returns {Array} Teams with simulated final points
 */
function simulateResults(teams, games, placements) {
    const teamCount = teams.length;

    return teams.map(team => {
        let finalPoints = team.totalPoints || 0;

        // Add points from each game
        games.forEach(game => {
            const placement = placements[game.id]?.[team.id] || teamCount; // Default to last place
            const points = calculateGameScore(placement, game.point_scheme, teamCount);
            finalPoints += points;
        });

        return {
            ...team,
            finalPoints,
            pointsGained: finalPoints - (team.totalPoints || 0)
        };
    }).sort((a, b) => b.finalPoints - a.finalPoints); // Sort by final points descending
}

/**
 * Compute min/max possible points for all teams
 * Used to determine if a team can mathematically still win
 */
function computeMaxMinPoints(teams, games) {
    const teamCount = teams.length;
    const results = {};

    teams.forEach(team => {
        let maxPoints = team.totalPoints || 0;
        let minPoints = team.totalPoints || 0;

        games.forEach(game => {
            // Max: win all games (1st place)
            maxPoints += calculateGameScore(1, game.point_scheme, teamCount);
            // Min: lose all games (last place)
            minPoints += calculateGameScore(teamCount, game.point_scheme, teamCount);
        });

        results[team.id] = { min: minPoints, max: maxPoints };
    });

    return results;
}

/**
 * Evaluate if a team can still win
 * Returns: 'guaranteed', 'possible', or 'none'
 */
function evaluateWinPossibility(teams, games, selectedTeamId) {
    const teamCount = teams.length;
    const maxMinPoints = computeMaxMinPoints(teams, games);
    const selectedTeam = teams.find(t => t.id === selectedTeamId);

    if (!selectedTeam) return { status: 'none', explanation: 'Team not found' };

    const userMax = maxMinPoints[selectedTeamId].max;
    const userMin = maxMinPoints[selectedTeamId].min;

    // Check against all rivals
    const rivals = teams.filter(t => t.id !== selectedTeamId);
    const rivalMaxes = rivals.map(r => maxMinPoints[r.id].max);
    const rivalMins = rivals.map(r => maxMinPoints[r.id].min);

    const highestRivalMin = Math.max(...rivalMins);
    const highestRivalMax = Math.max(...rivalMaxes);

    // No mathematical path to win
    if (userMax < highestRivalMin) {
        const blocker = rivals.find(r => maxMinPoints[r.id].min === highestRivalMin);
        return {
            status: 'none',
            explanation: `Even if you win every remaining game (+${userMax - (selectedTeam.totalPoints || 0)} → ${userMax} pts), ${blocker.name}'s lowest possible outcome gives them ${highestRivalMin} pts. No path to first place.`,
            blocker: blocker.name,
            userMax,
            blockerMin: highestRivalMin
        };
    }

    // Guaranteed win
    if (userMin > highestRivalMax) {
        return {
            status: 'guaranteed',
            explanation: `You're guaranteed to win! Even if you finish last in every game (${userMin} pts), the best any rival can do is ${highestRivalMax} pts.`,
            userMin,
            rivalMax: highestRivalMax
        };
    }

    // Still possible - depends on placements
    const pointsNeeded = highestRivalMax - (selectedTeam.totalPoints || 0) + 1;
    return {
        status: 'possible',
        explanation: `Need at least ${pointsNeeded} more points to secure 1st place.`,
        pointsNeeded,
        userMax,
        rivalMax: highestRivalMax
    };
}

/**
 * Find most conservative winning scenario for selected team
 * Finds ANY valid scenario where user can win, prioritizing balanced placements (2nd+3rd over 1st+4th)
 * FIXED: Now correctly tracks accumulated points across games within each scenario
 */
function findMinimalWinningScenario(teams, games, selectedTeamId) {
    const teamCount = teams.length;
    const gameCount = games.length;

    // Brute force is feasible for up to 10 games (as requested)
    if (gameCount > 10) {
        return null; // Too many combinations
    }

    const selectedTeam = teams.find(t => t.id === selectedTeamId);
    if (!selectedTeam) return null;

    const rivals = teams.filter(t => t.id !== selectedTeamId);

    // Generate all possible placement combinations for selected team
    function* generateCombinations(depth = 0, current = []) {
        if (depth === gameCount) {
            yield current;
            return;
        }
        for (let place = 1; place <= teamCount; place++) {
            yield* generateCombinations(depth + 1, [...current, place]);
        }
    }

    /**
     * Try to build a winning scenario with given user placements
     * Returns the complete scenario if user wins, null otherwise
     * FIXED: Tracks accumulated points across games for optimal rival assignments
     */
    function tryBuildWinningScenario(userPlacements) {
        // Calculate user's total with these placements
        let userTotal = selectedTeam.totalPoints || 0;
        userPlacements.forEach((place, gameIdx) => {
            userTotal += calculateGameScore(place, games[gameIdx].point_scheme, teamCount);
        });

        // Track accumulated points for each rival in this scenario
        const rivalScores = {};
        rivals.forEach(rival => {
            rivalScores[rival.id] = rival.totalPoints || 0;
        });

        const completeScenario = {};

        // For each game, assign rivals to remaining placements
        // Strategy: assign strongest rival (by accumulated score) to worst placement
        for (let gameIdx = 0; gameIdx < gameCount; gameIdx++) {
            const game = games[gameIdx];
            const userPlace = userPlacements[gameIdx];

            // Get available placements (excluding user's placement)
            const availablePlaces = [];
            for (let p = 1; p <= teamCount; p++) {
                if (p !== userPlace) availablePlaces.push(p);
            }

            // Sort rivals by their ACCUMULATED score in this scenario (descending)
            // FIXED: This was the bug - it was sorting by initial totalPoints instead
            const sortedRivals = [...rivals].sort((a, b) =>
                rivalScores[b.id] - rivalScores[a.id]
            );

            // Assign strongest to worst placement to minimize rival scores
            completeScenario[game.id] = {};
            sortedRivals.forEach((rival, idx) => {
                // availablePlaces is sorted ascending (1st, 2nd, 3rd, ...)
                // We want worst places first, so access from the end
                const placeIdx = availablePlaces.length - 1 - idx;
                const assignedPlace = availablePlaces[placeIdx];
                completeScenario[game.id][rival.id] = assignedPlace;

                // Update rival's accumulated score for next game
                const points = calculateGameScore(assignedPlace, game.point_scheme, teamCount);
                rivalScores[rival.id] += points;
            });
        }

        // Check if user wins (has strictly higher score than all rivals)
        let maxRivalScore = -Infinity;
        let topRival = null;

        for (const rival of rivals) {
            if (rivalScores[rival.id] >= userTotal) {
                // User doesn't win in this scenario
                return null;
            }
            if (rivalScores[rival.id] > maxRivalScore) {
                maxRivalScore = rivalScores[rival.id];
                topRival = rival;
            }
        }

        // User wins!
        return {
            userPlacements,
            userTotal,
            completeScenario,
            topRival,
            maxRivalScore
        };
    }

    let bestScenario = null;
    let bestScore = -Infinity; // Score for prioritization

    // Try each user placement combination
    for (const userPlacements of generateCombinations()) {
        const scenario = tryBuildWinningScenario(userPlacements);

        if (scenario) {
            // Calculate priority score (prefer balanced, middle placements)
            const avgPlacement = userPlacements.reduce((sum, p) => sum + p, 0) / userPlacements.length;
            const variance = userPlacements.reduce((sum, p) => sum + Math.pow(p - avgPlacement, 2), 0) / userPlacements.length;

            // Bonus for placements near 2nd or 3rd (prioritize 2 and 3 over 1 and 4)
            const middleBonus = userPlacements.reduce((bonus, p) => {
                const distanceFrom2_5 = Math.abs(p - 2.5);
                return bonus + (distanceFrom2_5 < 1.5 ? 50 : 0); // Bonus for 2nd or 3rd
            }, 0);

            // Lower avg placement is better, lower variance is better
            const priorityScore = (1000 - avgPlacement * 100) - variance * 10 + middleBonus;

            if (priorityScore > bestScore) {
                bestScore = priorityScore;
                bestScenario = {
                    placements: userPlacements.map((place, idx) => ({
                        game: games[idx],
                        place,
                        points: calculateGameScore(place, games[idx].point_scheme, teamCount)
                    })),
                    totalPoints: scenario.userTotal,
                    worstCaseRival: scenario.topRival,
                    worstCaseRivalMax: scenario.maxRivalScore,
                    completeScenario: scenario.completeScenario
                };
            }
        }
    }

    return bestScenario;
}

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

class PlaygroundState {
    constructor(teams, games) {
        this.teams = teams;
        this.games = games;
        this.selectedTeamId = teams[0]?.id || null;
        this.placements = {}; // gameId -> teamId -> placement
        this.listeners = [];

        // Initialize default placements (current standings order)
        this.resetPlacements();
    }

    resetPlacements() {
        this.games.forEach(game => {
            this.placements[game.id] = {};
            this.teams.forEach((team, idx) => {
                this.placements[game.id][team.id] = idx + 1; // Default to current rank order
            });
        });
        this.notifyListeners();
    }

    randomizePlacements(gameId) {
        const teamIds = this.teams.map(t => t.id);
        const shuffled = [...teamIds].sort(() => Math.random() - 0.5);

        this.placements[gameId] = {};
        shuffled.forEach((teamId, idx) => {
            this.placements[gameId][teamId] = idx + 1;
        });
        this.notifyListeners();
    }

    setPlacement(gameId, teamId, placement) {
        if (!this.placements[gameId]) {
            this.placements[gameId] = {};
        }

        // Find if another team already has this placement
        const currentOccupant = Object.keys(this.placements[gameId]).find(
            tid => parseInt(tid) !== teamId && this.placements[gameId][tid] === placement
        );

        // If someone else has this placement, swap them
        if (currentOccupant) {
            const oldPlacement = this.placements[gameId][teamId];
            this.placements[gameId][currentOccupant] = oldPlacement;
        }

        this.placements[gameId][teamId] = placement;
        this.notifyListeners();
    }

    setSelectedTeam(teamId) {
        this.selectedTeamId = teamId;
        this.notifyListeners();
    }

    getSimulatedResults() {
        return simulateResults(this.teams, this.games, this.placements);
    }

    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    notifyListeners() {
        this.listeners.forEach(listener => listener());
    }
}

// ============================================================================
// UI COMPONENTS
// ============================================================================

/**
 * Team Selector Component
 * Allows user to select their team for personalized analysis
 */
class TeamSelector {
    constructor(container, state) {
        this.container = container;
        this.state = state;
        this.render();
        this.state.subscribe(() => this.render());
    }

    render() {
        const selectedTeam = this.state.teams.find(t => t.id === this.state.selectedTeamId);

        this.container.innerHTML = `
            <div class="team-selector">
                <select class="team-selector-dropdown" id="teamSelect">
                    ${this.state.teams.map(team => `
                        <option value="${team.id}" ${team.id === this.state.selectedTeamId ? 'selected' : ''}>
                            ${team.name}
                        </option>
                    `).join('')}
                </select>
            </div>
        `;

        // Add event listener
        const select = this.container.querySelector('#teamSelect');
        select.addEventListener('change', (e) => {
            this.state.setSelectedTeam(parseInt(e.target.value));
        });
    }
}

/**
 * Win Possibility Banner Component
 * Shows at-a-glance whether the selected team can still win
 */
class WinPossibilityBanner {
    constructor(container, state) {
        this.container = container;
        this.state = state;
        this.render();
        this.state.subscribe(() => this.render());
    }

    render() {
        const analysis = evaluateWinPossibility(
            this.state.teams,
            this.state.games,
            this.state.selectedTeamId
        );

        let statusClass = '';
        let statusIcon = '';
        let statusText = '';

        switch (analysis.status) {
            case 'guaranteed':
                statusClass = 'win-possible-guaranteed';
                statusIcon = '🟢';
                statusText = 'Victory guaranteed!';
                break;
            case 'possible':
                statusClass = 'win-possible-maybe';
                statusIcon = '🟡';
                statusText = '';
                break;
            case 'none':
                statusClass = 'win-possible-none';
                statusIcon = '🔴';
                statusText = 'No mathematical path to first.';
                break;
        }

        // Only show banner for 'guaranteed' and 'none' cases, hide for 'possible'
        if (analysis.status === 'possible') {
            this.container.innerHTML = '';
            return;
        }

        this.container.innerHTML = `
            <div class="win-possibility-banner ${statusClass}">
                <div class="win-status-icon">${statusIcon}</div>
                <div class="win-status-content">
                    <div class="win-status-text">${statusText}</div>
                    <div class="win-status-explanation">${analysis.explanation}</div>
                </div>
            </div>
        `;
    }
}

/**
 * Standings Display Component
 * Shows current or simulated standings with highlighting
 */
class StandingsDisplay {
    constructor(container, state, mode = 'current') {
        this.container = container;
        this.state = state;
        this.mode = mode; // 'current' or 'simulated'
        this.render();
        this.state.subscribe(() => this.render());
    }

    render() {
        let teams = [];

        if (this.mode === 'current') {
            teams = [...this.state.teams].sort((a, b) =>
                (b.totalPoints || 0) - (a.totalPoints || 0)
            );
        } else {
            teams = this.state.getSimulatedResults();
        }

        this.container.innerHTML = teams.map((team, idx) => {
            const isSelected = team.id === this.state.selectedTeamId;
            const currentPoints = team.totalPoints || 0;
            const finalPoints = team.finalPoints || currentPoints;
            const pointsGained = team.pointsGained || 0;

            // Calculate max possible for current standings
            let maxPossibleText = '';
            if (this.mode === 'current' && this.state.games.length > 0) {
                const maxMinPoints = computeMaxMinPoints(this.state.teams, this.state.games);
                const maxPossible = maxMinPoints[team.id]?.max || currentPoints;
                maxPossibleText = `<span class="max-possible">max: ${maxPossible}</span>`;
            }

            return `
                <div class="standing-item ${isSelected ? 'selected' : ''}">
                    <div class="standing-rank">${this.getRankEmoji(idx + 1)}</div>
                    <div class="team-color-dot" style="background-color: ${team.color || '#3b82f6'};"></div>
                    <div class="standing-name">${team.name}</div>
                    <div class="standing-points">
                        ${this.mode === 'simulated' ? finalPoints : currentPoints} pts
                        ${this.mode === 'simulated' && pointsGained !== 0 ?
                            `<span class="points-diff ${pointsGained > 0 ? 'positive' : 'negative'}">
                                ${pointsGained > 0 ? '+' : ''}${pointsGained}
                            </span>` : ''}
                        ${this.mode === 'current' ? maxPossibleText : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    getRankEmoji(rank) {
        const emojis = ['🥇', '🥈', '🥉'];
        return emojis[rank - 1] || `${rank}`;
    }
}

/**
 * Game Placement Input Component
 * Touch-friendly placement controls for each game
 */
class GamePlacementInput {
    constructor(container, state) {
        this.container = container;
        this.state = state;
        this.render();
        this.state.subscribe(() => this.render());
    }

    render() {
        if (this.state.games.length === 0) {
            this.container.innerHTML = `
                <div class="no-games-message">
                    <p>No upcoming games to simulate</p>
                </div>
            `;
            return;
        }

        this.container.innerHTML = this.state.games.map(game => `
            <div class="game-simulation-card" data-game-id="${game.id}">
                <div class="game-simulation-header">
                    <div class="game-info">
                        <div class="game-number">#${game.sequence_number || game.id}</div>
                        <div class="game-details">
                            <div class="game-name">${game.name}</div>
                            <div class="game-meta">
                                <span class="game-badge ${game.type}">${game.type}</span>
                                <span class="game-points">×${game.point_scheme} points</span>
                            </div>
                        </div>
                    </div>
                    <button class="btn-randomize-icon" data-game-id="${game.id}" title="Randomize this game">
                        <i class="fas fa-dice"></i>
                    </button>
                </div>
                <div class="game-simulation-body">
                    ${this.renderPlacementGrid(game)}
                </div>
            </div>
        `).join('');

        // Attach event listeners
        this.attachEventListeners();
    }

    renderPlacementGrid(game) {
        const teamCount = this.state.teams.length;

        return `
            <div class="placement-grid">
                ${this.state.teams.map(team => {
                    const placement = this.state.placements[game.id]?.[team.id] || 1;
                    const points = calculateGameScore(placement, game.point_scheme, teamCount);

                    return `
                        <div class="placement-row" data-team-id="${team.id}" data-game-id="${game.id}">
                            <div class="placement-team">
                                <div class="team-color-dot" style="background-color: ${team.color || '#3b82f6'};"></div>
                                <span>${team.name}</span>
                            </div>
                            <div class="placement-controls">
                                <select class="placement-dropdown"
                                        data-team-id="${team.id}"
                                        data-game-id="${game.id}">
                                    ${Array.from({length: teamCount}, (_, i) => i + 1).map(place => `
                                        <option value="${place}" ${place === placement ? 'selected' : ''}>
                                            ${this.getPlaceLabel(place)} place
                                        </option>
                                    `).join('')}
                                </select>
                            </div>
                            <div class="placement-points">
                                +${points} pts
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    getPlaceLabel(place) {
        const labels = ['1st', '2nd', '3rd'];
        return labels[place - 1] || `${place}th`;
    }

    attachEventListeners() {
        // Placement dropdowns
        this.container.querySelectorAll('.placement-dropdown').forEach(select => {
            select.addEventListener('change', (e) => {
                const gameId = parseInt(e.target.dataset.gameId);
                const teamId = parseInt(e.target.dataset.teamId);
                const placement = parseInt(e.target.value);
                this.state.setPlacement(gameId, teamId, placement);
            });
        });

        // Randomize game icon buttons
        this.container.querySelectorAll('.btn-randomize-icon').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const gameId = parseInt(e.target.dataset.gameId);
                this.state.randomizePlacements(gameId);
            });
        });
    }
}

/**
 * Outcome Summary Component
 * Plain-language explanation of current scenario with placement-specific messaging
 */
class OutcomeSummary {
    constructor(container, state) {
        this.container = container;
        this.state = state;
        this.render();
        this.state.subscribe(() => this.render());
    }

    render() {
        const results = this.state.getSimulatedResults();
        const selectedTeam = results.find(t => t.id === this.state.selectedTeamId);
        const selectedRank = results.findIndex(t => t.id === this.state.selectedTeamId) + 1;
        const leader = results[0];

        if (!selectedTeam) {
            this.container.innerHTML = '<p class="error-message">Please select a team</p>';
            return;
        }

        let summaryText = '';
        let summaryClass = '';

        if (selectedRank === 1) {
            // Team secures 1st place
            summaryText = `🎉 <strong>${selectedTeam.name} secures 1st place!</strong> Final score: ${selectedTeam.finalPoints} pts`;
            summaryClass = 'outcome-win';
        } else {
            // Team doesn't win - show specific placement and gap to leader
            const pointsBehind = leader.finalPoints - selectedTeam.finalPoints;
            summaryText = `${selectedTeam.name} finishes ${this.getOrdinal(selectedRank)} with ${selectedTeam.finalPoints} pts (${pointsBehind} pts behind ${leader.name})`;
            summaryClass = 'outcome-loss';
        }

        this.container.innerHTML = `
            <div class="outcome-summary ${summaryClass}">
                <div class="outcome-text">${summaryText}</div>
            </div>
        `;
    }

    getOrdinal(n) {
        const s = ['th', 'st', 'nd', 'rd'];
        const v = n % 100;
        return n + (s[(v - 20) % 10] || s[v] || s[0]);
    }
}

/**
 * Win Simulator Component
 * Finds and displays paths to victory with improved UX
 */
class WinSimulator {
    constructor(container, state) {
        this.container = container;
        this.state = state;
        this.render();
        this.state.subscribe(() => this.render());
    }

    render() {
        const gameCount = this.state.games.length;
        const canCompute = gameCount > 0 && gameCount <= 10;

        if (!canCompute) {
            this.container.innerHTML = `
                <div class="win-simulator-card">
                    <p class="info-message">
                        ${this.state.games.length === 0 ? 'No upcoming games available.' : 'Path calculator only works with 1-10 upcoming games.'}
                    </p>
                </div>
            `;
            return;
        }

        // Check if winning is possible
        const winPossibility = evaluateWinPossibility(
            this.state.teams,
            this.state.games,
            this.state.selectedTeamId
        );

        // Only show button if winning is mathematically possible
        if (winPossibility.status === 'none') {
            this.container.innerHTML = '';
            return;
        }

        this.container.innerHTML = `
            <div class="win-simulator-card">
                <button class="btn-primary btn-compute-path" id="computePathBtn">
                    <span class="btn-text">Show Me a Winning Path</span>
                    <span class="btn-spinner" style="display: none;">
                        <i class="fas fa-spinner fa-spin"></i> Calculating...
                    </span>
                </button>
                <p class="btn-explanation">This calculates a possible scenario where you win 1st place and fills it in below</p>
                <div id="pathResults"></div>
            </div>
        `;

        // Compute button listener
        const computeBtn = this.container.querySelector('#computePathBtn');
        if (computeBtn) {
            computeBtn.addEventListener('click', () => this.computePath());
        }
    }

    computePath() {
        const computeBtn = this.container.querySelector('#computePathBtn');
        const btnText = this.container.querySelector('.btn-text');
        const btnSpinner = this.container.querySelector('.btn-spinner');
        const resultsContainer = this.container.querySelector('#pathResults');

        // Show loading state
        computeBtn.disabled = true;
        btnText.style.display = 'none';
        btnSpinner.style.display = 'inline-block';

        // Use setTimeout to allow UI to update
        setTimeout(() => {
            const scenario = findMinimalWinningScenario(
                this.state.teams,
                this.state.games,
                this.state.selectedTeamId
            );

            // Reset button state
            computeBtn.disabled = false;
            btnText.style.display = 'inline-block';
            btnSpinner.style.display = 'none';

            if (!scenario) {
                resultsContainer.innerHTML = `
                    <div class="path-results no-path">
                        <div class="result-icon">❌</div>
                        <p><strong>No winning path found</strong></p>
                        <p class="result-explanation">Based on current standings and remaining games, there's no combination of results that guarantees 1st place for your team.</p>
                    </div>
                `;
            } else {
                // Automatically apply the scenario
                // Apply the user's placements
                scenario.placements.forEach(p => {
                    this.state.setPlacement(p.game.id, this.state.selectedTeamId, p.place);
                });

                // Apply all rivals' placements from the complete scenario
                if (scenario.completeScenario) {
                    Object.keys(scenario.completeScenario).forEach(gameId => {
                        const gamePlacements = scenario.completeScenario[gameId];
                        Object.keys(gamePlacements).forEach(teamId => {
                            this.state.setPlacement(
                                parseInt(gameId),
                                parseInt(teamId),
                                gamePlacements[teamId]
                            );
                        });
                    });
                }

                // Show success message
                resultsContainer.innerHTML = `
                    <div class="path-results has-path">
                        <div class="result-icon">✅</div>
                        <p><strong>Winning scenario applied!</strong></p>
                    </div>
                `;

                // Show success banner and scroll to results
                showSuccessBanner('Scenario Applied!', 'Scroll down to see the projected results.');

                // Auto-scroll to Projected Results tab
                setTimeout(() => {
                    // Switch to Projected Results tab
                    const projectedTab = document.getElementById('projectedTab');
                    if (projectedTab) {
                        projectedTab.click();
                    }

                    // Scroll to results zone
                    const resultsZone = document.querySelector('.results-zone');
                    if (resultsZone) {
                        resultsZone.scrollIntoView({ behavior: 'smooth', block: 'start' });

                        // Add highlight animation to results zone
                        resultsZone.classList.add('highlight-pulse');
                        setTimeout(() => {
                            resultsZone.classList.remove('highlight-pulse');
                        }, 2000);
                    }
                }, 300);
            }
        }, 150);
    }

    calculateScore(place, multiplier) {
        const teamCount = this.state.teams.length;
        return (teamCount + 1 - place) * multiplier;
    }

    getOrdinalSuffix(n) {
        const s = ['th', 'st', 'nd', 'rd'];
        const v = n % 100;
        return (s[(v - 20) % 10] || s[v] || s[0]);
    }

    getOrdinal(n) {
        const s = ['th', 'st', 'nd', 'rd'];
        const v = n % 100;
        return n + (s[(v - 20) % 10] || s[v] || s[0]);
    }
}

/**
 * Share Scenario Component - REMOVED
 * Feature has been removed as per user request
 */

// ============================================================================
// MAIN INITIALIZATION
// ============================================================================

function initPlayground(teams, games) {
    // Sort teams by current points
    teams.sort((a, b) => (b.totalPoints || 0) - (a.totalPoints || 0));

    // Initialize state
    const state = new PlaygroundState(teams, games);

    // Initialize components
    const teamSelector = new TeamSelector(
        document.getElementById('teamSelectorContainer'),
        state
    );

    const winBanner = new WinPossibilityBanner(
        document.getElementById('winPossibilityContainer'),
        state
    );

    const currentStandings = new StandingsDisplay(
        document.getElementById('currentStandings'),
        state,
        'current'
    );

    const simulatedStandings = new StandingsDisplay(
        document.getElementById('simulatedStandings'),
        state,
        'simulated'
    );

    const gamePlacement = new GamePlacementInput(
        document.getElementById('gamePlacementContainer'),
        state
    );

    const outcomeSummary = new OutcomeSummary(
        document.getElementById('outcomeSummaryContainer'),
        state
    );

    const winSimulator = new WinSimulator(
        document.getElementById('winSimulatorContainer'),
        state
    );

    // Share scenario feature removed as per user request

    // Global reset button
    const resetAllBtn = document.getElementById('resetAllBtn');
    if (resetAllBtn) {
        resetAllBtn.addEventListener('click', () => {
            state.resetPlacements();
        });
    }
}

// Export for use in HTML
window.initPlayground = initPlayground;

// Auto-initialize when DOM is ready if data is available
document.addEventListener('DOMContentLoaded', () => {
    if (window.playgroundTeams && window.playgroundGames) {
        initPlayground(window.playgroundTeams, window.playgroundGames);
    }
});
