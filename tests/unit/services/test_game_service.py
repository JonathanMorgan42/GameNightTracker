"""Unit tests for GameService."""
import pytest
from app.services.game_service import GameService
from app.models import Game, Score, Penalty, Tournament, Match, Team


class TestGameService:
    """Test game service operations."""

    def test_get_all_games(self, db_session, game):
        """Test getting all games."""
        result = GameService.get_all_games(ordered=False)
        assert len(result) >= 1
        assert any(g.id == game.id for g in result)

    def test_get_all_games_ordered(self, db_session, game_night):
        """Test getting games ordered by sequence."""
        # Create multiple games with different sequences
        game1 = Game(name='Game 1', type='standard', sequence_number=3,
                    game_night_id=game_night.id, point_scheme=1,
                    metric_type='score', scoring_direction='higher_better')
        game2 = Game(name='Game 2', type='standard', sequence_number=1,
                    game_night_id=game_night.id, point_scheme=1,
                    metric_type='score', scoring_direction='higher_better')
        game3 = Game(name='Game 3', type='standard', sequence_number=2,
                    game_night_id=game_night.id, point_scheme=1,
                    metric_type='score', scoring_direction='higher_better')
        db_session.add_all([game1, game2, game3])
        db_session.commit()

        result = GameService.get_all_games(ordered=True)
        sequences = [g.sequence_number for g in result]
        assert sequences == sorted(sequences)

    def test_get_game_by_id(self, db_session, game):
        """Test getting game by ID."""
        result = GameService.get_game_by_id(game.id)
        assert result.id == game.id
        assert result.name == game.name

    def test_get_game_by_id_not_found(self, db_session):
        """Test getting non-existent game raises 404."""
        with pytest.raises(Exception):
            GameService.get_game_by_id(99999)

    def test_create_game(self, db_session, game_night):
        """Test creating a new game."""
        form_data = {
            'name': 'New Game',
            'type': 'standard',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }

        game = GameService.create_game(form_data, game_night_id=game_night.id)

        assert game.id is not None
        assert game.name == 'New Game'
        assert game.type == 'standard'
        assert game.sequence_number == 1
        assert game.game_night_id == game_night.id

    def test_create_game_with_penalties(self, db_session, game_night):
        """Test creating game with penalties."""
        form_data = {
            'name': 'Game with Penalties',
            'type': 'standard',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'time',
            'scoring_direction': 'lower_better',
            'public_input': False
        }

        penalties_data = [
            {'name': 'Penalty 1', 'value': 10, 'stackable': True},
            {'name': 'Penalty 2', 'value': 5, 'stackable': False}
        ]

        game = GameService.create_game(form_data, penalties_data, game_night_id=game_night.id)

        penalties = game.penalties.all()
        assert len(penalties) == 2
        assert penalties[0].name == 'Penalty 1'
        assert penalties[0].value == 10
        assert penalties[0].stackable is True

    def test_create_game_shifts_existing_sequences(self, db_session, game_night):
        """Test that creating a game shifts existing game sequences."""
        # Create initial games
        game1 = Game(name='Game 1', type='standard', sequence_number=1,
                    game_night_id=game_night.id, point_scheme=1,
                    metric_type='score', scoring_direction='higher_better')
        game2 = Game(name='Game 2', type='standard', sequence_number=2,
                    game_night_id=game_night.id, point_scheme=1,
                    metric_type='score', scoring_direction='higher_better')
        db_session.add_all([game1, game2])
        db_session.commit()

        # Insert new game at position 2
        form_data = {
            'name': 'Inserted Game',
            'type': 'standard',
            'sequence_number': 2,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }

        new_game = GameService.create_game(form_data, game_night_id=game_night.id)

        # Refresh games
        db_session.refresh(game1)
        db_session.refresh(game2)

        # Original game1 should still be at 1
        assert game1.sequence_number == 1
        # New game should be at 2
        assert new_game.sequence_number == 2
        # Original game2 should be shifted to 3
        assert game2.sequence_number == 3

    def test_update_game(self, db_session, game):
        """Test updating game."""
        form_data = {
            'name': 'Updated Game',
            'type': 'tournament',
            'sequence_number': game.sequence_number,
            'point_scheme': 2,
            'metric_type': 'time',
            'scoring_direction': 'lower_better',
            'public_input': True
        }

        updated_game = GameService.update_game(game.id, form_data)

        assert updated_game.name == 'Updated Game'
        assert updated_game.type == 'tournament'
        assert updated_game.point_scheme == 2
        assert updated_game.public_input is True

    def test_update_game_sequence_reordering(self, db_session, game_night):
        """Test that updating game sequence reorders other games."""
        # Create games with sequence 1, 2, 3
        game1 = Game(name='Game 1', type='standard', sequence_number=1,
                    game_night_id=game_night.id, point_scheme=1,
                    metric_type='score', scoring_direction='higher_better')
        game2 = Game(name='Game 2', type='standard', sequence_number=2,
                    game_night_id=game_night.id, point_scheme=1,
                    metric_type='score', scoring_direction='higher_better')
        game3 = Game(name='Game 3', type='standard', sequence_number=3,
                    game_night_id=game_night.id, point_scheme=1,
                    metric_type='score', scoring_direction='higher_better')
        db_session.add_all([game1, game2, game3])
        db_session.commit()

        # Move game3 to position 1 (should shift others down)
        form_data = {
            'name': 'Game 3',
            'type': 'standard',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }

        GameService.update_game(game3.id, form_data)

        # Refresh all games
        db_session.refresh(game1)
        db_session.refresh(game2)
        db_session.refresh(game3)

        # Verify reordering
        assert game3.sequence_number == 1
        assert game1.sequence_number == 2
        assert game2.sequence_number == 3

    def test_delete_game(self, db_session, game, teams):
        """Test deleting a game."""
        game_id = game.id

        # Add a score
        score = Score(game_id=game_id, team_id=teams[0].id, score_value=100, points=3)
        db_session.add(score)
        db_session.commit()

        # Add a penalty
        penalty = Penalty(game_id=game_id, name='Test Penalty', value=10)
        db_session.add(penalty)
        db_session.commit()

        # Verify game and related data exist
        assert Game.query.get(game_id) is not None
        assert len(Score.query.filter_by(game_id=game_id).all()) == 1
        assert len(Penalty.query.filter_by(game_id=game_id).all()) == 1

        # Delete game
        GameService.delete_game(game_id)

        # Verify game and related data are deleted
        assert Game.query.get(game_id) is None
        assert len(Score.query.filter_by(game_id=game_id).all()) == 0
        assert len(Penalty.query.filter_by(game_id=game_id).all()) == 0

    def test_delete_game_with_tournament(self, db_session, game, teams):
        """Test deleting a game with tournament cascades properly."""
        game_id = game.id

        # Create a tournament for this game
        tournament = Tournament(
            game_id=game_id,
            pairing_type='random',
            bracket_style='standard',
            public_edit=False
        )
        db_session.add(tournament)
        db_session.commit()

        # Create matches
        match = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=1,
            team1_id=teams[0].id,
            team2_id=teams[1].id
        )
        db_session.add(match)
        db_session.commit()

        # Verify tournament and matches exist
        assert Tournament.query.filter_by(game_id=game_id).first() is not None
        assert len(Match.query.filter_by(tournament_id=tournament.id).all()) == 1

        # Delete game
        GameService.delete_game(game_id)

        # Verify game, tournament, and matches are deleted
        assert Game.query.get(game_id) is None
        assert Tournament.query.filter_by(game_id=game_id).first() is None
        # Matches should be cascade deleted with tournament
        assert len(Match.query.filter_by(tournament_id=tournament.id).all()) == 0

    def test_delete_game_not_found(self, db_session):
        """Test deleting non-existent game raises 404."""
        with pytest.raises(Exception):
            GameService.delete_game(99999)

    def test_get_completed_games(self, db_session, game_night):
        """Test getting only completed games."""
        game1 = Game(name='Completed 1', type='standard', sequence_number=1,
                    game_night_id=game_night.id, isCompleted=True,
                    point_scheme=1, metric_type='score', scoring_direction='higher_better')
        game2 = Game(name='Not Completed', type='standard', sequence_number=2,
                    game_night_id=game_night.id, isCompleted=False,
                    point_scheme=1, metric_type='score', scoring_direction='higher_better')
        game3 = Game(name='Completed 2', type='standard', sequence_number=3,
                    game_night_id=game_night.id, isCompleted=True,
                    point_scheme=1, metric_type='score', scoring_direction='higher_better')
        db_session.add_all([game1, game2, game3])
        db_session.commit()

        completed = GameService.get_completed_games()
        assert len(completed) == 2
        assert all(g.isCompleted for g in completed)

    def test_get_upcoming_games(self, db_session, game_night):
        """Test getting only upcoming games."""
        game1 = Game(name='Completed', type='standard', sequence_number=1,
                    game_night_id=game_night.id, isCompleted=True,
                    point_scheme=1, metric_type='score', scoring_direction='higher_better')
        game2 = Game(name='Upcoming 1', type='standard', sequence_number=2,
                    game_night_id=game_night.id, isCompleted=False,
                    point_scheme=1, metric_type='score', scoring_direction='higher_better')
        game3 = Game(name='Upcoming 2', type='standard', sequence_number=3,
                    game_night_id=game_night.id, isCompleted=False,
                    point_scheme=1, metric_type='score', scoring_direction='higher_better')
        db_session.add_all([game1, game2, game3])
        db_session.commit()

        upcoming = GameService.get_upcoming_games()
        assert len(upcoming) == 2
        assert all(not g.isCompleted for g in upcoming)
