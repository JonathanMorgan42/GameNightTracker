"""Unit tests for TimerAggregator."""
import pytest
from datetime import date
from app import create_app, db
from app.websockets.timer_aggregator import TimerAggregator
from app.models.timer_record import TimerRecord
from app.models.score import Score
from app.models.game import Game
from app.models.team import Team
from app.models.game_night import GameNight


@pytest.fixture
def app():
    """Create test app."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        # Clean up session and data before dropping tables
        db.session.rollback()
        db.session.close()
        db.session.remove()
        # Clear all data to avoid FK constraint issues
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        db.drop_all()


@pytest.fixture
def aggregator():
    """Create TimerAggregator instance."""
    return TimerAggregator()


@pytest.fixture
def sample_data(app):
    """Create sample game and team data."""
    with app.app_context():
        gn = GameNight(name='Test Night', date=date.today(), is_active=True)
        db.session.add(gn)
        db.session.flush()

        team = Team(name='Team 1', game_night_id=gn.id)
        db.session.add(team)
        db.session.flush()

        game = Game(name='Test Game', game_night_id=gn.id, metric_type='time')
        db.session.add(game)
        db.session.commit()

        return {'game_id': game.id, 'team_id': team.id}


class TestTimerAggregator:
    """Test suite for TimerAggregator."""

    def test_start_timer(self, aggregator):
        """Test starting a timer."""
        aggregator.start_timer(1, 1, 'user1', 'User One')

        active = aggregator.get_active_timers_for_game(1)
        assert len(active) == 1
        assert active[0]['user_id'] == 'user1'
        assert active[0]['team_id'] == 1

    def test_record_time(self, app, aggregator, sample_data):
        """Test recording a timer value."""
        with app.app_context():
            aggregator.start_timer(
                sample_data['game_id'],
                sample_data['team_id'],
                'user1',
                'User One'
            )

            record = aggregator.record_time(
                sample_data['game_id'],
                sample_data['team_id'],
                'user1',
                'User One',
                12.5
            )

            assert record.time_value == 12.5
            assert record.is_active is True

            # Timer should be removed from active
            active = aggregator.get_active_timers_for_game(sample_data['game_id'])
            assert len(active) == 0

    def test_get_team_timers(self, app, aggregator, sample_data):
        """Test retrieving all timers for a team."""
        with app.app_context():
            aggregator.record_time(
                sample_data['game_id'],
                sample_data['team_id'],
                'user1', 'User One', 10.0
            )
            aggregator.record_time(
                sample_data['game_id'],
                sample_data['team_id'],
                'user2', 'User Two', 12.0
            )

            timer_data = aggregator.get_team_timers(
                sample_data['game_id'],
                sample_data['team_id']
            )

            assert len(timer_data['times']) == 2
            assert 10.0 in timer_data['times']
            assert 12.0 in timer_data['times']
            assert len(timer_data['timers']) == 2

    def test_clear_team_timers(self, app, aggregator, sample_data):
        """Test clearing timers for a team."""
        with app.app_context():
            aggregator.record_time(
                sample_data['game_id'],
                sample_data['team_id'],
                'user1', 'User One', 10.0
            )
            aggregator.record_time(
                sample_data['game_id'],
                sample_data['team_id'],
                'user2', 'User Two', 12.0
            )

            count = aggregator.clear_team_timers(
                sample_data['game_id'],
                sample_data['team_id']
            )

            assert count == 2

            timer_data = aggregator.get_team_timers(
                sample_data['game_id'],
                sample_data['team_id']
            )
            assert len(timer_data['times']) == 0

    def test_calculate_average(self, app, aggregator, sample_data):
        """Test average calculation and score update."""
        with app.app_context():
            aggregator.record_time(
                sample_data['game_id'],
                sample_data['team_id'],
                'user1', 'User One', 10.0
            )
            aggregator.record_time(
                sample_data['game_id'],
                sample_data['team_id'],
                'user2', 'User Two', 12.0
            )
            aggregator.record_time(
                sample_data['game_id'],
                sample_data['team_id'],
                'user3', 'User Three', 11.0
            )

            avg = aggregator.calculate_average(
                sample_data['game_id'],
                sample_data['team_id']
            )

            assert avg == 11.0

            # Check score was updated
            score = Score.query.filter_by(
                game_id=sample_data['game_id'],
                team_id=sample_data['team_id']
            ).first()

            assert score is not None
            assert score.multi_timer_avg == 11.0
            assert score.timer_count == 3
            assert score.score_value == 11.0

    def test_stop_user_timers(self, aggregator):
        """Test stopping all timers for a user."""
        aggregator.start_timer(1, 1, 'user1', 'User One')
        aggregator.start_timer(1, 2, 'user1', 'User One')
        aggregator.start_timer(2, 1, 'user1', 'User One')

        stopped = aggregator.stop_user_timers('user1')

        assert len(stopped) == 3
        active = aggregator.get_active_timers_for_game(1)
        assert len(active) == 0

    def test_multiple_games_independent(self, aggregator):
        """Test that timers for different games are independent."""
        aggregator.start_timer(1, 1, 'user1', 'User One')
        aggregator.start_timer(2, 1, 'user2', 'User Two')

        active_game1 = aggregator.get_active_timers_for_game(1)
        active_game2 = aggregator.get_active_timers_for_game(2)

        assert len(active_game1) == 1
        assert len(active_game2) == 1
        assert active_game1[0]['user_id'] == 'user1'
        assert active_game2[0]['user_id'] == 'user2'
