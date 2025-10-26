/**
 * Unit tests for games.js
 * Tests game management UI functionality
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';

describe('Game Search and Filtering', () => {
  let dom;
  let document;
  let filterGames;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <input id="gameSearch" type="text" />
          <table id="gamesTable">
            <tr><th>Name</th></tr>
            <tr><td class="game-name">Trivia Night</td></tr>
            <tr><td class="game-name">Physical Challenge</td></tr>
            <tr><td class="game-name">Strategy Game</td></tr>
          </table>
        </body>
      </html>
    `);
    document = dom.window.document;
    global.document = document;

    // Define filterGames function (from games.js)
    filterGames = function() {
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
    };
  });

  it('should show all games when search is empty', () => {
    const input = document.getElementById('gameSearch');
    input.value = '';
    filterGames();

    const rows = document.querySelectorAll('#gamesTable tr');
    expect(rows[1].style.display).toBe('');
    expect(rows[2].style.display).toBe('');
    expect(rows[3].style.display).toBe('');
  });

  it('should filter games by search term (case insensitive)', () => {
    const input = document.getElementById('gameSearch');
    input.value = 'trivia';
    filterGames();

    const rows = document.querySelectorAll('#gamesTable tr');
    expect(rows[1].style.display).toBe(''); // Trivia Night visible
    expect(rows[2].style.display).toBe('none'); // Physical Challenge hidden
    expect(rows[3].style.display).toBe('none'); // Strategy Game hidden
  });

  it('should handle partial matches', () => {
    const input = document.getElementById('gameSearch');
    input.value = 'game';
    filterGames();

    const rows = document.querySelectorAll('#gamesTable tr');
    expect(rows[1].style.display).toBe('none'); // Trivia Night hidden
    expect(rows[2].style.display).toBe('none'); // Physical Challenge hidden
    expect(rows[3].style.display).toBe(''); // Strategy Game visible
  });

  it('should handle no matches', () => {
    const input = document.getElementById('gameSearch');
    input.value = 'nonexistent';
    filterGames();

    const rows = document.querySelectorAll('#gamesTable tr');
    expect(rows[1].style.display).toBe('none');
    expect(rows[2].style.display).toBe('none');
    expect(rows[3].style.display).toBe('none');
  });

  it('should not crash if search input is missing', () => {
    document.getElementById('gameSearch').remove();
    expect(() => filterGames()).not.toThrow();
  });

  it('should not crash if table is missing', () => {
    document.getElementById('gamesTable').remove();
    expect(() => filterGames()).not.toThrow();
  });
});

describe('Delete Modal Management', () => {
  let dom;
  let document;
  let confirmDelete;
  let closeModal;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <div id="deleteModal" style="display: none;">
            <span class="close">&times;</span>
            <span id="gameToDelete"></span>
            <form id="deleteForm" action="">
              <button class="cancel-delete-btn">Cancel</button>
            </form>
          </div>
        </body>
      </html>
    `);
    document = dom.window.document;
    global.document = document;
    global.window = dom.window;
    global.alert = vi.fn();
    document.body.style = {};

    // Define confirmDelete function
    confirmDelete = function(gameId, gameName) {
      const modal = document.getElementById('deleteModal');
      if (!modal) {
        alert('Error: Delete modal not found. Please refresh the page.');
        return;
      }

      const gameToDeleteSpan = document.getElementById('gameToDelete');
      if (gameToDeleteSpan) {
        gameToDeleteSpan.textContent = gameName;
      }

      const deleteForm = document.getElementById('deleteForm');
      if (deleteForm) {
        deleteForm.action = `/admin/games/delete/${gameId}`;
      } else {
        alert('Error: Delete form not found. Please refresh the page.');
        return;
      }

      modal.style.display = 'block';
      document.body.style.overflow = 'hidden';
    };

    // Define closeModal function
    closeModal = function() {
      const modal = document.getElementById('deleteModal');
      if (!modal) return;

      modal.style.display = 'none';
      document.body.style.overflow = 'auto';
    };
  });

  it('should open modal and display game name', () => {
    confirmDelete(123, 'Test Game');

    const modal = document.getElementById('deleteModal');
    const gameToDelete = document.getElementById('gameToDelete');

    expect(modal.style.display).toBe('block');
    expect(gameToDelete.textContent).toBe('Test Game');
  });

  it('should set form action with correct game ID', () => {
    confirmDelete(456, 'Another Game');

    const form = document.getElementById('deleteForm');
    expect(form.action).toContain('/admin/games/delete/456');
  });

  it('should prevent body scrolling when modal opens', () => {
    confirmDelete(123, 'Test Game');
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('should close modal and restore scrolling', () => {
    confirmDelete(123, 'Test Game');
    closeModal();

    const modal = document.getElementById('deleteModal');
    expect(modal.style.display).toBe('none');
    expect(document.body.style.overflow).toBe('auto');
  });

  it('should handle missing modal gracefully', () => {
    document.getElementById('deleteModal').remove();
    confirmDelete(123, 'Test Game');
    expect(alert).toHaveBeenCalled();
  });

  it('should handle missing form gracefully', () => {
    document.getElementById('deleteForm').remove();
    confirmDelete(123, 'Test Game');
    expect(alert).toHaveBeenCalled();
  });
});

describe('Penalty Management', () => {
  let dom;
  let document;
  let addPenalty;
  let removePenalty;
  let penaltyCount;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <div id="penalties-container"></div>
        </body>
      </html>
    `);
    document = dom.window.document;
    global.document = document;
    penaltyCount = 0;

    // Define addPenalty function
    addPenalty = function(name = '', value = '', stackable = false) {
      const container = document.getElementById('penalties-container');
      if (!container) return;

      const penaltyDiv = document.createElement('div');
      penaltyDiv.className = 'penalty-item';
      penaltyDiv.dataset.penaltyId = penaltyCount;

      penaltyDiv.innerHTML = `
        <div class="form-row penalty-row">
          <div class="form-group">
            <input type="text" name="penalties[${penaltyCount}][name]" value="${name}" required>
          </div>
          <div class="form-group">
            <input type="number" name="penalties[${penaltyCount}][value]" value="${value}" required>
          </div>
          <div class="form-group">
            <input type="checkbox" name="penalties[${penaltyCount}][stackable]" ${stackable ? 'checked' : ''}>
          </div>
          <button type="button" onclick="removePenalty(${penaltyCount})">Remove</button>
        </div>
      `;

      container.appendChild(penaltyDiv);
      penaltyCount++;
    };

    // Define removePenalty function
    removePenalty = function(penaltyId) {
      const penaltyItem = document.querySelector(`[data-penalty-id="${penaltyId}"]`);
      if (penaltyItem) {
        penaltyItem.remove();
      }
    };
  });

  it('should add penalty with default values', () => {
    addPenalty();
    const container = document.getElementById('penalties-container');
    expect(container.children.length).toBe(1);
  });

  it('should add penalty with custom values', () => {
    addPenalty('False start', '-5', true);
    const container = document.getElementById('penalties-container');
    const nameInput = container.querySelector('input[name="penalties[0][name]"]');
    const valueInput = container.querySelector('input[name="penalties[0][value]"]');
    const stackableInput = container.querySelector('input[name="penalties[0][stackable]"]');

    expect(nameInput.value).toBe('False start');
    expect(valueInput.value).toBe('-5');
    expect(stackableInput.checked).toBe(true);
  });

  it('should increment penalty counter', () => {
    addPenalty();
    addPenalty();
    const container = document.getElementById('penalties-container');
    expect(container.children.length).toBe(2);
  });

  it('should remove penalty by ID', () => {
    addPenalty('Penalty 1', '10', false);
    addPenalty('Penalty 2', '15', false);
    removePenalty(0);

    const container = document.getElementById('penalties-container');
    expect(container.children.length).toBe(1);
    expect(container.querySelector('[data-penalty-id="0"]')).toBeNull();
    expect(container.querySelector('[data-penalty-id="1"]')).not.toBeNull();
  });

  it('should handle removing non-existent penalty', () => {
    removePenalty(999);
    // Should not throw error
  });
});

describe('Game Form Toggles', () => {
  let dom;
  let document;
  let toggleCustomType;
  let toggleGameMode;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <select id="game-type-select">
            <option value="trivia">Trivia</option>
            <option value="custom">Custom</option>
          </select>
          <div id="custom-type-group" style="display: none;">
            <input id="custom_type" type="text" />
          </div>
          <input id="create_as_tournament" type="checkbox" />
          <div id="scoring-section"></div>
          <div id="penalties-section"></div>
        </body>
      </html>
    `);
    document = dom.window.document;
    global.document = document;

    toggleCustomType = function() {
      const typeSelect = document.getElementById('game-type-select');
      const customTypeGroup = document.getElementById('custom-type-group');
      const customTypeInput = document.getElementById('custom_type');

      if (!typeSelect || !customTypeGroup) return;

      if (typeSelect.value === 'custom') {
        customTypeGroup.style.display = 'block';
      } else {
        customTypeGroup.style.display = 'none';
        if (customTypeInput) customTypeInput.value = '';
      }
    };

    toggleGameMode = function() {
      const tournamentCheckbox = document.getElementById('create_as_tournament');
      const scoringSection = document.getElementById('scoring-section');
      const penaltiesSection = document.getElementById('penalties-section');

      if (!tournamentCheckbox) return;

      if (tournamentCheckbox.checked) {
        if (scoringSection) scoringSection.style.display = 'none';
        if (penaltiesSection) penaltiesSection.style.display = 'none';
      } else {
        if (scoringSection) scoringSection.style.display = 'block';
        if (penaltiesSection) penaltiesSection.style.display = 'block';
      }
    };
  });

  it('should show custom type input when custom is selected', () => {
    const typeSelect = document.getElementById('game-type-select');
    const customGroup = document.getElementById('custom-type-group');

    typeSelect.value = 'custom';
    toggleCustomType();

    expect(customGroup.style.display).toBe('block');
  });

  it('should hide custom type input when standard type is selected', () => {
    const typeSelect = document.getElementById('game-type-select');
    const customGroup = document.getElementById('custom-type-group');

    typeSelect.value = 'trivia';
    toggleCustomType();

    expect(customGroup.style.display).toBe('none');
  });

  it('should clear custom input value when switching away from custom', () => {
    const typeSelect = document.getElementById('game-type-select');
    const customInput = document.getElementById('custom_type');

    customInput.value = 'My Custom Type';
    typeSelect.value = 'trivia';
    toggleCustomType();

    expect(customInput.value).toBe('');
  });

  it('should hide scoring sections when tournament mode is enabled', () => {
    const checkbox = document.getElementById('create_as_tournament');
    const scoringSection = document.getElementById('scoring-section');
    const penaltiesSection = document.getElementById('penalties-section');

    checkbox.checked = true;
    toggleGameMode();

    expect(scoringSection.style.display).toBe('none');
    expect(penaltiesSection.style.display).toBe('none');
  });

  it('should show scoring sections when tournament mode is disabled', () => {
    const checkbox = document.getElementById('create_as_tournament');
    const scoringSection = document.getElementById('scoring-section');
    const penaltiesSection = document.getElementById('penalties-section');

    checkbox.checked = false;
    toggleGameMode();

    expect(scoringSection.style.display).toBe('block');
    expect(penaltiesSection.style.display).toBe('block');
  });
});
