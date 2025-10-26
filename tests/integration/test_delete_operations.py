"""Integration tests for delete operations."""
import pytest
from app.models import Team, Game, GameNight, Participant, Score, Tournament, Match


class TestDeleteTeam:
    """Test team deletion through the API."""

    def test_delete_team_success(self, authenticated_client, db_session, teams, participants):
        """Test successful team deletion."""
        team = teams[0]
        team_id = team.id

        # Verify team exists
        assert Team.query.get(team_id) is not None

        # Delete team
        response = authenticated_client.post(f'/admin/teams/delete/{team_id}')

        assert response.status_code == 302  # Redirect after delete
        assert Team.query.get(team_id) is None

    def test_delete_team_with_scores(self, authenticated_client, db_session, teams, game, participants):
        """Test deleting team with associated scores."""
        team = teams[0]
        team_id = team.id

        # Add score
        score = Score(game_id=game.id, team_id=team_id, score_value=100, points=3)
        db_session.add(score)
        db_session.commit()

        # Delete team
        response = authenticated_client.post(f'/admin/teams/delete/{team_id}')

        assert response.status_code == 302
        # Verify team and scores are deleted
        assert Team.query.get(team_id) is None
        assert Score.query.filter_by(team_id=team_id).first() is None

    def test_delete_team_requires_auth(self, client, db_session, teams):
        """Test that delete requires authentication."""
        response = client.post(f'/admin/teams/delete/{teams[0].id}')
        assert response.status_code == 302
        # Team should still exist
        assert Team.query.get(teams[0].id) is not None

    def test_delete_nonexistent_team(self, authenticated_client, db_session):
        """Test deleting non-existent team."""
        response = authenticated_client.post('/admin/teams/delete/99999')
        assert response.status_code in [404, 302]


class TestDeleteGame:
    """Test game deletion through the API."""

    def test_delete_game_success(self, authenticated_client, db_session, game):
        """Test successful game deletion."""
        game_id = game.id

        # Verify game exists
        assert Game.query.get(game_id) is not None

        # Delete game
        response = authenticated_client.post(f'/admin/games/delete/{game_id}')

        assert response.status_code == 302
        assert Game.query.get(game_id) is None

    def test_delete_game_with_scores(self, authenticated_client, db_session, game, teams):
        """Test deleting game with scores."""
        game_id = game.id

        # Add scores
        score1 = Score(game_id=game_id, team_id=teams[0].id, score_value=100, points=3)
        score2 = Score(game_id=game_id, team_id=teams[1].id, score_value=90, points=2)
        db_session.add_all([score1, score2])
        db_session.commit()

        # Delete game
        response = authenticated_client.post(f'/admin/games/delete/{game_id}')

        assert response.status_code == 302
        # Verify game and scores are deleted
        assert Game.query.get(game_id) is None
        assert Score.query.filter_by(game_id=game_id).count() == 0

    def test_delete_game_with_tournament(self, authenticated_client, db_session, game, teams):
        """Test deleting game with tournament cascades correctly."""
        game_id = game.id

        # Create tournament
        tournament = Tournament(
            game_id=game_id,
            pairing_type='random',
            bracket_style='standard',
            public_edit=False
        )
        db_session.add(tournament)
        db_session.commit()

        # Create match
        match = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=1,
            team1_id=teams[0].id,
            team2_id=teams[1].id
        )
        db_session.add(match)
        db_session.commit()

        tournament_id = tournament.id
        match_id = match.id

        # Delete game
        response = authenticated_client.post(f'/admin/games/delete/{game_id}')

        assert response.status_code == 302
        # Verify game, tournament, and matches are deleted
        assert Game.query.get(game_id) is None
        assert Tournament.query.get(tournament_id) is None
        assert Match.query.get(match_id) is None

    def test_delete_game_requires_auth(self, client, db_session, game):
        """Test that delete requires authentication."""
        response = client.post(f'/admin/games/delete/{game.id}')
        assert response.status_code == 302
        # Game should still exist
        assert Game.query.get(game.id) is not None

    def test_delete_nonexistent_game(self, authenticated_client, db_session):
        """Test deleting non-existent game."""
        response = authenticated_client.post('/admin/games/delete/99999')
        assert response.status_code in [404, 302]


class TestDeleteGameNight:
    """Test game night deletion through the API."""

    def test_delete_game_night_success(self, authenticated_client, db_session):
        """Test successful game night deletion."""
        from datetime import date
        game_night = GameNight(name='To Delete', date=date.today())
        db_session.add(game_night)
        db_session.commit()

        game_night_id = game_night.id

        # Delete game night
        response = authenticated_client.post(f'/admin/game-nights/{game_night_id}/delete')

        assert response.status_code == 302
        assert GameNight.query.get(game_night_id) is None

    def test_delete_game_night_with_teams_and_games(self, authenticated_client, db_session, game_night, teams, game):
        """Test deleting game night cascades to teams and games."""
        game_night_id = game_night.id

        # Verify related data exists
        assert len(Team.query.filter_by(game_night_id=game_night_id).all()) > 0
        assert len(Game.query.filter_by(game_night_id=game_night_id).all()) > 0

        # Delete game night
        response = authenticated_client.post(f'/admin/game-nights/{game_night_id}/delete')

        assert response.status_code == 302
        # Verify game night and related data are deleted
        assert GameNight.query.get(game_night_id) is None
        assert len(Team.query.filter_by(game_night_id=game_night_id).all()) == 0
        assert len(Game.query.filter_by(game_night_id=game_night_id).all()) == 0

    def test_delete_active_game_night(self, authenticated_client, db_session, game_night):
        """Test deleting an active game night."""
        game_night.is_active = True
        db_session.commit()

        game_night_id = game_night.id

        # Delete game night
        response = authenticated_client.post(f'/admin/game-nights/{game_night_id}/delete')

        assert response.status_code == 302
        assert GameNight.query.get(game_night_id) is None

    def test_delete_completed_game_night(self, authenticated_client, db_session, game_night):
        """Test deleting a completed game night."""
        game_night.is_completed = True
        db_session.commit()

        game_night_id = game_night.id

        # Delete game night
        response = authenticated_client.post(f'/admin/game-nights/{game_night_id}/delete')

        assert response.status_code == 302
        assert GameNight.query.get(game_night_id) is None

    def test_delete_game_night_requires_auth(self, client, db_session, game_night):
        """Test that delete requires authentication."""
        response = client.post(f'/admin/game-nights/{game_night.id}/delete')
        assert response.status_code == 302
        # Game night should still exist
        assert GameNight.query.get(game_night.id) is not None

    def test_delete_nonexistent_game_night(self, authenticated_client, db_session):
        """Test deleting non-existent game night."""
        response = authenticated_client.post('/admin/game-nights/99999/delete')
        assert response.status_code in [404, 302]


class TestCascadeDelete:
    """Test that deletes properly cascade through relationships."""

    def test_delete_team_cascades_to_participants(self, authenticated_client, db_session, teams, participants):
        """Test that deleting team deletes all participants."""
        team = teams[0]
        team_id = team.id

        # Count participants
        participant_count = Participant.query.filter_by(team_id=team_id).count()
        assert participant_count > 0

        # Delete team
        authenticated_client.post(f'/admin/teams/delete/{team_id}')

        # Verify participants are deleted
        assert Participant.query.filter_by(team_id=team_id).count() == 0

    def test_delete_game_cascades_to_tournament_and_matches(self, authenticated_client, db_session, game, teams):
        """Test complete cascade from game to tournament to matches."""
        game_id = game.id

        # Create tournament with multiple matches
        tournament = Tournament(game_id=game_id, pairing_type='random')
        db_session.add(tournament)
        db_session.commit()

        matches = []
        for i in range(3):
            match = Match(
                tournament_id=tournament.id,
                round_number=1,
                position_in_round=i,
                team1_id=teams[0].id if i % 2 == 0 else teams[1].id,
                team2_id=teams[1].id if i % 2 == 0 else teams[2].id
            )
            matches.append(match)
            db_session.add(match)
        db_session.commit()

        match_ids = [m.id for m in matches]

        # Delete game
        authenticated_client.post(f'/admin/games/delete/{game_id}')

        # Verify all matches are deleted
        for match_id in match_ids:
            assert Match.query.get(match_id) is None

    def test_delete_game_night_full_cascade(self, authenticated_client, db_session, game_night, teams, participants, game):
        """Test complete cascade deletion from game night."""
        game_night_id = game_night.id

        # Add scores
        score = Score(game_id=game.id, team_id=teams[0].id, score_value=100, points=3)
        db_session.add(score)
        db_session.commit()

        team_ids = [t.id for t in teams]
        participant_ids = [p.id for p in participants]
        game_id = game.id

        # Delete game night
        authenticated_client.post(f'/admin/game-nights/{game_night_id}/delete')

        # Verify everything is deleted
        assert GameNight.query.get(game_night_id) is None
        for team_id in team_ids:
            assert Team.query.get(team_id) is None
        for participant_id in participant_ids:
            assert Participant.query.get(participant_id) is None
        assert Game.query.get(game_id) is None
