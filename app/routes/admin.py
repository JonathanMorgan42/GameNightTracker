"""Admin routes - Team, Game, Score, and Game Night management."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
import time

from app import db
from app.services import TeamService, GameService, ScoreService, TournamentService, GameNightService, RoundService
from app.forms import TeamForm, GameForm, LiveScoringForm
from app.forms.tournament_forms import TournamentSetupForm
from app.forms.game_night_forms import GameNightForm
from app.models import Team, Game
from app.exceptions import ValidationError
from app.utils.logger import get_logger
from app.utils.validators import validate_penalties_list, extract_penalties_from_form

admin_bp = Blueprint('admin', __name__)
logger = get_logger(__name__)


def validate_positive_id(id_value, name='ID'):
    """Validate that an ID is a positive integer."""
    try:
        id_int = int(id_value)
        if id_int <= 0:
            logger.warning(f'Invalid {name}: {id_value} (must be positive)')
            abort(400, description=f'{name} must be a positive integer')
        return id_int
    except (ValueError, TypeError):
        logger.warning(f'Invalid {name}: {id_value} (not an integer)')
        abort(400, description=f'{name} must be a valid integer')


# ============================================================================
# TEAM MANAGEMENT
# ============================================================================

@admin_bp.route('/teams/add', methods=['GET', 'POST'])
@login_required
def add_team():
    """Add new team."""
    # Check if game_night_id was provided as a query parameter
    game_night_id = request.args.get('game_night_id', type=int)

    # If game_night_id is provided, set it as the working context
    if game_night_id:
        try:
            GameNightService.set_working_context(game_night_id)
        except Exception as e:
            flash(f'Error setting working context: {str(e)}', 'error')
            return redirect(url_for('admin.game_night_management'))

    # Validation: Check if there's a working context game night
    working_context = GameNightService.get_working_context_game_night()

    # If no working context exists, redirect with error
    if not working_context:
        flash('You need to create a game night before adding teams.', 'error')
        return redirect(url_for('admin.create_game_night'))

    form = TeamForm()

    if form.validate_on_submit():
        participants_data = [
            {
                'firstName': form.participant1FirstName.data,
                'lastName': form.participant1LastName.data
            },
            {
                'firstName': form.participant2FirstName.data,
                'lastName': form.participant2LastName.data
            }
        ]

        # Add optional participants (3-6)
        for i in range(3, 7):
            first_name_field = getattr(form, f'participant{i}FirstName', None)
            last_name_field = getattr(form, f'participant{i}LastName', None)

            if first_name_field and last_name_field:
                first_name = first_name_field.data
                last_name = last_name_field.data

                # Only add if at least first name is provided
                if first_name and first_name.strip():
                    participants_data.append({
                        'firstName': first_name,
                        'lastName': last_name if last_name else ''
                    })

        TeamService.create_team(form.name.data, participants_data, form.color.data)
        flash('Team created successfully!', 'success')
        return redirect(url_for('main.teams'))

    return render_template('admin/add_team.html', form=form, working_context=working_context)


@admin_bp.route('/teams/edit/<int:team_id>', methods=['GET', 'POST'])
@login_required
def edit_team(team_id):
    """Edit team."""
    validate_positive_id(team_id, 'Team ID')
    team = TeamService.get_team_by_id(team_id)
    form = TeamForm()

    if request.method == 'GET':
        participants = list(team.participants)
        form.name.data = team.name
        form.color.data = team.color

        # Populate all participant fields (1-6)
        for i, participant in enumerate(participants, start=1):
            if i <= 6:
                first_name_field = getattr(form, f'participant{i}FirstName', None)
                last_name_field = getattr(form, f'participant{i}LastName', None)

                if first_name_field and last_name_field:
                    first_name_field.data = participant.firstName
                    last_name_field.data = participant.lastName

    if form.validate_on_submit():
        participants_data = [
            {
                'firstName': form.participant1FirstName.data,
                'lastName': form.participant1LastName.data
            },
            {
                'firstName': form.participant2FirstName.data,
                'lastName': form.participant2LastName.data
            }
        ]

        # Add optional participants (3-6)
        for i in range(3, 7):
            first_name_field = getattr(form, f'participant{i}FirstName', None)
            last_name_field = getattr(form, f'participant{i}LastName', None)

            if first_name_field and last_name_field:
                first_name = first_name_field.data
                last_name = last_name_field.data

                # Only add if at least first name is provided
                if first_name and first_name.strip():
                    participants_data.append({
                        'firstName': first_name,
                        'lastName': last_name if last_name else ''
                    })

        TeamService.update_team(team_id, form.name.data, participants_data, form.color.data)
        flash('Team updated successfully!', 'success')
        return redirect(url_for('main.teams'))

    return render_template('admin/edit_team.html', form=form, team=team)


@admin_bp.route('/teams/delete/<int:team_id>', methods=['POST'])
@login_required
def delete_team(team_id):
    """Delete team."""
    validate_positive_id(team_id, 'Team ID')
    try:
        TeamService.delete_team(team_id)
        flash('Team deleted successfully!', 'success')
    except SQLAlchemyError as e:
        logger.error(f'Database error deleting team {team_id}: {e}', exc_info=True)
        flash('Error deleting team: Database error occurred', 'error')
    except Exception as e:
        logger.error(f'Unexpected error deleting team {team_id}: {e}', exc_info=True)
        flash(f'Error deleting team: {str(e)}', 'error')

    return redirect(url_for('main.teams'))


# ============================================================================
# GAME MANAGEMENT
# ============================================================================

@admin_bp.route('/games/add', methods=['GET', 'POST'])
@login_required
def add_game():
    """Add new game."""
    # Check if game_night_id was provided as a query parameter
    game_night_id = request.args.get('game_night_id', type=int)

    # If game_night_id is provided, set it as the working context
    if game_night_id:
        try:
            GameNightService.set_working_context(game_night_id)
        except Exception as e:
            flash(f'Error setting working context: {str(e)}', 'error')
            return redirect(url_for('admin.game_night_management'))

    # Validation: Check if there's a working context game night
    working_context = GameNightService.get_working_context_game_night()

    # If no working context exists, redirect with error
    if not working_context:
        flash('You need to create a game night before adding games.', 'error')
        return redirect(url_for('admin.create_game_night'))

    # Validation: Check if there are teams
    team_count = Team.query.filter_by(game_night_id=working_context.id).count()
    if team_count == 0:
        flash('You need to add at least one team before adding games.', 'warning')
        return redirect(url_for('admin.add_team'))

    form = GameForm()

    if form.validate_on_submit():
        # Check if tournament mode is enabled
        create_as_tournament = request.form.get('create_as_tournament') == 'on'

        # Handle custom game type
        game_type = form.type.data
        if game_type == 'custom' and form.custom_type.data:
            game_type = form.custom_type.data.strip()

        # Override type to 'tournament' if checkbox is checked
        if create_as_tournament:
            game_type = 'tournament'

        form_data = {
            'name': form.name.data,
            'type': game_type,
            'sequence_number': form.sequence_number.data,
            'point_scheme': form.point_scheme.data,
            'metric_type': form.metric_type.data,
            'scoring_direction': form.scoring_direction.data,
            'public_input': form.public_input.data,
            'has_rounds': form.has_rounds.data,
            'number_of_rounds': form.number_of_rounds.data if form.has_rounds.data else None
        }

        # Collect and validate penalties from form
        penalties_dict = request.form.to_dict(flat=False)
        penalties_data, error_message = validate_penalties_list(penalties_dict)

        if error_message:
            flash(error_message, 'danger')
            # Extract penalties for re-display even if invalid
            penalties_for_display = extract_penalties_from_form(penalties_dict)
            team_count = Team.query.filter_by(game_night_id=working_context.id).count() if working_context else 0
            return render_template('admin/add_game.html', form=form, team_count=team_count,
                                 next_sequence=next_sequence, existing_games=existing_games,
                                 working_context=working_context, penalties_json=penalties_for_display)

        game = GameService.create_game(form_data, penalties_data)

        # Create rounds if round-based game
        if form.has_rounds.data and form.number_of_rounds.data:
            try:
                # Get round descriptions from form (if provided)
                round_descriptions = []
                for i in range(1, form.number_of_rounds.data + 1):
                    desc_key = f'round_description_{i}'
                    desc = request.form.get(desc_key, '').strip()
                    round_descriptions.append(desc if desc else None)

                RoundService.create_rounds_for_game(
                    game.id,
                    form.number_of_rounds.data,
                    round_descriptions
                )
                flash(f'Game created successfully with {form.number_of_rounds.data} rounds!', 'success')
            except Exception as e:
                logger.error(f'Error creating rounds for game {game.id}: {e}', exc_info=True)
                flash(f'Game created but error creating rounds: {str(e)}', 'warning')
        else:
            flash('Game created successfully!', 'success')

        # Redirect to tournament setup if tournament mode
        if create_as_tournament:
            flash('Now set up the tournament bracket', 'info')
            return redirect(url_for('admin.setup_tournament', game_id=game.id))

        return redirect(url_for('main.games'))

    # Get working context game night to filter games
    working_gn = working_context

    # Get next available sequence number for current game night
    if working_gn:
        max_sequence = Game.query.filter_by(game_night_id=working_gn.id).with_entities(func.max(Game.sequence_number)).scalar()
        existing_games = Game.query.filter_by(game_night_id=working_gn.id).order_by(Game.sequence_number).all()
    else:
        max_sequence = Game.query.with_entities(func.max(Game.sequence_number)).scalar()
        existing_games = Game.query.order_by(Game.sequence_number).all()

    next_sequence = (max_sequence or 0) + 1

    # Set default sequence number if not already set
    if not form.sequence_number.data:
        form.sequence_number.data = next_sequence

    team_count = Team.query.filter_by(game_night_id=working_gn.id).count() if working_gn else 0
    return render_template('admin/add_game.html', form=form, team_count=team_count,
                         next_sequence=next_sequence, existing_games=existing_games, working_context=working_context)


@admin_bp.route('/games/edit/<int:game_id>', methods=['GET', 'POST'])
@login_required
def edit_game(game_id):
    """Edit game."""
    validate_positive_id(game_id, 'Game ID')
    game = GameService.get_game_by_id(game_id)
    form = GameForm(obj=game)

    if form.validate_on_submit():
        # Handle custom game type
        game_type = form.type.data
        if game_type == 'custom' and form.custom_type.data:
            game_type = form.custom_type.data.strip()

        form_data = {
            'name': form.name.data,
            'type': game_type,
            'sequence_number': form.sequence_number.data,
            'point_scheme': form.point_scheme.data,
            'metric_type': form.metric_type.data,
            'scoring_direction': form.scoring_direction.data,
            'public_input': form.public_input.data,
            'has_rounds': form.has_rounds.data,
            'number_of_rounds': form.number_of_rounds.data if form.has_rounds.data else None
        }

        # Collect and validate penalties from form
        penalties_dict = request.form.to_dict(flat=False)
        penalties_data, error_message = validate_penalties_list(penalties_dict)

        if error_message:
            flash(error_message, 'danger')
            # Convert penalties to dictionaries for JSON serialization
            penalties = game.penalties.all()
            penalties_dict_json = [{
                'id': p.id,
                'name': p.name,
                'value': p.value,
                'stackable': p.stackable
            } for p in penalties]
            team_count = Team.query.count()
            return render_template('admin/edit_game.html', form=form, game=game, penalties_json=penalties_dict_json,
                                 team_count=team_count, existing_games=[])

        try:
            GameService.update_game(game_id, form_data, penalties_data)
            flash('Game updated successfully!', 'success')
            return redirect(url_for('main.games'))
        except Exception as e:
            flash(f'Error updating game: {str(e)}', 'error')

    # Convert penalties to dictionaries for JSON serialization
    penalties = game.penalties.all()
    penalties_dict = [{
        'id': p.id,
        'name': p.name,
        'value': p.value,
        'stackable': p.stackable
    } for p in penalties]

    # Get existing games for reference (excluding current game)
    # Filter by same game night if game has one
    if game.game_night_id:
        existing_games = Game.query.filter(Game.id != game_id, Game.game_night_id == game.game_night_id).order_by(Game.sequence_number).all()
    else:
        existing_games = Game.query.filter(Game.id != game_id).order_by(Game.sequence_number).all()

    team_count = Team.query.count()
    return render_template('admin/edit_game.html', form=form, game=game, penalties_json=penalties_dict,
                         team_count=team_count, existing_games=existing_games)


@admin_bp.route('/games/delete/<int:game_id>', methods=['POST'])
@login_required
def delete_game(game_id):
    """Delete game."""
    validate_positive_id(game_id, 'Game ID')
    try:
        game = GameService.get_game_by_id(game_id)
        game_name = game.name
        GameService.delete_game(game_id)
        flash(f'Game "{game_name}" has been deleted', 'success')
    except Exception as e:
        flash(f'Error deleting game: {str(e)}', 'error')

    return redirect(url_for('main.games'))


# ============================================================================
# SCORE MANAGEMENT
# ============================================================================

@admin_bp.route('/scores/edit/<int:game_id>', methods=['GET', 'POST'])
@admin_bp.route('/scores/edit/<int:game_id>/round/<int:round_number>', methods=['GET', 'POST'])
@login_required
def edit_scores(game_id, round_number=None):
    """Live scoring page (supports both regular and round-based games)."""
    game = GameService.get_game_by_id(game_id)
    # Get teams from the same game night as the game
    if game.game_night_id:
        teams = Team.query.filter_by(game_night_id=game.game_night_id).all()
    else:
        # Fallback to active game night teams
        active_gn = GameNightService.get_active_game_night()
        if active_gn:
            teams = Team.query.filter_by(game_night_id=active_gn.id).all()
        else:
            teams = Team.query.all()

    # Check if this is a round-based game
    rounds = []
    current_round = None
    existing_scores = {}

    if game.has_rounds:
        rounds = RoundService.get_rounds_for_game(game_id)
        # Default to first round if no round specified
        if round_number is None and rounds:
            round_number = 1

        if round_number:
            current_round = RoundService.get_round_by_game_and_number(game_id, round_number)
            if current_round:
                # Get existing scores for this round
                round_scores = RoundService.get_round_scores(current_round.id)
                existing_scores = {rs.team_id: {
                    'score_value': rs.score_value,
                    'points': rs.points,
                    'notes': rs.notes
                } for rs in round_scores}
    else:
        # Regular game, use regular scores
        existing_scores_objs = ScoreService.get_existing_scores_dict(game_id)
        existing_scores = {team_id: {
            'score_value': score.score_value,
            'points': score.points,
            'notes': score.notes
        } for team_id, score in existing_scores_objs.items()}

    form = LiveScoringForm()
    form.game_id.data = game_id

    # Handle form POST
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Collect scores from form
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
                            pass

                    if points:
                        try:
                            scores_data[team.id]['points'] = int(points)
                        except (ValueError, TypeError):
                            pass

                    if notes:
                        scores_data[team.id]['notes'] = notes

            # Save scores based on game type
            if game.has_rounds and current_round:
                # Save to round scores
                for team_id, score_data in scores_data.items():
                    RoundService.save_round_score(
                        current_round.id,
                        team_id,
                        score_data.get('score'),
                        score_data.get('points', 0),
                        score_data.get('notes')
                    )

                # Sync cumulative scores to main Score table
                ScoreService.sync_round_scores_to_main_scores(game_id)

                # Check if all rounds are complete to mark game as complete
                if form.is_completed.data:
                    game.isCompleted = True
                    db.session.commit()
                    flash(f'Game "{game.name}" finalized! Scores have been added to the leaderboard.', 'success')
                    # Redirect to home leaderboard after finalization
                    return redirect(url_for('main.index'))
                else:
                    flash(f'Scores for Round {round_number} saved successfully!', 'success')
                    # Stay on scoring page if not finalizing
                    return redirect(url_for('admin.edit_scores', game_id=game_id, round_number=round_number))
            else:
                # Regular score saving
                ScoreService.save_scores(
                    game_id,
                    scores_data,
                    form.is_completed.data
                )

                if form.is_completed.data:
                    flash(f'Game "{game.name}" finalized! Scores have been added to the leaderboard.', 'success')
                    # Redirect to home leaderboard after finalization
                    return redirect(url_for('main.index'))
                else:
                    flash('Scores saved successfully!', 'success')
                    return redirect(url_for('main.games'))
        except Exception as e:
            logger.error(f'Error saving scores for game {game_id}: {e}', exc_info=True)
            flash(f'Error saving scores: {str(e)}', 'error')

    penalties = game.penalties.all()

    # Convert penalties to dictionaries for JSON serialization
    penalties_dict = [{
        'id': p.id,
        'name': p.name,
        'value': p.value,
        'unit': 'seconds' if game.metric_type == 'time' else 'points',
        'stackable': p.stackable
    } for p in penalties]

    # Convert teams to dictionaries for JSON serialization
    teams_dict = [{
        'id': t.id,
        'name': t.name,
        'color': t.color
    } for t in teams]

    # Convert existing_scores to dictionaries for JSON serialization
    existing_scores_dict = existing_scores

    # Prepare round data for template
    rounds_dict = []
    cumulative_scores = {}
    if game.has_rounds:
        rounds_dict = [{
            'id': r.id,
            'round_number': r.round_number,
            'description': r.description,
            'name': r.name
        } for r in rounds]

        # Get cumulative scores across all rounds
        cumulative_scores = RoundService.get_cumulative_scores_for_game(game_id)

    return render_template(
        'admin/live_scoring.html',
        form=form,
        game=game,
        teams=teams,
        teams_json=teams_dict,
        existing_scores=existing_scores,
        existing_scores_json=existing_scores_dict,
        penalties=penalties_dict,
        has_rounds=game.has_rounds,
        rounds=rounds,
        rounds_json=rounds_dict,
        current_round=current_round,
        round_number=round_number,
        cumulative_scores=cumulative_scores,
        cache_bust=int(time.time())
    )


@admin_bp.route('/scores/manual-save/<int:game_id>', methods=['POST'])
@admin_bp.route('/scores/manual-save/<int:game_id>/round/<int:round_number>', methods=['POST'])
@login_required
def manual_save_scores(game_id, round_number=None):
    """Manual save endpoint that updates scores and syncs to leaderboard without marking complete."""
    try:
        game = GameService.get_game_by_id(game_id)

        # Get teams from the same game night
        if game.game_night_id:
            teams = Team.query.filter_by(game_night_id=game.game_night_id).all()
        else:
            teams = Team.query.all()

        # Collect scores from form (same logic as main edit_scores endpoint)
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
                        pass

                if points:
                    try:
                        scores_data[team.id]['points'] = int(points)
                    except (ValueError, TypeError):
                        pass

                if notes:
                    scores_data[team.id]['notes'] = notes

        # Save based on game type
        if game.has_rounds and round_number:
            # Get the current round
            current_round = RoundService.get_round_by_game_and_number(game_id, round_number)

            if current_round:
                # Save to round scores
                for team_id, score_data in scores_data.items():
                    RoundService.save_round_score(
                        current_round.id,
                        team_id,
                        score_data.get('score'),
                        score_data.get('points', 0),
                        score_data.get('notes')
                    )

                # Sync cumulative scores to main Score table
                ScoreService.sync_round_scores_to_main_scores(game_id)

                return jsonify({
                    'success': True,
                    'message': f'Round {round_number} scores saved and leaderboard updated!'
                })
        else:
            # Regular score saving (without marking complete)
            ScoreService.save_scores(
                game_id,
                scores_data,
                is_completed=False  # Never mark complete on manual save
            )

            return jsonify({
                'success': True,
                'message': 'Scores saved and leaderboard updated!'
            })

    except Exception as e:
        logger.error(f'Error manually saving scores for game {game_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/scores/save/<int:game_id>', methods=['POST'])
@admin_bp.route('/scores/save/<int:game_id>/round/<int:round_id>', methods=['POST'])
@login_required
def save_scores(game_id, round_id=None):
    """AJAX endpoint for saving scores (supports both regular and round-based games)."""
    data = request.json

    try:
        if round_id:
            # Save round scores
            scores_data = data.get('scores', {})
            for team_id_str, score_data in scores_data.items():
                team_id = int(team_id_str)
                RoundService.save_round_score(
                    round_id,
                    team_id,
                    score_data.get('score'),
                    score_data.get('points', 0),
                    score_data.get('notes')
                )

            # Sync cumulative scores to main Score table
            ScoreService.sync_round_scores_to_main_scores(game_id)
        else:
            # Regular score saving
            ScoreService.save_scores(
                game_id,
                data.get('scores', {}),
                data.get('isCompleted', False),
                data.get('notes')
            )
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error saving scores: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 400


# ============================================================================
# TOURNAMENT MANAGEMENT
# ============================================================================

@admin_bp.route('/tournament/create', methods=['GET', 'POST'])
@login_required
def create_tournament_direct():
    """Create a tournament directly (combines game creation and tournament setup)."""
    from app.forms.tournament_forms import TournamentSetupForm

    if request.method == 'POST':
        form = TournamentSetupForm()
        if form.validate_on_submit():
            # Create the game first
            game_name = request.form.get('game_name', 'Tournament')

            # Get active game night to filter games
            active_gn = GameNightService.get_active_game_night()
            if active_gn:
                sequence_number = Game.query.filter_by(game_night_id=active_gn.id).with_entities(func.max(Game.sequence_number)).scalar() or 0
            else:
                sequence_number = Game.query.with_entities(func.max(Game.sequence_number)).scalar() or 0
            sequence_number += 1

            game_data = {
                'name': game_name,
                'type': 'tournament',
                'sequence_number': sequence_number,
                'point_scheme': 1,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False
            }

            game = GameService.create_game(game_data, [])

            # Create tournament
            try:
                # Get included teams (filter out unchecked teams)
                included_team_ids = request.form.getlist('included_teams')
                included_team_ids = [int(tid) for tid in included_team_ids] if included_team_ids else None

                tournament = TournamentService.create_tournament(
                    game_id=game.id,
                    pairing_type=form.pairing_type.data,
                    bracket_style=form.bracket_style.data,
                    public_edit=form.public_edit.data,
                    included_team_ids=included_team_ids
                )
                flash(f'Tournament "{game_name}" created successfully!', 'success')
                return redirect(url_for('admin.view_tournament', game_id=game.id))
            except Exception as e:
                # If tournament creation fails, delete the game
                GameService.delete_game(game.id)
                flash(f'Error creating tournament: {str(e)}', 'error')
                return redirect(url_for('main.games'))

    # GET request - show form
    form = TournamentSetupForm()
    # Get teams from active game night
    active_gn = GameNightService.get_active_game_night()
    if active_gn:
        teams = Team.query.filter_by(game_night_id=active_gn.id).all()
    else:
        teams = Team.query.all()
    return render_template('admin/create_tournament_direct.html', form=form, teams=teams)


@admin_bp.route('/tournament/setup/<int:game_id>', methods=['GET', 'POST'])
@login_required
def setup_tournament(game_id):
    """Setup tournament bracket for a game."""
    game = GameService.get_game_by_id(game_id)

    # Check if tournament already exists - if so, redirect to view it
    existing_tournament = TournamentService.get_tournament_by_game(game_id)
    if existing_tournament:
        # Tournament already created, redirect to view it
        return redirect(url_for('admin.view_tournament', game_id=game_id))

    form = TournamentSetupForm()
    form.game_id.data = game_id

    if form.validate_on_submit():
        try:
            # Get included teams (filter out unchecked teams)
            included_team_ids = request.form.getlist('included_teams')
            included_team_ids = [int(tid) for tid in included_team_ids] if included_team_ids else None

            # Parse manual pairings if provided
            manual_pairings = None
            if form.pairing_type.data == 'manual':
                manual_pairings_json = request.form.get('manual_pairings', '[]')
                try:
                    import json
                    pairings_list = json.loads(manual_pairings_json)
                    if pairings_list:
                        manual_pairings = [(p[0], p[1]) for p in pairings_list]
                except (json.JSONDecodeError, IndexError, KeyError):
                    flash('Error parsing manual pairings. Using random pairing instead.', 'warning')

            tournament = TournamentService.create_tournament(
                game_id=game_id,
                pairing_type=form.pairing_type.data,
                bracket_style=form.bracket_style.data,
                public_edit=form.public_edit.data,
                manual_pairings=manual_pairings,
                included_team_ids=included_team_ids
            )
            flash('Tournament bracket created successfully!', 'success')
            return redirect(url_for('admin.view_tournament', game_id=game_id))
        except Exception as e:
            flash(f'Error creating tournament: {str(e)}', 'error')

    # Get teams from the same game night as the game
    if game.game_night_id:
        teams = Team.query.filter_by(game_night_id=game.game_night_id).all()
    else:
        # Fallback to active game night teams
        active_gn = GameNightService.get_active_game_night()
        if active_gn:
            teams = Team.query.filter_by(game_night_id=active_gn.id).all()
        else:
            teams = Team.query.all()
    return render_template('admin/setup_tournament.html', form=form, game=game, teams=teams)


@admin_bp.route('/tournament/view/<int:game_id>')
@login_required
def view_tournament(game_id):
    """View and manage tournament bracket."""
    game = GameService.get_game_by_id(game_id)
    tournament = TournamentService.get_tournament_by_game(game_id)

    if not tournament:
        flash('No tournament found for this game', 'error')
        return redirect(url_for('main.games'))

    bracket_data = TournamentService.get_bracket_structure(tournament.id)

    return render_template('admin/view_tournament.html',
                         game=game,
                         tournament=tournament,
                         bracket=bracket_data['bracket'],
                         rounds=bracket_data['rounds'])


@admin_bp.route('/tournament/match/<int:match_id>/score', methods=['POST'])
@login_required
def score_match(match_id):
    """Update match score and advance winner."""
    data = request.json

    try:
        TournamentService.update_match_result(
            match_id=match_id,
            team1_score=data.get('team1_score'),
            team2_score=data.get('team2_score'),
            winner_team_id=data.get('winner_team_id')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_bp.route('/tournament/finalize/<int:tournament_id>', methods=['POST'])
@login_required
def finalize_tournament(tournament_id):
    """Finalize tournament and mark game as complete."""
    try:
        from app.models import Tournament
        tournament = TournamentService.finalize_tournament(tournament_id)
        flash(f'Tournament finalized! Winner: {tournament.winner_team.name}. Scores added to leaderboard.', 'success')
        return redirect(url_for('main.index'))
    except ValueError as e:
        flash(str(e), 'error')
        tournament = Tournament.query.get_or_404(tournament_id)
        return redirect(url_for('admin.view_tournament', game_id=tournament.game_id))
    except Exception as e:
        flash(f'Error finalizing tournament: {str(e)}', 'error')
        return redirect(url_for('main.games'))


@admin_bp.route('/tournament/reset/<int:tournament_id>', methods=['POST'])
@login_required
def reset_tournament(tournament_id):
    """Reset tournament to initial state."""
    try:
        from app.models import Tournament
        TournamentService.reset_tournament(tournament_id)
        tournament = Tournament.query.get_or_404(tournament_id)
        flash('Tournament has been reset', 'success')
        return redirect(url_for('admin.view_tournament', game_id=tournament.game_id))
    except Exception as e:
        flash(f'Error resetting tournament: {str(e)}', 'error')
        return redirect(url_for('main.games'))


# ============================================================================
# GAME NIGHT MANAGEMENT
# ============================================================================

@admin_bp.route('/game-nights')
@login_required
def game_night_management():
    """Game night management dashboard."""
    game_nights = GameNightService.get_all_game_nights(order='desc')
    active_game_night = GameNightService.get_active_game_night()
    working_context = GameNightService.get_working_context_game_night()

    return render_template(
        'admin/game_night_management.html',
        game_nights=game_nights,
        active_game_night=active_game_night,
        working_context=working_context
    )


@admin_bp.route('/game-nights/create', methods=['GET', 'POST'])
@login_required
def create_game_night():
    """Create a new game night."""
    form = GameNightForm()

    if form.validate_on_submit():
        try:
            game_night = GameNightService.create_game_night(
                name=form.name.data,
                game_date=form.date.data
            )
            flash(f'Game Night "{game_night.name}" created successfully!', 'success')
            return redirect(url_for('admin.game_night_management'))
        except Exception as e:
            flash(f'Error creating game night: {str(e)}', 'error')

    return render_template('admin/create_game_night.html', form=form)


@admin_bp.route('/game-nights/<int:game_night_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_game_night(game_night_id):
    """Edit a game night."""
    game_night = GameNightService.get_game_night_by_id(game_night_id)

    # Cannot edit if completed
    if game_night.is_completed:
        flash('Cannot edit a completed game night.', 'error')
        return redirect(url_for('admin.game_night_management'))

    form = GameNightForm()

    if form.validate_on_submit():
        try:
            GameNightService.update_game_night(
                game_night_id,
                name=form.name.data,
                game_date=form.date.data
            )
            flash(f'Game Night "{form.name.data}" updated successfully!', 'success')
            return redirect(url_for('admin.game_night_management'))
        except Exception as e:
            flash(f'Error updating game night: {str(e)}', 'error')
    elif request.method == 'GET':
        # Populate form with existing data
        form.name.data = game_night.name
        form.date.data = game_night.date

    return render_template('admin/edit_game_night.html', form=form, game_night=game_night)


@admin_bp.route('/game-nights/<int:game_night_id>/set-working', methods=['POST'])
@login_required
def set_working_context(game_night_id):
    """Set a game night as the working context."""
    try:
        game_night = GameNightService.set_working_context(game_night_id)
        flash(f'Now working on "{game_night.name}". Teams and games will be added to this game night.', 'info')
    except Exception as e:
        flash(f'Error setting working context: {str(e)}', 'error')

    return redirect(url_for('admin.game_night_management'))


@admin_bp.route('/game-nights/<int:game_night_id>/activate', methods=['POST'])
@login_required
def activate_game_night(game_night_id):
    """Set a game night as active (visible to public)."""
    try:
        # All validation is now handled in the service layer
        game_night = GameNightService.set_active_game_night(game_night_id)
        flash(f'"{game_night.name}" is now ACTIVE and visible to all players on the public leaderboard!', 'success')
    except ValueError as e:
        # Validation errors from the service layer
        flash(str(e), 'warning')
    except Exception as e:
        # Other unexpected errors
        flash(f'Error activating game night: {str(e)}', 'error')

    return redirect(url_for('admin.game_night_management'))


@admin_bp.route('/game-nights/<int:game_night_id>/end', methods=['POST'])
@login_required
def end_game_night(game_night_id):
    """End/finalize a game night."""
    try:
        game_night = GameNightService.end_game_night(game_night_id)
        flash(f'Game Night "{game_night.name}" has been ended and finalized!', 'success')
    except Exception as e:
        flash(f'Error ending game night: {str(e)}', 'error')

    return redirect(url_for('admin.game_night_management'))


@admin_bp.route('/game-nights/<int:game_night_id>/wipe', methods=['POST'])
@login_required
def wipe_game_night(game_night_id):
    """Wipe data from a game night."""
    try:
        game_night = GameNightService.wipe_game_night_data(game_night_id)
        flash(f'All data cleared from "{game_night.name}"!', 'success')
    except Exception as e:
        flash(f'Error wiping game night: {str(e)}', 'error')

    return redirect(url_for('admin.game_night_management'))


@admin_bp.route('/game-nights/<int:game_night_id>/delete', methods=['POST'])
@login_required
def delete_game_night(game_night_id):
    """Delete a game night permanently."""
    try:
        game_night = GameNightService.get_game_night_by_id(game_night_id)
        game_night_name = game_night.name

        GameNightService.delete_game_night(game_night_id)
        flash(f'Game Night "{game_night_name}" has been deleted!', 'success')
    except Exception as e:
        flash(f'Error deleting game night: {str(e)}', 'error')

    return redirect(url_for('admin.game_night_management'))


# ============================================================================
# TIMER MANAGEMENT
# ============================================================================

@admin_bp.route('/timer/<int:timer_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_timer_record(timer_id):
    """Delete a specific timer record and recalculate averages."""
    try:
        from app.models.timer_record import TimerRecord
        from app.websockets import timer_aggregator

        # Get the timer record
        timer_record = TimerRecord.query.get_or_404(timer_id)
        game_id = timer_record.game_id
        team_id = timer_record.team_id

        # Delete the timer record
        db.session.delete(timer_record)
        db.session.commit()

        # Recalculate the average for this team
        timer_aggregator.calculate_average(game_id, team_id)

        logger.info(f'Admin {current_user.username} deleted timer record {timer_id} for game {game_id}, team {team_id}')

        return jsonify({
            'success': True,
            'message': 'Timer record deleted successfully',
            'game_id': game_id,
            'team_id': team_id
        })
    except Exception as e:
        logger.error(f'Error deleting timer record {timer_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500