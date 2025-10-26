"""Unit tests for TeamService."""
import pytest
from app.services.team_service import TeamService
from app.models import Team, Participant, Score, Game


class TestTeamService:
    """Test team service operations."""

    def test_get_all_teams(self, db_session, teams):
        """Test getting all teams."""
        result = TeamService.get_all_teams(sort_by_points=False)
        assert len(result) == 3
        assert all(isinstance(team, Team) for team in result)

    def test_get_all_teams_sorted_by_points(self, db_session, teams, game):
        """Test getting teams sorted by points."""
        from app.models import Score

        # Add points to teams via scores
        score1 = Score(game_id=game.id, team_id=teams[0].id, points=30)
        score2 = Score(game_id=game.id, team_id=teams[1].id, points=50)
        score3 = Score(game_id=game.id, team_id=teams[2].id, points=10)
        db_session.add_all([score1, score2, score3])
        db_session.commit()

        result = TeamService.get_all_teams(sort_by_points=True)
        assert result[0].totalPoints == 50
        assert result[1].totalPoints == 30
        assert result[2].totalPoints == 10

    def test_get_team_by_id(self, db_session, teams):
        """Test getting team by ID."""
        team = TeamService.get_team_by_id(teams[0].id)
        assert team.id == teams[0].id
        assert team.name == teams[0].name

    def test_get_team_by_id_not_found(self, db_session):
        """Test getting non-existent team raises 404."""
        with pytest.raises(Exception):
            TeamService.get_team_by_id(99999)

    def test_create_team(self, db_session, game_night):
        """Test creating a new team."""
        participants_data = [
            {'firstName': 'John', 'lastName': 'Doe'},
            {'firstName': 'Jane', 'lastName': 'Smith'}
        ]

        team = TeamService.create_team(
            name='New Team',
            participants_data=participants_data,
            color='#FF5733',
            game_night_id=game_night.id
        )

        assert team.id is not None
        assert team.name == 'New Team'
        assert team.color == '#FF5733'
        assert team.game_night_id == game_night.id

        # Verify participants were created
        participants = list(team.participants)
        assert len(participants) == 2
        assert participants[0].firstName == 'John'
        assert participants[1].firstName == 'Jane'

    def test_create_team_with_active_game_night(self, db_session, game_night):
        """Test creating team without specifying game_night_id uses active."""
        participants_data = [
            {'firstName': 'Alice', 'lastName': 'Wonder'},
            {'firstName': 'Bob', 'lastName': 'Builder'}
        ]

        team = TeamService.create_team(
            name='Auto Team',
            participants_data=participants_data
        )

        # Should auto-associate with active game night
        assert team.game_night_id == game_night.id

    def test_update_team(self, db_session, teams, participants):
        """Test updating team details."""
        team = teams[0]
        new_participants_data = [
            {'firstName': 'Updated', 'lastName': 'Player1'},
            {'firstName': 'Updated', 'lastName': 'Player2'}
        ]

        updated_team = TeamService.update_team(
            team_id=team.id,
            name='Updated Name',
            participants_data=new_participants_data,
            color='#ABCDEF'
        )

        assert updated_team.name == 'Updated Name'
        assert updated_team.color == '#ABCDEF'

        # Verify participants were updated
        participants = list(updated_team.participants)
        assert participants[0].firstName == 'Updated'
        assert participants[1].firstName == 'Updated'

    def test_delete_team(self, db_session, teams, participants):
        """Test deleting a team."""
        team = teams[0]
        team_id = team.id

        # Create a game and score for this team
        game = Game(
            name='Test Game',
            type='standard',
            game_night_id=team.game_night_id,
            sequence_number=1,
            point_scheme=1,
            metric_type='score',
            scoring_direction='higher_better'
        )
        db_session.add(game)
        db_session.commit()

        score = Score(
            game_id=game.id,
            team_id=team_id,
            score_value=100,
            points=3
        )
        db_session.add(score)
        db_session.commit()

        # Verify team, participants, and scores exist
        assert Team.query.get(team_id) is not None
        assert len(Participant.query.filter_by(team_id=team_id).all()) > 0
        assert len(Score.query.filter_by(team_id=team_id).all()) == 1

        # Delete the team
        TeamService.delete_team(team_id)

        # Verify team, participants, and scores are deleted
        assert Team.query.get(team_id) is None
        assert len(Participant.query.filter_by(team_id=team_id).all()) == 0
        assert len(Score.query.filter_by(team_id=team_id).all()) == 0

    def test_delete_team_not_found(self, db_session):
        """Test deleting non-existent team raises 404."""
        with pytest.raises(Exception):
            TeamService.delete_team(99999)

    def test_delete_team_cascade(self, db_session, teams, participants):
        """Test that deleting a team cascades to all related data."""
        team = teams[0]
        team_id = team.id

        # Get count of participants before deletion
        participant_count = len(Participant.query.filter_by(team_id=team_id).all())
        assert participant_count > 0

        # Delete team
        TeamService.delete_team(team_id)

        # Verify all participants are deleted
        assert len(Participant.query.filter_by(team_id=team_id).all()) == 0
