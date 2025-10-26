"""Helper functions for route handlers."""
from app.models.team import Team
from app.services.game_night_service import GameNightService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_teams_for_game_night(game_night_id=None):
    """
    Get teams for a specific game night, with fallback logic.

    Args:
        game_night_id: Optional game night ID. If None, uses active game night.

    Returns:
        List of Team objects
    """
    if game_night_id:
        teams = Team.query.filter_by(game_night_id=game_night_id).all()
        logger.debug(f"Retrieved {len(teams)} teams for game_night_id={game_night_id}")
    else:
        # Fallback to active game night teams
        active_gn = GameNightService.get_active_game_night()
        if active_gn:
            teams = Team.query.filter_by(game_night_id=active_gn.id).all()
            logger.debug(f"Retrieved {len(teams)} teams for active game night id={active_gn.id}")
        else:
            teams = Team.query.all()
            logger.debug(f"Retrieved all {len(teams)} teams (no active game night)")

    return teams


def collect_scores_from_form(request, teams):
    """
    Extract score data from form submission.

    Args:
        request: Flask request object
        teams: List of Team objects

    Returns:
        Dictionary mapping team_id to score data dict

    Example:
        {
            1: {'score': 100.0, 'points': 10, 'notes': 'Great job!'},
            2: {'score': 85.5, 'points': 8}
        }
    """
    scores_data = {}

    for team in teams:
        score_value = request.form.get(f'score-{team.id}')
        points = request.form.get(f'points-input-{team.id}')
        notes = request.form.get(f'notes-{team.id}')

        if score_value or points:
            scores_data[team.id] = {}

            if score_value:
                try:
                    scores_data[team.id]['score'] = float(score_value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid score value for team {team.id}: {score_value}")
                    pass

            if points:
                try:
                    scores_data[team.id]['points'] = int(points)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid points value for team {team.id}: {points}")
                    pass

            if notes:
                scores_data[team.id]['notes'] = notes

    logger.debug(f"Collected scores for {len(scores_data)} teams")
    return scores_data


def serialize_penalties(penalties, game):
    """
    Convert penalty objects to dictionaries for JSON/template use.

    Args:
        penalties: List of Penalty objects
        game: Game object (for metric_type)

    Returns:
        List of penalty dictionaries
    """
    return [{
        'id': p.id,
        'name': p.name,
        'value': p.value,
        'unit': 'seconds' if game.metric_type == 'time' else 'points',
        'stackable': p.stackable
    } for p in penalties]


def serialize_teams(teams):
    """
    Convert team objects to dictionaries for JSON/template use.

    Args:
        teams: List of Team objects

    Returns:
        List of team dictionaries
    """
    return [{
        'id': t.id,
        'name': t.name,
        'color': t.color
    } for t in teams]


def serialize_existing_scores(existing_scores):
    """
    Convert existing score objects to dictionaries for JSON/template use.

    Args:
        existing_scores: Dictionary mapping team_id to Score object

    Returns:
        Dictionary mapping team_id to score data dict
    """
    return {
        team_id: {
            'score_value': score.score_value,
            'points': score.points,
            'notes': score.notes
        }
        for team_id, score in existing_scores.items()
    }


def is_ajax_request(request):
    """
    Check if the request is an AJAX request.

    Args:
        request: Flask request object

    Returns:
        Boolean indicating if request is AJAX
    """
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'
