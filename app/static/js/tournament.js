/**
 * Tournament JavaScript
 * Handles tournament bracket modal interactions and match scoring
 */

let currentMatchId = null;
let team1Id = null;
let team2Id = null;

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    attachTournamentListeners();
});

// Attach event listeners
function attachTournamentListeners() {
    // Close modal button
    const closeBtn = document.querySelector('.modal .close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeScoreModal);
    }

    // Cancel button
    const cancelBtn = document.querySelector('[data-action="cancel-modal"]');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeScoreModal);
    }

    // Score form submission
    const scoreForm = document.getElementById('scoreForm');
    if (scoreForm) {
        scoreForm.addEventListener('submit', submitScore);
    }

    // Winner selection buttons
    const selectWinner1Btn = document.querySelector('[data-action="select-winner-1"]');
    if (selectWinner1Btn) {
        selectWinner1Btn.addEventListener('click', function() {
            selectWinner(1);
        });
    }

    const selectWinner2Btn = document.querySelector('[data-action="select-winner-2"]');
    if (selectWinner2Btn) {
        selectWinner2Btn.addEventListener('click', function() {
            selectWinner(2);
        });
    }

    // Score inputs for auto-highlighting
    const team1ScoreInput = document.getElementById('team1Score');
    const team2ScoreInput = document.getElementById('team2Score');

    if (team1ScoreInput && team2ScoreInput) {
        team1ScoreInput.addEventListener('input', handleScoreInput);
        team2ScoreInput.addEventListener('input', handleScoreInput);
    }

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('scoreModal');
        if (event.target === modal) {
            closeScoreModal();
        }
    });

    // Match cards with click handlers
    document.querySelectorAll('[data-action="open-score-modal"]').forEach(card => {
        card.addEventListener('click', function() {
            const matchId = this.getAttribute('data-match-id');
            const team1Name = this.getAttribute('data-team1-name');
            const team2Name = this.getAttribute('data-team2-name');
            const t1Id = this.getAttribute('data-team1-id');
            const t2Id = this.getAttribute('data-team2-id');
            const team1Color = this.getAttribute('data-team1-color');
            const team2Color = this.getAttribute('data-team2-color');
            const roundNum = this.getAttribute('data-round-num');

            openScoreModal(matchId, team1Name, team2Name, t1Id, t2Id, team1Color, team2Color, roundNum);
        });
    });
}

function openScoreModal(matchId, team1Name, team2Name, t1Id, t2Id, team1Color, team2Color, roundNum) {
    currentMatchId = matchId;
    team1Id = t1Id;
    team2Id = t2Id;

    document.getElementById('matchId').value = matchId;
    document.getElementById('team1Name').textContent = team1Name;
    document.getElementById('team2Name').textContent = team2Name;
    document.getElementById('team1Color').style.backgroundColor = team1Color;
    document.getElementById('team2Color').style.backgroundColor = team2Color;

    // Set round info
    const roundNames = {
        1: 'Round 1',
        2: 'Quarter-finals',
        3: 'Semi-finals',
        4: 'Final'
    };
    const roundName = roundNames[roundNum] || `Round ${roundNum}`;
    document.getElementById('roundInfo').innerHTML = `<i class="fas fa-layer-group"></i> ${roundName}`;

    // Clear previous values
    document.getElementById('team1Score').value = '';
    document.getElementById('team2Score').value = '';
    document.getElementById('winnerId').value = '';
    const winnerDisplay = document.getElementById('winnerDisplay');
    winnerDisplay.textContent = '';
    winnerDisplay.classList.remove('show');
    document.getElementById('team1Section').classList.remove('winner-selected');
    document.getElementById('team2Section').classList.remove('winner-selected');
    document.getElementById('submitBtn').disabled = true;

    document.getElementById('scoreModal').style.display = 'block';
}

function closeScoreModal() {
    document.getElementById('scoreModal').style.display = 'none';
}

function selectWinner(teamNum) {
    // Remove selected class from both sections
    document.getElementById('team1Section').classList.remove('winner-selected');
    document.getElementById('team2Section').classList.remove('winner-selected');

    const winnerDisplay = document.getElementById('winnerDisplay');

    if (teamNum === 1) {
        document.getElementById('winnerId').value = team1Id;
        document.getElementById('team1Section').classList.add('winner-selected');
        winnerDisplay.innerHTML = '<i class="fas fa-trophy"></i> ' + document.getElementById('team1Name').textContent + ' selected as winner';
    } else {
        document.getElementById('winnerId').value = team2Id;
        document.getElementById('team2Section').classList.add('winner-selected');
        winnerDisplay.innerHTML = '<i class="fas fa-trophy"></i> ' + document.getElementById('team2Name').textContent + ' selected as winner';
    }

    // Show winner display and enable submit button
    winnerDisplay.classList.add('show');
    document.getElementById('submitBtn').disabled = false;
}

function handleScoreInput() {
    const team1Score = parseFloat(document.getElementById('team1Score').value);
    const team2Score = parseFloat(document.getElementById('team2Score').value);

    // Auto-highlight higher score
    if (!isNaN(team1Score) && !isNaN(team2Score)) {
        document.getElementById('team1Score').parentElement.classList.remove('leading-score');
        document.getElementById('team2Score').parentElement.classList.remove('leading-score');

        if (team1Score > team2Score) {
            document.getElementById('team1Score').parentElement.classList.add('leading-score');
        } else if (team2Score > team1Score) {
            document.getElementById('team2Score').parentElement.classList.add('leading-score');
        }
    }
}

async function submitScore(event) {
    event.preventDefault();

    const matchId = document.getElementById('matchId').value;
    const team1Score = parseFloat(document.getElementById('team1Score').value) || null;
    const team2Score = parseFloat(document.getElementById('team2Score').value) || null;
    const winnerId = parseInt(document.getElementById('winnerId').value);

    if (!winnerId) {
        alert('Please select a winner');
        return;
    }

    try {
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;

        // Determine the endpoint based on whether user is authenticated
        // This will be set by the template
        const isAuthenticated = window.isAuthenticated || false;
        const endpoint = isAuthenticated ?
            `/admin/tournament/match/${matchId}/score` :
            `/tournament/match/${matchId}/score`;

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                team1_score: team1Score,
                team2_score: team2Score,
                winner_team_id: winnerId
            })
        });

        const data = await response.json();

        if (data.success) {
            closeScoreModal();
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error submitting score: ' + error.message);
    }
}
