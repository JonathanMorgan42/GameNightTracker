/**
 * Unit tests for playground.js
 * Tests simulation engine and win possibility calculations
 */

import { describe, it, expect, beforeEach } from 'vitest';

describe('Base Points Calculation', () => {
  let basePoints;

  beforeEach(() => {
    basePoints = function(place, teamCount) {
      if (place < 1 || place > teamCount) return 0;
      return teamCount + 1 - place;
    };
  });

  it('should calculate 1st place points correctly', () => {
    expect(basePoints(1, 7)).toBe(7);
    expect(basePoints(1, 10)).toBe(10);
  });

  it('should calculate last place points correctly', () => {
    expect(basePoints(7, 7)).toBe(1);
    expect(basePoints(10, 10)).toBe(1);
  });

  it('should calculate middle place points correctly', () => {
    expect(basePoints(4, 7)).toBe(4);
    expect(basePoints(5, 10)).toBe(6);
  });

  it('should return 0 for invalid placement (too low)', () => {
    expect(basePoints(0, 5)).toBe(0);
    expect(basePoints(-1, 5)).toBe(0);
  });

  it('should return 0 for invalid placement (too high)', () => {
    expect(basePoints(8, 7)).toBe(0);
    expect(basePoints(11, 10)).toBe(0);
  });

  it('should work with single team', () => {
    expect(basePoints(1, 1)).toBe(1);
  });
});

describe('Game Score with Multiplier', () => {
  let calculateGameScore;
  let basePoints;

  beforeEach(() => {
    basePoints = function(place, teamCount) {
      if (place < 1 || place > teamCount) return 0;
      return teamCount + 1 - place;
    };

    calculateGameScore = function(place, multiplier, teamCount) {
      return basePoints(place, teamCount) * multiplier;
    };
  });

  it('should apply multiplier correctly', () => {
    expect(calculateGameScore(1, 3, 7)).toBe(21); // 7 * 3
    expect(calculateGameScore(1, 5, 10)).toBe(50); // 10 * 5
  });

  it('should calculate last place with multiplier', () => {
    expect(calculateGameScore(7, 3, 7)).toBe(3); // 1 * 3
  });

  it('should handle multiplier of 1', () => {
    expect(calculateGameScore(1, 1, 5)).toBe(5);
    expect(calculateGameScore(3, 1, 5)).toBe(3);
  });

  it('should handle multiplier of 10', () => {
    expect(calculateGameScore(1, 10, 5)).toBe(50);
  });
});

describe('Min/Max Points Computation', () => {
  let computeMaxMinPoints;
  let teams;
  let games;

  beforeEach(() => {
    teams = [
      { id: 1, name: 'Team A', totalPoints: 20 },
      { id: 2, name: 'Team B', totalPoints: 15 },
      { id: 3, name: 'Team C', totalPoints: 10 }
    ];

    games = [
      { id: 1, name: 'Game 1', point_scheme: 3 },
      { id: 2, name: 'Game 2', point_scheme: 5 }
    ];

    computeMaxMinPoints = function(teams, games) {
      const teamCount = teams.length;
      const results = {};

      teams.forEach(team => {
        let maxPoints = team.totalPoints || 0;
        let minPoints = team.totalPoints || 0;

        games.forEach(game => {
          const firstPlacePoints = (teamCount + 1 - 1) * game.point_scheme;
          const lastPlacePoints = (teamCount + 1 - teamCount) * game.point_scheme;
          maxPoints += firstPlacePoints;
          minPoints += lastPlacePoints;
        });

        results[team.id] = { min: minPoints, max: maxPoints };
      });

      return results;
    };
  });

  it('should calculate max points (winning all games)', () => {
    const result = computeMaxMinPoints(teams, games);

    // Team A: 20 + (3*3) + (3*5) = 20 + 9 + 15 = 44
    expect(result[1].max).toBe(44);
  });

  it('should calculate min points (losing all games)', () => {
    const result = computeMaxMinPoints(teams, games);

    // Team A: 20 + (1*3) + (1*5) = 20 + 3 + 5 = 28
    expect(result[1].min).toBe(28);
  });

  it('should work with no remaining games', () => {
    const result = computeMaxMinPoints(teams, []);

    expect(result[1].max).toBe(20);
    expect(result[1].min).toBe(20);
  });

  it('should handle team with zero points', () => {
    teams[2].totalPoints = 0;
    const result = computeMaxMinPoints(teams, games);

    // Team C: 0 + (3*3) + (3*5) = 24
    expect(result[3].max).toBe(24);
    // Team C: 0 + (1*3) + (1*5) = 8
    expect(result[3].min).toBe(8);
  });
});

describe('Win Possibility Evaluation', () => {
  let evaluateWinPossibility;
  let teams;
  let games;

  beforeEach(() => {
    teams = [
      { id: 1, name: 'Team A', totalPoints: 50 },
      { id: 2, name: 'Team B', totalPoints: 45 },
      { id: 3, name: 'Team C', totalPoints: 30 }
    ];

    games = [
      { id: 1, name: 'Final Game', point_scheme: 3 }
    ];

    evaluateWinPossibility = function(teams, games, selectedTeamId) {
      const teamCount = teams.length;

      // Compute max/min for all teams
      const maxMinPoints = {};
      teams.forEach(team => {
        let maxPoints = team.totalPoints || 0;
        let minPoints = team.totalPoints || 0;

        games.forEach(game => {
          maxPoints += (teamCount + 1 - 1) * game.point_scheme;
          minPoints += (teamCount + 1 - teamCount) * game.point_scheme;
        });

        maxMinPoints[team.id] = { min: minPoints, max: maxPoints };
      });

      const selectedTeam = teams.find(t => t.id === selectedTeamId);
      if (!selectedTeam) return { status: 'none', explanation: 'Team not found' };

      const userMax = maxMinPoints[selectedTeamId].max;
      const userMin = maxMinPoints[selectedTeamId].min;

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
          explanation: `Even if you win every remaining game, ${blocker.name}'s lowest possible outcome is higher.`,
          blocker: blocker.name,
          userMax,
          blockerMin: highestRivalMin
        };
      }

      // Guaranteed win
      if (userMin > highestRivalMax) {
        return {
          status: 'guaranteed',
          explanation: `You're guaranteed to win!`,
          userMin,
          rivalMax: highestRivalMax
        };
      }

      // Still possible
      const pointsNeeded = highestRivalMax - (selectedTeam.totalPoints || 0) + 1;
      return {
        status: 'possible',
        explanation: `Need at least ${pointsNeeded} more points to secure 1st place.`,
        pointsNeeded,
        userMax,
        rivalMax: highestRivalMax
      };
    };
  });

  it('should detect when win is guaranteed', () => {
    teams[0].totalPoints = 100; // Team A has huge lead
    teams[1].totalPoints = 10;
    teams[2].totalPoints = 5;

    const result = evaluateWinPossibility(teams, games, 1);
    expect(result.status).toBe('guaranteed');
  });

  it('should detect when win is possible', () => {
    const result = evaluateWinPossibility(teams, games, 1);
    expect(result.status).toBe('possible');
  });

  it('should detect when win is impossible', () => {
    teams[0].totalPoints = 10; // Team A far behind
    teams[1].totalPoints = 100;
    teams[2].totalPoints = 95;

    const result = evaluateWinPossibility(teams, games, 1);
    expect(result.status).toBe('none');
    expect(result.blocker).toBeDefined();
  });

  it('should handle single game remaining', () => {
    const result = evaluateWinPossibility(teams, games, 2);
    expect(['guaranteed', 'possible', 'none']).toContain(result.status);
  });

  it('should return error for invalid team', () => {
    const result = evaluateWinPossibility(teams, games, 999);
    expect(result.status).toBe('none');
    expect(result.explanation).toContain('not found');
  });
});

describe('Simulate Results', () => {
  let simulateResults;
  let teams;
  let games;
  let placements;

  beforeEach(() => {
    teams = [
      { id: 1, name: 'Team A', totalPoints: 20 },
      { id: 2, name: 'Team B', totalPoints: 15 },
      { id: 3, name: 'Team C', totalPoints: 10 }
    ];

    games = [
      { id: 1, name: 'Game 1', point_scheme: 3 }
    ];

    placements = {
      1: {
        1: 1, // Team A gets 1st place
        2: 2, // Team B gets 2nd place
        3: 3  // Team C gets 3rd place
      }
    };

    simulateResults = function(teams, games, placements) {
      const teamCount = teams.length;

      return teams.map(team => {
        let finalPoints = team.totalPoints || 0;

        games.forEach(game => {
          const placement = placements[game.id]?.[team.id] || teamCount;
          const points = (teamCount + 1 - placement) * game.point_scheme;
          finalPoints += points;
        });

        return {
          ...team,
          finalPoints,
          pointsGained: finalPoints - (team.totalPoints || 0)
        };
      }).sort((a, b) => b.finalPoints - a.finalPoints);
    };
  });

  it('should calculate final points correctly', () => {
    const results = simulateResults(teams, games, placements);

    // Team A: 20 + (3*3) = 29
    expect(results[0].finalPoints).toBe(29);
    expect(results[0].id).toBe(1);
  });

  it('should sort teams by final points', () => {
    const results = simulateResults(teams, games, placements);

    expect(results[0].id).toBe(1); // Team A (29 points)
    expect(results[1].id).toBe(2); // Team B (21 points)
    expect(results[2].id).toBe(3); // Team C (13 points)
  });

  it('should calculate points gained', () => {
    const results = simulateResults(teams, games, placements);

    expect(results[0].pointsGained).toBe(9);  // Team A gained 9
    expect(results[1].pointsGained).toBe(6);  // Team B gained 6
    expect(results[2].pointsGained).toBe(3);  // Team C gained 3
  });

  it('should handle multiple games', () => {
    games.push({ id: 2, name: 'Game 2', point_scheme: 5 });
    placements[2] = {
      1: 2, // Team A gets 2nd
      2: 1, // Team B gets 1st
      3: 3  // Team C gets 3rd
    };

    const results = simulateResults(teams, games, placements);

    // Team A: 20 + 9 + (2*5) = 39
    // Team B: 15 + 6 + (3*5) = 36
    expect(results[0].id).toBe(1);
    expect(results[0].finalPoints).toBe(39);
  });

  it('should default to last place if placement missing', () => {
    placements[1] = {
      1: 1,
      2: 2
      // Team C placement missing - should default to last (3rd)
    };

    const results = simulateResults(teams, games, placements);
    const teamC = results.find(t => t.id === 3);

    // Team C: 10 + (1*3) = 13
    expect(teamC.finalPoints).toBe(13);
  });
});

describe('Playground State Management', () => {
  let PlaygroundState;

  beforeEach(() => {
    PlaygroundState = class {
      constructor(teams, games) {
        this.teams = teams;
        this.games = games;
        this.selectedTeamId = teams[0]?.id || null;
        this.placements = {};
        this.listeners = [];
        this.resetPlacements();
      }

      resetPlacements() {
        this.games.forEach(game => {
          this.placements[game.id] = {};
          this.teams.forEach((team, idx) => {
            this.placements[game.id][team.id] = idx + 1;
          });
        });
        this.notifyListeners();
      }

      setPlacement(gameId, teamId, placement) {
        if (!this.placements[gameId]) {
          this.placements[gameId] = {};
        }

        const currentOccupant = Object.keys(this.placements[gameId]).find(
          tid => parseInt(tid) !== teamId && this.placements[gameId][tid] === placement
        );

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

      subscribe(listener) {
        this.listeners.push(listener);
        return () => {
          this.listeners = this.listeners.filter(l => l !== listener);
        };
      }

      notifyListeners() {
        this.listeners.forEach(listener => listener());
      }
    };
  });

  it('should initialize with first team selected', () => {
    const teams = [
      { id: 1, name: 'Team A' },
      { id: 2, name: 'Team B' }
    ];
    const games = [{ id: 1, name: 'Game 1', point_scheme: 3 }];

    const state = new PlaygroundState(teams, games);
    expect(state.selectedTeamId).toBe(1);
  });

  it('should reset placements to default order', () => {
    const teams = [
      { id: 1, name: 'Team A' },
      { id: 2, name: 'Team B' },
      { id: 3, name: 'Team C' }
    ];
    const games = [{ id: 1, name: 'Game 1', point_scheme: 3 }];

    const state = new PlaygroundState(teams, games);

    expect(state.placements[1][1]).toBe(1);
    expect(state.placements[1][2]).toBe(2);
    expect(state.placements[1][3]).toBe(3);
  });

  it('should update placement and swap if needed', () => {
    const teams = [
      { id: 1, name: 'Team A' },
      { id: 2, name: 'Team B' }
    ];
    const games = [{ id: 1, name: 'Game 1', point_scheme: 3 }];

    const state = new PlaygroundState(teams, games);
    state.setPlacement(1, 2, 1); // Move Team B to 1st

    expect(state.placements[1][2]).toBe(1); // Team B now 1st
    expect(state.placements[1][1]).toBe(2); // Team A swapped to 2nd
  });

  it('should change selected team', () => {
    const teams = [
      { id: 1, name: 'Team A' },
      { id: 2, name: 'Team B' }
    ];
    const games = [];

    const state = new PlaygroundState(teams, games);
    state.setSelectedTeam(2);

    expect(state.selectedTeamId).toBe(2);
  });

  it('should notify listeners on state change', () => {
    const teams = [{ id: 1, name: 'Team A' }];
    const games = [{ id: 1, name: 'Game 1', point_scheme: 3 }];

    const state = new PlaygroundState(teams, games);
    let notified = false;

    state.subscribe(() => {
      notified = true;
    });

    state.setSelectedTeam(1);
    expect(notified).toBe(true);
  });

  it('should allow unsubscribing listeners', () => {
    const teams = [{ id: 1, name: 'Team A' }];
    const games = [];

    const state = new PlaygroundState(teams, games);
    let callCount = 0;

    const unsubscribe = state.subscribe(() => {
      callCount++;
    });

    state.setSelectedTeam(1);
    expect(callCount).toBe(1);

    unsubscribe();
    state.setSelectedTeam(1);
    expect(callCount).toBe(1); // Should not increase
  });
});
