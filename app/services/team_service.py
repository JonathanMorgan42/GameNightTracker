from app import db
from app.models import Team, Participant
from app.utils.validators import TEAM_NAME_MAX


class TeamService:

    @staticmethod
    def get_all_teams(sort_by_points=True, game_night_id=None):
        """
        Get all teams, optionally filtered by game night.

        Args:
            sort_by_points: If True, sort by total points descending
            game_night_id: If provided, filter teams by game night

        Returns:
            List of Team objects
        """
        query = Team.query

        if game_night_id:
            query = query.filter_by(game_night_id=game_night_id)

        teams = query.all()
        if sort_by_points:
            if game_night_id:
                # Sort by game-night-specific points
                teams = sorted(teams, key=lambda t: t.get_points_for_game_night(game_night_id), reverse=True)
            else:
                # Sort by total points across all game nights
                teams = sorted(teams, key=lambda t: t.totalPoints, reverse=True)
        return teams

    @staticmethod
    def get_team_by_id(team_id):
        """Get team by ID."""
        return Team.query.get_or_404(team_id)

    @staticmethod
    def create_team(name, participants_data, color='#3b82f6', game_night_id=None):
        """
        Create a new team with participants.

        Args:
            name: Team name
            participants_data: List of dicts with firstName and lastName
            color: Team color (default: blue)
            game_night_id: Optional game night ID to associate with

        Returns:
            Created Team object
        """
        # Auto-associate with working context game night if not specified
        if game_night_id is None:
            from app.services.game_night_service import GameNightService
            working_context = GameNightService.get_working_context_game_night()
            if working_context:
                game_night_id = working_context.id

        # Truncate name if too long
        if len(name) > TEAM_NAME_MAX:
            name = name[:TEAM_NAME_MAX]

        team = Team(name=name, color=color, game_night_id=game_night_id)
        db.session.add(team)
        db.session.flush()  # Get team.id

        for participant_data in participants_data:
            participant = Participant(
                firstName=participant_data['firstName'],
                lastName=participant_data['lastName'],
                team_id=team.id
            )
            db.session.add(participant)

        db.session.commit()
        return team

    @staticmethod
    def update_team(team_id, name, participants_data, color=None):
        """
        Update team and participants.

        Args:
            team_id: Team ID
            name: New team name
            participants_data: List of dicts with firstName and lastName
            color: New team color (optional)
        """
        team = Team.query.get_or_404(team_id)

        # Truncate name if too long
        if len(name) > TEAM_NAME_MAX:
            name = name[:TEAM_NAME_MAX]

        team.name = name
        if color:
            team.color = color

        participants = list(team.participants)

        # Update existing participants and create new ones
        for i, participant_data in enumerate(participants_data):
            if i < len(participants):
                # Update existing participant
                participants[i].firstName = participant_data['firstName']
                participants[i].lastName = participant_data['lastName']
            else:
                # Create new participant
                new_participant = Participant(
                    firstName=participant_data['firstName'],
                    lastName=participant_data['lastName'],
                    team_id=team.id
                )
                db.session.add(new_participant)

        # Remove participants that are no longer in the list
        if len(participants) > len(participants_data):
            for i in range(len(participants_data), len(participants)):
                db.session.delete(participants[i])

        db.session.commit()
        return team

    @staticmethod
    def delete_team(team_id):
        """
        Delete team and all associated data.
        Uses SQLAlchemy cascade to automatically delete related participants and scores.

        Args:
            team_id: Team ID to delete
        """
        team = Team.query.get_or_404(team_id)

        # Simply delete the team - cascade will handle participants and scores
        db.session.delete(team)
        db.session.commit()