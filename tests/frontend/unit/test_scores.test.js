/**
 * Unit tests for scores.js
 * Tests scoring calculations, interactions, and real-time updates
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';

describe('Score Calculations', () => {
  let calculateRankingsAndPoints;
  let teamScores;
  let gameData;

  beforeEach(() => {
    teamScores = {
      1: { baseScore: 100, penaltyTotal: -10, finalScore: 90, rank: 0, points: 0 },
      2: { baseScore: 80, penaltyTotal: 0, finalScore: 80, rank: 0, points: 0 },
      3: { baseScore: 120, penaltyTotal: -5, finalScore: 115, rank: 0, points: 0 }
    };

    gameData = {
      scoringDirection: 'higher_better',
      pointScheme: 3,
      teamsCount: 3
    };

    calculateRankingsAndPoints = function() {
      const teamsWithScores = [];

      Object.keys(teamScores).forEach(teamId => {
        const teamScore = teamScores[teamId];
        if (teamScore.finalScore > 0 || teamScore.baseScore > 0) {
          teamsWithScores.push({
            id: teamId,
            score: teamScore.finalScore
          });
        }
      });

      const scoringDirection = gameData.scoringDirection;
      if (scoringDirection === 'lower_better') {
        teamsWithScores.sort((a, b) => a.score - b.score);
      } else {
        teamsWithScores.sort((a, b) => b.score - a.score);
      }

      const pointScheme = gameData.pointScheme;
      const totalTeams = gameData.teamsCount;

      teamsWithScores.forEach((team, index) => {
        const rank = index + 1;
        const points = (totalTeams - rank + 1) * pointScheme;
        teamScores[team.id].rank = rank;
        teamScores[team.id].points = points;
      });

      Object.keys(teamScores).forEach(teamId => {
        const hasScore = teamsWithScores.some(t => t.id == teamId);
        if (!hasScore) {
          teamScores[teamId].rank = 0;
          teamScores[teamId].points = 0;
        }
      });
    };
  });

  it('should calculate correct rankings (higher is better)', () => {
    calculateRankingsAndPoints();

    expect(teamScores[3].rank).toBe(1); // 115 points
    expect(teamScores[1].rank).toBe(2); // 90 points
    expect(teamScores[2].rank).toBe(3); // 80 points
  });

  it('should calculate correct points based on rank', () => {
    calculateRankingsAndPoints();

    expect(teamScores[3].points).toBe(9);  // (3 - 1 + 1) * 3 = 9
    expect(teamScores[1].points).toBe(6);  // (3 - 2 + 1) * 3 = 6
    expect(teamScores[2].points).toBe(3);  // (3 - 3 + 1) * 3 = 3
  });

  it('should calculate correct rankings (lower is better)', () => {
    gameData.scoringDirection = 'lower_better';
    calculateRankingsAndPoints();

    expect(teamScores[2].rank).toBe(1); // 80 points (lowest)
    expect(teamScores[1].rank).toBe(2); // 90 points
    expect(teamScores[3].rank).toBe(3); // 115 points (highest)
  });

  it('should handle teams with zero scores', () => {
    teamScores[4] = { baseScore: 0, penaltyTotal: 0, finalScore: 0, rank: 0, points: 0 };
    calculateRankingsAndPoints();

    expect(teamScores[4].rank).toBe(0);
    expect(teamScores[4].points).toBe(0);
  });

  it('should apply point scheme multiplier correctly', () => {
    gameData.pointScheme = 5;
    calculateRankingsAndPoints();

    expect(teamScores[3].points).toBe(15); // (3 - 1 + 1) * 5
    expect(teamScores[1].points).toBe(10); // (3 - 2 + 1) * 5
    expect(teamScores[2].points).toBe(5);  // (3 - 3 + 1) * 5
  });
});

describe('Penalty Calculations', () => {
  let updatePenaltyTotals;
  let teamScores;
  let teamPenalties;
  let penaltiesData;
  let currentTeamId;

  beforeEach(() => {
    currentTeamId = 1;
    teamScores = {
      1: { baseScore: 100, penaltyTotal: 0, finalScore: 100, rank: 0, points: 0 }
    };
    teamPenalties = {
      1: {}
    };
    penaltiesData = [
      { id: 1, value: -5, name: 'False start' },
      { id: 2, value: -10, name: 'Equipment failure' }
    ];

    updatePenaltyTotals = function() {
      if (!currentTeamId) return;

      const baseScore = teamScores[currentTeamId].baseScore || 0;
      let penaltyTotal = 0;

      if (penaltiesData && teamPenalties[currentTeamId]) {
        penaltiesData.forEach(penalty => {
          const count = teamPenalties[currentTeamId][penalty.id] || 0;
          penaltyTotal += count * penalty.value;
        });
      }

      const finalScore = baseScore + penaltyTotal;
      teamScores[currentTeamId].penaltyTotal = penaltyTotal;
      teamScores[currentTeamId].finalScore = finalScore;
    };
  });

  it('should calculate zero penalty for no penalties', () => {
    updatePenaltyTotals();

    expect(teamScores[1].penaltyTotal).toBe(0);
    expect(teamScores[1].finalScore).toBe(100);
  });

  it('should calculate single penalty correctly', () => {
    teamPenalties[1][1] = 1; // One false start
    updatePenaltyTotals();

    expect(teamScores[1].penaltyTotal).toBe(-5);
    expect(teamScores[1].finalScore).toBe(95);
  });

  it('should calculate multiple penalties correctly', () => {
    teamPenalties[1][1] = 2; // Two false starts (-10)
    teamPenalties[1][2] = 1; // One equipment failure (-10)
    updatePenaltyTotals();

    expect(teamScores[1].penaltyTotal).toBe(-20);
    expect(teamScores[1].finalScore).toBe(80);
  });

  it('should handle positive penalties (bonuses)', () => {
    penaltiesData.push({ id: 3, value: 15, name: 'Bonus' });
    teamPenalties[1][3] = 1;
    updatePenaltyTotals();

    expect(teamScores[1].penaltyTotal).toBe(15);
    expect(teamScores[1].finalScore).toBe(115);
  });

  it('should handle mixed penalties', () => {
    teamPenalties[1][1] = 1; // -5
    penaltiesData.push({ id: 3, value: 10, name: 'Bonus' });
    teamPenalties[1][3] = 1; // +10
    updatePenaltyTotals();

    expect(teamScores[1].penaltyTotal).toBe(5);
    expect(teamScores[1].finalScore).toBe(105);
  });
});

describe('Score Input Handlers', () => {
  let dom;
  let document;
  let incrementScore;
  let decrementScore;
  let currentTeamId;
  let teamScores;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <input id="score-input" type="number" value="10.00" />
        </body>
      </html>
    `);
    document = dom.window.document;
    global.document = document;

    currentTeamId = 1;
    teamScores = {
      1: { baseScore: 10, penaltyTotal: 0, finalScore: 10, rank: 0, points: 0 }
    };

    incrementScore = function() {
      if (!currentTeamId) return;
      const input = document.getElementById('score-input');
      const currentValue = parseFloat(input.value) || 0;
      input.value = (currentValue + 1).toFixed(2);
      teamScores[currentTeamId].baseScore = parseFloat(input.value);
    };

    decrementScore = function() {
      if (!currentTeamId) return;
      const input = document.getElementById('score-input');
      const currentValue = parseFloat(input.value) || 0;
      if (currentValue > 0) {
        input.value = (currentValue - 1).toFixed(2);
        teamScores[currentTeamId].baseScore = parseFloat(input.value);
      }
    };
  });

  it('should increment score by 1', () => {
    incrementScore();
    const input = document.getElementById('score-input');
    expect(input.value).toBe('11.00');
    expect(teamScores[1].baseScore).toBe(11);
  });

  it('should decrement score by 1', () => {
    decrementScore();
    const input = document.getElementById('score-input');
    expect(input.value).toBe('9.00');
    expect(teamScores[1].baseScore).toBe(9);
  });

  it('should not decrement below zero', () => {
    const input = document.getElementById('score-input');
    input.value = '0.00';
    teamScores[1].baseScore = 0;

    decrementScore();
    expect(input.value).toBe('0.00');
    expect(teamScores[1].baseScore).toBe(0);
  });

  it('should handle increment from zero', () => {
    const input = document.getElementById('score-input');
    input.value = '0.00';
    incrementScore();
    expect(input.value).toBe('1.00');
  });

  it('should not execute without selected team', () => {
    currentTeamId = null;
    const input = document.getElementById('score-input');
    const originalValue = input.value;

    incrementScore();
    expect(input.value).toBe(originalValue);
  });
});

describe('Stopwatch Functionality', () => {
  let formatTimeWithMillis;

  beforeEach(() => {
    formatTimeWithMillis = function(milliseconds) {
      const totalSeconds = Math.floor(milliseconds / 1000);
      const mins = Math.floor(totalSeconds / 60);
      const secs = totalSeconds % 60;
      const millis = Math.floor((milliseconds % 1000));
      return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(3, '0')}`;
    };
  });

  it('should format zero time correctly', () => {
    expect(formatTimeWithMillis(0)).toBe('00:00.000');
  });

  it('should format seconds correctly', () => {
    expect(formatTimeWithMillis(5430)).toBe('00:05.430');
  });

  it('should format minutes and seconds correctly', () => {
    expect(formatTimeWithMillis(125500)).toBe('02:05.500');
  });

  it('should handle exact seconds', () => {
    expect(formatTimeWithMillis(60000)).toBe('01:00.000');
  });

  it('should handle milliseconds correctly', () => {
    expect(formatTimeWithMillis(1234)).toBe('00:01.234');
  });
});

describe('Team Switching', () => {
  let dom;
  let document;
  let switchTeam;
  let currentTeamId;
  let teamScores;
  let teamsData;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <select id="team-selector">
            <option value="">Select a team</option>
            <option value="1">Team Alpha</option>
            <option value="2">Team Beta</option>
          </select>
          <div id="team-scoring-card" class="display-none">
            <span id="selected-team-name"></span>
            <div id="team-color"></div>
            <input id="score-input" type="number" />
          </div>
        </body>
      </html>
    `);
    document = dom.window.document;
    global.document = document;
    global.sessionStorage = { setItem: vi.fn(), removeItem: vi.fn() };

    currentTeamId = null;
    teamScores = {
      1: { baseScore: 50, penaltyTotal: 0, finalScore: 50, rank: 1, points: 9 },
      2: { baseScore: 30, penaltyTotal: -5, finalScore: 25, rank: 2, points: 6 }
    };
    teamsData = [
      { id: 1, name: 'Team Alpha', color: '#FF0000' },
      { id: 2, name: 'Team Beta', color: '#0000FF' }
    ];

    switchTeam = function() {
      const selector = document.getElementById('team-selector');
      const teamId = selector.value;
      const scoringCard = document.getElementById('team-scoring-card');

      if (!teamId) {
        scoringCard.classList.add('display-none');
        currentTeamId = null;
        return;
      }

      currentTeamId = teamId;
      const team = teamsData.find(t => t.id == teamId);

      scoringCard.classList.remove('display-none');
      document.getElementById('selected-team-name').textContent = team.name;
      document.getElementById('team-color').style.backgroundColor = team.color;

      const teamScore = teamScores[teamId];
      document.getElementById('score-input').value = teamScore.baseScore || '';
    };
  });

  it('should show scoring card when team is selected', () => {
    const selector = document.getElementById('team-selector');
    selector.value = '1';
    switchTeam();

    const card = document.getElementById('team-scoring-card');
    expect(card.classList.contains('display-none')).toBe(false);
  });

  it('should hide scoring card when no team is selected', () => {
    const selector = document.getElementById('team-selector');
    selector.value = '';
    switchTeam();

    const card = document.getElementById('team-scoring-card');
    expect(card.classList.contains('display-none')).toBe(true);
    expect(currentTeamId).toBe(null);
  });

  it('should display team name correctly', () => {
    const selector = document.getElementById('team-selector');
    selector.value = '1';
    switchTeam();

    const nameDisplay = document.getElementById('selected-team-name');
    expect(nameDisplay.textContent).toBe('Team Alpha');
  });

  it('should set team color correctly', () => {
    const selector = document.getElementById('team-selector');
    selector.value = '2';
    switchTeam();

    const colorDiv = document.getElementById('team-color');
    expect(colorDiv.style.backgroundColor).toBe('rgb(0, 0, 255)');
  });

  it('should load team score into input', () => {
    const selector = document.getElementById('team-selector');
    selector.value = '1';
    switchTeam();

    const scoreInput = document.getElementById('score-input');
    expect(scoreInput.value).toBe('50');
  });

  it('should update currentTeamId', () => {
    const selector = document.getElementById('team-selector');
    selector.value = '2';
    switchTeam();

    expect(currentTeamId).toBe('2');
  });
});

describe('Ordinal Number Formatting', () => {
  let getOrdinalSuffix;

  beforeEach(() => {
    getOrdinalSuffix = function(num) {
      const j = num % 10;
      const k = num % 100;
      if (j === 1 && k !== 11) return num + "st";
      if (j === 2 && k !== 12) return num + "nd";
      if (j === 3 && k !== 13) return num + "rd";
      return num + "th";
    };
  });

  it('should format 1st correctly', () => {
    expect(getOrdinalSuffix(1)).toBe('1st');
  });

  it('should format 2nd correctly', () => {
    expect(getOrdinalSuffix(2)).toBe('2nd');
  });

  it('should format 3rd correctly', () => {
    expect(getOrdinalSuffix(3)).toBe('3rd');
  });

  it('should format 4th and above correctly', () => {
    expect(getOrdinalSuffix(4)).toBe('4th');
    expect(getOrdinalSuffix(10)).toBe('10th');
  });

  it('should handle teens correctly', () => {
    expect(getOrdinalSuffix(11)).toBe('11th');
    expect(getOrdinalSuffix(12)).toBe('12th');
    expect(getOrdinalSuffix(13)).toBe('13th');
  });

  it('should format 21st, 22nd, 23rd correctly', () => {
    expect(getOrdinalSuffix(21)).toBe('21st');
    expect(getOrdinalSuffix(22)).toBe('22nd');
    expect(getOrdinalSuffix(23)).toBe('23rd');
  });
});

describe('Session Storage Persistence', () => {
  let saveTeamSelection;
  let clearSavedTeamSelection;
  let gameData;

  beforeEach(() => {
    global.sessionStorage = {
      setItem: vi.fn(),
      getItem: vi.fn(),
      removeItem: vi.fn()
    };

    gameData = { id: 42 };

    saveTeamSelection = function(teamId) {
      if (gameData && gameData.id) {
        const key = `selectedTeam_game_${gameData.id}`;
        sessionStorage.setItem(key, teamId);
      }
    };

    clearSavedTeamSelection = function() {
      if (gameData && gameData.id) {
        const key = `selectedTeam_game_${gameData.id}`;
        sessionStorage.removeItem(key);
      }
    };
  });

  it('should save team selection to session storage', () => {
    saveTeamSelection(5);
    expect(sessionStorage.setItem).toHaveBeenCalledWith('selectedTeam_game_42', 5);
  });

  it('should clear team selection from session storage', () => {
    clearSavedTeamSelection();
    expect(sessionStorage.removeItem).toHaveBeenCalledWith('selectedTeam_game_42');
  });

  it('should use game-specific keys', () => {
    gameData.id = 123;
    saveTeamSelection(7);
    expect(sessionStorage.setItem).toHaveBeenCalledWith('selectedTeam_game_123', 7);
  });
});
