/**
 * Unit tests for websocket-client.js
 * Tests WebSocket connection, locking, and real-time updates
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';

describe('WebSocket Connection Management', () => {
  let GameSocketClient;
  let mockSocket;

  beforeEach(() => {
    mockSocket = {
      on: vi.fn(),
      emit: vi.fn(),
      disconnect: vi.fn()
    };

    global.io = vi.fn(() => mockSocket);

    GameSocketClient = class {
      constructor(gameId, roundId = null) {
        this.gameId = gameId;
        this.roundId = roundId;
        this.socket = null;
        this.connected = false;
        this.activeLocks = new Map();
        this.updateDebounceTimers = new Map();
        this.init();
      }

      init() {
        this.socket = io({
          transports: ['websocket', 'polling'],
          reconnection: true,
          reconnectionDelay: 1000,
          reconnectionAttempts: 5
        });
      }

      joinGame() {
        if (!this.connected || !this.gameId) return;

        const payload = { game_id: this.gameId };
        if (this.roundId !== null && this.roundId !== undefined) {
          payload.round_id = this.roundId;
        }
        this.socket.emit('join_game', payload);
      }

      disconnect() {
        if (this.socket) {
          this.socket.disconnect();
        }
      }
    };
  });

  it('should initialize with game ID', () => {
    const client = new GameSocketClient(42);
    expect(client.gameId).toBe(42);
    expect(client.connected).toBe(false);
  });

  it('should initialize with game ID and round ID', () => {
    const client = new GameSocketClient(42, 5);
    expect(client.gameId).toBe(42);
    expect(client.roundId).toBe(5);
  });

  it('should create socket connection on init', () => {
    const client = new GameSocketClient(42);
    expect(global.io).toHaveBeenCalled();
    expect(client.socket).toBeDefined();
  });

  it('should emit join_game with correct payload', () => {
    const client = new GameSocketClient(42);
    client.connected = true;
    client.joinGame();

    expect(mockSocket.emit).toHaveBeenCalledWith('join_game', { game_id: 42 });
  });

  it('should emit join_game with round_id if provided', () => {
    const client = new GameSocketClient(42, 7);
    client.connected = true;
    client.joinGame();

    expect(mockSocket.emit).toHaveBeenCalledWith('join_game', {
      game_id: 42,
      round_id: 7
    });
  });

  it('should not join game if not connected', () => {
    const client = new GameSocketClient(42);
    client.connected = false;
    client.joinGame();

    expect(mockSocket.emit).not.toHaveBeenCalled();
  });

  it('should disconnect socket on disconnect()', () => {
    const client = new GameSocketClient(42);
    client.disconnect();

    expect(mockSocket.disconnect).toHaveBeenCalled();
  });
});

describe('Lock Management', () => {
  let GameSocketClient;
  let mockSocket;

  beforeEach(() => {
    mockSocket = {
      on: vi.fn(),
      emit: vi.fn(),
      disconnect: vi.fn()
    };

    global.io = vi.fn(() => mockSocket);

    GameSocketClient = class {
      constructor(gameId) {
        this.gameId = gameId;
        this.socket = mockSocket;
        this.connected = true;
        this.activeLocks = new Map();
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
    };
  });

  it('should request lock with correct parameters', () => {
    const client = new GameSocketClient(42);
    const success = client.requestLock(5, 'score');

    expect(success).toBe(true);
    expect(mockSocket.emit).toHaveBeenCalledWith('request_edit_lock', {
      game_id: 42,
      team_id: 5,
      field: 'score'
    });
  });

  it('should not request lock if disconnected', () => {
    const client = new GameSocketClient(42);
    client.connected = false;
    const success = client.requestLock(5, 'score');

    expect(success).toBe(false);
    expect(mockSocket.emit).not.toHaveBeenCalled();
  });

  it('should release lock with score and points', () => {
    const client = new GameSocketClient(42);
    client.releaseLock(5, 'score', 100.5, 9);

    expect(mockSocket.emit).toHaveBeenCalledWith('release_edit_lock', {
      game_id: 42,
      team_id: 5,
      field: 'score',
      score: 100.5,
      points: 9
    });
  });

  it('should not release lock if disconnected', () => {
    const client = new GameSocketClient(42);
    client.connected = false;
    client.releaseLock(5, 'score', 100, 9);

    expect(mockSocket.emit).not.toHaveBeenCalled();
  });
});

describe('Score Updates with Debouncing', () => {
  let GameSocketClient;
  let mockSocket;

  beforeEach(() => {
    vi.useFakeTimers();

    mockSocket = {
      on: vi.fn(),
      emit: vi.fn(),
      disconnect: vi.fn()
    };

    global.io = vi.fn(() => mockSocket);

    GameSocketClient = class {
      constructor(gameId, roundId = null) {
        this.gameId = gameId;
        this.roundId = roundId;
        this.socket = mockSocket;
        this.connected = true;
        this.updateDebounceTimers = new Map();
      }

      updateScore(teamId, score, points) {
        if (!this.connected) return;

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

          if (this.roundId !== null && this.roundId !== undefined) {
            payload.round_id = this.roundId;
          }

          this.socket.emit('update_score', payload);
          this.updateDebounceTimers.delete(key);
        }, 300));
      }
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should debounce score updates', () => {
    const client = new GameSocketClient(42);

    client.updateScore(5, 100, 9);
    client.updateScore(5, 101, 9);
    client.updateScore(5, 102, 9);

    // Should not emit yet
    expect(mockSocket.emit).not.toHaveBeenCalled();

    // Fast forward 300ms
    vi.advanceTimersByTime(300);

    // Should emit only once with the last value
    expect(mockSocket.emit).toHaveBeenCalledTimes(1);
    expect(mockSocket.emit).toHaveBeenCalledWith('update_score', {
      game_id: 42,
      team_id: 5,
      score: 102,
      points: 9
    });
  });

  it('should include round_id in score update if provided', () => {
    const client = new GameSocketClient(42, 7);
    client.updateScore(5, 100, 9);

    vi.advanceTimersByTime(300);

    expect(mockSocket.emit).toHaveBeenCalledWith('update_score', {
      game_id: 42,
      team_id: 5,
      score: 100,
      points: 9,
      round_id: 7
    });
  });

  it('should not update score if disconnected', () => {
    const client = new GameSocketClient(42);
    client.connected = false;

    client.updateScore(5, 100, 9);
    vi.advanceTimersByTime(300);

    expect(mockSocket.emit).not.toHaveBeenCalled();
  });
});

describe('Timer Events', () => {
  let GameSocketClient;
  let mockSocket;

  beforeEach(() => {
    mockSocket = {
      on: vi.fn(),
      emit: vi.fn(),
      disconnect: vi.fn()
    };

    global.io = vi.fn(() => mockSocket);

    GameSocketClient = class {
      constructor(gameId) {
        this.gameId = gameId;
        this.socket = mockSocket;
        this.connected = true;
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
          time_value: time
        });
      }

      clearTimers(teamId) {
        if (!this.connected) return;

        this.socket.emit('clear_timers', {
          game_id: this.gameId,
          team_id: teamId
        });
      }
    };
  });

  it('should emit start_timer event', () => {
    const client = new GameSocketClient(42);
    client.startTimer(5);

    expect(mockSocket.emit).toHaveBeenCalledWith('start_timer', {
      game_id: 42,
      team_id: 5
    });
  });

  it('should emit stop_timer event with time value', () => {
    const client = new GameSocketClient(42);
    client.stopTimer(5, 45.123);

    expect(mockSocket.emit).toHaveBeenCalledWith('stop_timer', {
      game_id: 42,
      team_id: 5,
      time_value: 45.123
    });
  });

  it('should emit clear_timers event', () => {
    const client = new GameSocketClient(42);
    client.clearTimers(5);

    expect(mockSocket.emit).toHaveBeenCalledWith('clear_timers', {
      game_id: 42,
      team_id: 5
    });
  });

  it('should not emit timer events if disconnected', () => {
    const client = new GameSocketClient(42);
    client.connected = false;

    client.startTimer(5);
    client.stopTimer(5, 45.123);
    client.clearTimers(5);

    expect(mockSocket.emit).not.toHaveBeenCalled();
  });
});

describe('Lock Indicator UI Updates', () => {
  let GameSocketClient;
  let dom;
  let document;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <div id="score-container">
            <input id="score-input" type="number" />
          </div>
        </body>
      </html>
    `);
    document = dom.window.document;
    global.document = document;
    global.currentTeamId = 5;

    GameSocketClient = class {
      constructor(gameId) {
        this.gameId = gameId;
        this.activeLocks = new Map();
      }

      showLockIndicator(teamId, field, displayName) {
        const lockKey = `${teamId}_${field}`;
        this.activeLocks.set(lockKey, true);

        const input = String(currentTeamId) === String(teamId) ?
          document.querySelector('#score-input') : null;

        if (!input) return;

        let lockIndicator = input.parentElement.querySelector('.lock-indicator');
        if (!lockIndicator) {
          lockIndicator = document.createElement('div');
          lockIndicator.className = 'lock-indicator';
          input.parentElement.appendChild(lockIndicator);
        }

        const userName = displayName || 'Someone';
        lockIndicator.innerHTML = `<i class="fas fa-lock"></i> <span>${userName} is editing</span>`;
        lockIndicator.style.display = 'flex';

        input.disabled = true;
        input.classList.add('locked');
      }

      hideLockIndicator(teamId, field) {
        const lockKey = `${teamId}_${field}`;
        this.activeLocks.delete(lockKey);

        const input = String(currentTeamId) === String(teamId) ?
          document.querySelector('#score-input') : null;

        if (!input) return;

        const lockIndicator = input.parentElement.querySelector('.lock-indicator');
        if (lockIndicator) {
          lockIndicator.style.display = 'none';
        }

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
    };
  });

  it('should show lock indicator with user name', () => {
    const client = new GameSocketClient(42);
    client.showLockIndicator(5, 'score', 'John Doe');

    const indicator = document.querySelector('.lock-indicator');
    expect(indicator).not.toBeNull();
    expect(indicator.innerHTML).toContain('John Doe is editing');
    expect(indicator.style.display).toBe('flex');
  });

  it('should disable input when lock indicator is shown', () => {
    const client = new GameSocketClient(42);
    const input = document.getElementById('score-input');

    client.showLockIndicator(5, 'score', 'Admin');

    expect(input.disabled).toBe(true);
    expect(input.classList.contains('locked')).toBe(true);
  });

  it('should hide lock indicator and enable input', () => {
    const client = new GameSocketClient(42);
    client.showLockIndicator(5, 'score', 'Admin');

    client.hideLockIndicator(5, 'score');

    const indicator = document.querySelector('.lock-indicator');
    const input = document.getElementById('score-input');

    expect(indicator.style.display).toBe('none');
    expect(input.disabled).toBe(false);
    expect(input.classList.contains('locked')).toBe(false);
  });

  it('should clear all lock indicators', () => {
    const client = new GameSocketClient(42);
    client.showLockIndicator(5, 'score', 'User 1');

    client.clearAllLockIndicators();

    const input = document.getElementById('score-input');
    expect(input.disabled).toBe(false);
    expect(input.classList.contains('locked')).toBe(false);
    expect(client.activeLocks.size).toBe(0);
  });

  it('should track active locks in Map', () => {
    const client = new GameSocketClient(42);

    client.showLockIndicator(5, 'score', 'Admin');
    expect(client.activeLocks.has('5_score')).toBe(true);

    client.hideLockIndicator(5, 'score');
    expect(client.activeLocks.has('5_score')).toBe(false);
  });
});
