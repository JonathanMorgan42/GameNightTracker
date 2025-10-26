"""Test data factories for creating test fixtures."""
from datetime import date
from app.models import GameNight, Team, Game, Participant, Score, Admin, Tournament, Match, Penalty


class GameNightFactory:
    """Factory for creating GameNight instances."""

    @staticmethod
    def create(db_session, name='Test Game Night', game_date=None,
               is_active=True, is_working_context=True, is_completed=False):
        """Create a game night with default values.

        Args:
            db_session: Database session
            name: Game night name
            game_date: Date of game night (defaults to today)
            is_active: Whether game night is active
            is_working_context: Whether this is the working context
            is_completed: Whether game night is completed

        Returns:
            GameNight instance
        """
        if game_date is None:
            game_date = date.today()

        gn = GameNight(
            name=name,
            date=game_date,
            is_active=is_active,
            is_working_context=is_working_context,
            is_completed=is_completed
        )
        db_session.add(gn)
        db_session.commit()
        return gn


class TeamFactory:
    """Factory for creating Team instances."""

    @staticmethod
    def create(db_session, name='Test Team', game_night_id=None,
               color='#3b82f6', participant_count=2):
        """Create a team with participants.

        Args:
            db_session: Database session
            name: Team name
            game_night_id: ID of associated game night
            color: Team color (hex code)
            participant_count: Number of participants (0-6)

        Returns:
            Team instance
        """
        team = Team(name=name, color=color, game_night_id=game_night_id)
        db_session.add(team)
        db_session.flush()

        for i in range(participant_count):
            participant = Participant(
                firstName=f'Player{i+1}',
                lastName='Doe',
                team_id=team.id
            )
            db_session.add(participant)

        db_session.commit()
        return team

    @staticmethod
    def create_batch(db_session, count=3, game_night_id=None, **kwargs):
        """Create multiple teams at once.

        Args:
            db_session: Database session
            count: Number of teams to create
            game_night_id: ID of associated game night
            **kwargs: Additional arguments passed to create()

        Returns:
            List of Team instances
        """
        teams = []
        for i in range(1, count + 1):
            team = TeamFactory.create(
                db_session,
                name=f'Team {i}',
                game_night_id=game_night_id,
                **kwargs
            )
            teams.append(team)
        return teams


class GameFactory:
    """Factory for creating Game instances."""

    @staticmethod
    def create(db_session, name='Test Game', game_night_id=None,
               sequence_number=1, point_scheme=1, metric_type='score',
               scoring_direction='higher_better', is_completed=False,
               public_input=False, game_type='standard'):
        """Create a game with default values.

        Args:
            db_session: Database session
            name: Game name
            game_night_id: ID of associated game night
            sequence_number: Order in which game is played
            point_scheme: Point multiplier (1-100)
            metric_type: 'score' or 'time'
            scoring_direction: 'higher_better' or 'lower_better'
            is_completed: Whether game is completed
            public_input: Whether public can score this game
            game_type: Type of game

        Returns:
            Game instance
        """
        game = Game(
            name=name,
            type=game_type,
            game_night_id=game_night_id,
            sequence_number=sequence_number,
            point_scheme=point_scheme,
            metric_type=metric_type,
            scoring_direction=scoring_direction,
            isCompleted=is_completed,
            public_input=public_input
        )
        db_session.add(game)
        db_session.commit()
        return game


class ScoreFactory:
    """Factory for creating Score instances."""

    @staticmethod
    def create(db_session, game_id, team_id, points=0, score_value=None, notes=None):
        """Create a score entry.

        Args:
            db_session: Database session
            game_id: ID of game
            team_id: ID of team
            points: Points awarded
            score_value: Raw score value
            notes: Optional notes

        Returns:
            Score instance
        """
        score = Score(
            game_id=game_id,
            team_id=team_id,
            points=points,
            score_value=score_value,
            notes=notes
        )
        db_session.add(score)
        db_session.commit()
        return score


class AdminFactory:
    """Factory for creating Admin users."""

    @staticmethod
    def create(db_session, username='testadmin', password='testpassword123'):
        """Create an admin user.

        Args:
            db_session: Database session
            username: Admin username
            password: Admin password

        Returns:
            Admin instance
        """
        admin = Admin(username=username)
        admin.setPassword(password)
        db_session.add(admin)
        db_session.commit()
        return admin


class TournamentFactory:
    """Factory for creating Tournament instances."""

    @staticmethod
    def create(db_session, game_id, pairing_type='random',
               bracket_style='standard', public_edit=False):
        """Create a tournament.

        Args:
            db_session: Database session
            game_id: ID of associated game
            pairing_type: 'random' or 'manual'
            bracket_style: 'standard' or 'play_in'
            public_edit: Whether public can edit tournament

        Returns:
            Tournament instance
        """
        tournament = Tournament(
            game_id=game_id,
            pairing_type=pairing_type,
            bracket_style=bracket_style,
            public_edit=public_edit
        )
        db_session.add(tournament)
        db_session.commit()
        return tournament


class MatchFactory:
    """Factory for creating Match instances."""

    @staticmethod
    def create(db_session, tournament_id, round_number=1, position_in_round=0,
               team1_id=None, team2_id=None, status='pending', is_bye=False):
        """Create a match.

        Args:
            db_session: Database session
            tournament_id: ID of tournament
            round_number: Round number (1, 2, 3, etc.)
            position_in_round: Position within round
            team1_id: ID of first team
            team2_id: ID of second team
            status: Match status
            is_bye: Whether this is a bye match

        Returns:
            Match instance
        """
        match = Match(
            tournament_id=tournament_id,
            round_number=round_number,
            position_in_round=position_in_round,
            team1_id=team1_id,
            team2_id=team2_id,
            status=status,
            is_bye=is_bye
        )
        db_session.add(match)
        db_session.commit()
        return match


class PenaltyFactory:
    """Factory for creating Penalty instances."""

    @staticmethod
    def create(db_session, game_id, name='Test Penalty', value=5, stackable=False):
        """Create a penalty.

        Args:
            db_session: Database session
            game_id: ID of associated game
            name: Penalty name
            value: Penalty value
            stackable: Whether penalty can stack

        Returns:
            Penalty instance
        """
        penalty = Penalty(
            game_id=game_id,
            name=name,
            value=value,
            stackable=stackable
        )
        db_session.add(penalty)
        db_session.commit()
        return penalty
