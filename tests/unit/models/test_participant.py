"""Unit tests for Participant model."""
import pytest
from app.models import Participant, Team


@pytest.mark.unit
@pytest.mark.models
class TestParticipantModel:
    """Test suite for Participant model."""

    def test_create_participant(self, db_session, teams):
        """Test creating a participant."""
        team = teams[0]
        participant = Participant(
            firstName='John',
            lastName='Doe',
            team_id=team.id
        )

        db_session.add(participant)
        db_session.commit()

        assert participant.id is not None
        assert participant.firstName == 'John'
        assert participant.lastName == 'Doe'
        assert participant.team_id == team.id

    def test_get_full_name(self, db_session, teams):
        """Test getting full name."""
        team = teams[0]
        participant = Participant(
            firstName='Jane',
            lastName='Smith',
            team_id=team.id
        )

        db_session.add(participant)
        db_session.commit()

        assert participant.getFullName() == 'Jane Smith'

    def test_get_full_name_no_last_name(self, db_session, teams):
        """Test getting full name when lastName is None."""
        team = teams[0]
        participant = Participant(
            firstName='Bob',
            lastName=None,
            team_id=team.id
        )

        db_session.add(participant)
        db_session.commit()

        full_name = participant.getFullName()
        assert 'Bob' in full_name

    def test_team_relationship(self, db_session, teams):
        """Test relationship with team."""
        team = teams[0]
        participant = Participant(
            firstName='Alice',
            lastName='Johnson',
            team_id=team.id
        )

        db_session.add(participant)
        db_session.commit()

        # Test bidirectional relationship
        assert participant.team == team
        assert participant in team.participants

    def test_first_name_required(self, db_session, teams):
        """Test that firstName is required."""
        participant = Participant(
            lastName='Doe',
            team_id=teams[0].id
        )

        db_session.add(participant)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_team_id_required(self, db_session):
        """Test that team_id is required."""
        participant = Participant(
            firstName='John',
            lastName='Doe'
        )

        db_session.add(participant)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_cascade_delete_with_team(self, db_session, game_night):
        """Test that participants are deleted when team is deleted."""
        team = Team(name='Temp Team', color='#FFFFFF', game_night_id=game_night.id)
        db_session.add(team)
        db_session.commit()

        participant = Participant(
            firstName='Test',
            lastName='User',
            team_id=team.id
        )
        db_session.add(participant)
        db_session.commit()

        participant_id = participant.id

        # Delete team
        db_session.delete(team)
        db_session.commit()

        # Participant should be deleted
        assert db_session.query(Participant).filter_by(id=participant_id).first() is None
