from datetime import datetime, date
from sqlalchemy import func
from app import db
from app.models import GameNight, Team, Game


class GameNightService:

    @staticmethod
    def create_game_night(name, game_date=None):
        """
        Create a new game night session.
        Automatically sets as working context if no other working context exists.

        Args:
            name: Name of the game night
            game_date: Date of the game night (defaults to today)

        Returns:
            The created GameNight object
        """
        if game_date is None:
            game_date = date.today()

        # Convert string date to date object if needed
        if isinstance(game_date, str):
            game_date = datetime.strptime(game_date, '%Y-%m-%d').date()

        # Check if there's already a working context
        has_working_context = GameNight.query.filter_by(is_working_context=True).first() is not None

        game_night = GameNight(
            name=name,
            date=game_date,
            is_active=False,  # Don't automatically activate
            is_working_context=not has_working_context,  # Set as working context if none exists
            is_completed=False
        )

        db.session.add(game_night)
        db.session.commit()

        return game_night

    @staticmethod
    def set_active_game_night(game_night_id):
        """
        Set a game night as active. Deactivates all other game nights.
        Automatically archives (marks as completed) the previously active game night.

        Args:
            game_night_id: ID of the game night to activate

        Returns:
            The activated GameNight object

        Raises:
            ValueError: If validation fails (incomplete games, multiple active nights, etc.)
        """
        game_night = GameNight.query.get_or_404(game_night_id)

        # Validation: Check that the game night being activated has required data
        if game_night.teams.count() < 2:
            raise ValueError(f'Cannot activate: Game night must have at least 2 teams. Currently has {game_night.teams.count()}.')

        if game_night.games.count() < 1:
            raise ValueError('Cannot activate: Game night must have at least 1 game.')

        # Get the currently active game night (if any)
        old_active = GameNight.query.filter_by(is_active=True).first()

        # Validation: If there's an active game night, ensure all its games are completed
        if old_active and old_active.id != game_night_id:
            incomplete_games = old_active.games.filter_by(isCompleted=False).count()
            if incomplete_games > 0:
                raise ValueError(
                    f'Cannot activate new game night: The currently active game night "{old_active.name}" '
                    f'has {incomplete_games} incomplete game(s). Please complete or end all games before activating a new game night.'
                )
            # Archive the old active game night
            old_active.finalize()  # This sets is_completed=True and is_active=False

        # Validation: Check for any other active game nights (belt and suspenders)
        other_active = GameNight.query.filter(
            GameNight.is_active == True,
            GameNight.id != game_night_id
        ).first()
        if other_active:
            raise ValueError(
                f'Cannot activate: Another game night "{other_active.name}" is currently active. '
                f'Only one game night can be active at a time.'
            )

        # Deactivate all game nights (in case there are multiple active, which shouldn't happen)
        GameNight.query.update({'is_active': False})

        # Activate the selected one
        game_night.is_active = True

        db.session.commit()

        return game_night

    @staticmethod
    def get_active_game_night():
        """
        Get the currently active game night (visible to public).

        Returns:
            The active GameNight object or None if no active session
        """
        return GameNight.query.filter_by(is_active=True).first()

    @staticmethod
    def get_working_context_game_night():
        """
        Get the game night currently being worked on (admin context).
        This is the game night that teams and games will be added to.

        Returns:
            The working context GameNight object or None if no working context
        """
        return GameNight.query.filter_by(is_working_context=True).first()

    @staticmethod
    def set_working_context(game_night_id):
        """
        Set a game night as the working context.
        Only one game night can be the working context at a time.

        Args:
            game_night_id: ID of the game night to set as working context

        Returns:
            The updated GameNight object
        """
        # Deactivate all working contexts
        GameNight.query.update({'is_working_context': False})

        # Set the selected one as working context
        game_night = GameNight.query.get_or_404(game_night_id)
        game_night.is_working_context = True

        db.session.commit()

        return game_night

    @staticmethod
    def get_all_game_nights(order='desc'):
        """
        Get all game nights, ordered by date.
        Optimized with subqueries to calculate counts and avoid N+1 queries.

        Args:
            order: 'desc' for newest first, 'asc' for oldest first

        Returns:
            List of GameNight objects with preloaded count attributes
        """
        # Subquery to count teams per game night
        teams_count = db.session.query(
            Team.game_night_id,
            func.count(Team.id).label('team_count')
        ).group_by(Team.game_night_id).subquery()

        # Subquery to count total games per game night
        games_count = db.session.query(
            Game.game_night_id,
            func.count(Game.id).label('game_count')
        ).group_by(Game.game_night_id).subquery()

        # Subquery to count completed games per game night
        completed_games_count = db.session.query(
            Game.game_night_id,
            func.count(Game.id).label('completed_count')
        ).filter(Game.isCompleted == True).group_by(Game.game_night_id).subquery()

        # Main query with left joins to get counts
        query = db.session.query(
            GameNight,
            func.coalesce(teams_count.c.team_count, 0).label('_teams_count'),
            func.coalesce(games_count.c.game_count, 0).label('_total_games'),
            func.coalesce(completed_games_count.c.completed_count, 0).label('_completed_games')
        ).outerjoin(
            teams_count, GameNight.id == teams_count.c.game_night_id
        ).outerjoin(
            games_count, GameNight.id == games_count.c.game_night_id
        ).outerjoin(
            completed_games_count, GameNight.id == completed_games_count.c.game_night_id
        )

        if order == 'desc':
            query = query.order_by(GameNight.date.desc(), GameNight.created_at.desc())
        else:
            query = query.order_by(GameNight.date.asc(), GameNight.created_at.asc())

        # Execute query and attach counts to game night objects
        results = query.all()
        game_nights = []
        for row in results:
            game_night = row[0]
            # Cache the counts as attributes to avoid additional queries
            game_night._cached_teams_count = int(row[1])
            game_night._cached_total_games = int(row[2])
            game_night._cached_completed_games = int(row[3])
            game_nights.append(game_night)

        return game_nights

    @staticmethod
    def get_completed_game_nights():
        """
        Get all completed game nights, newest first.

        Returns:
            List of completed GameNight objects
        """
        return GameNight.query.filter_by(is_completed=True).order_by(
            GameNight.date.desc(),
            GameNight.ended_at.desc()
        ).all()

    @staticmethod
    def get_game_night_by_id(game_night_id):
        """
        Get a specific game night by ID.

        Args:
            game_night_id: ID of the game night

        Returns:
            GameNight object or 404 error
        """
        return GameNight.query.get_or_404(game_night_id)

    @staticmethod
    def get_game_night_details(game_night_id):
        """
        Get full details of a game night including teams, games, and leaderboard.

        Args:
            game_night_id: ID of the game night

        Returns:
            Dictionary with game night details
        """
        game_night = GameNight.query.get_or_404(game_night_id)

        teams = game_night.get_leaderboard()
        games = game_night.games.order_by(Game.sequence_number).all()
        completed_games = [g for g in games if g.isCompleted]
        upcoming_games = [g for g in games if not g.isCompleted]
        winner = game_night.get_winner()

        return {
            'game_night': game_night,
            'teams': teams,
            'games': games,
            'completed_games': completed_games,
            'upcoming_games': upcoming_games,
            'winner': winner
        }

    @staticmethod
    def end_game_night(game_night_id):
        """
        End a game night session. Marks it as completed and inactive.
        Locks all edits by finalizing the data.

        Args:
            game_night_id: ID of the game night to end

        Returns:
            The ended GameNight object
        """
        game_night = GameNight.query.get_or_404(game_night_id)
        game_night.finalize()

        return game_night

    @staticmethod
    def wipe_game_night_data(game_night_id):
        """
        Wipe all data from a game night (teams and games).
        Useful for resetting the active session.
        Uses proper deletion to trigger cascades.

        Args:
            game_night_id: ID of the game night to wipe

        Returns:
            The wiped GameNight object
        """
        game_night = GameNight.query.get_or_404(game_night_id)

        # Delete all games individually to trigger cascade (scores, penalties, tournaments, matches)
        games = Game.query.filter_by(game_night_id=game_night_id).all()
        for game in games:
            db.session.delete(game)

        # Delete all teams individually to trigger cascade (participants, scores)
        teams = Team.query.filter_by(game_night_id=game_night_id).all()
        for team in teams:
            db.session.delete(team)

        db.session.commit()

        return game_night

    @staticmethod
    def delete_game_night(game_night_id):
        """
        Permanently delete a game night and all associated data.

        Args:
            game_night_id: ID of the game night to delete
        """
        game_night = GameNight.query.get_or_404(game_night_id)

        db.session.delete(game_night)
        db.session.commit()

    @staticmethod
    def update_game_night(game_night_id, name=None, game_date=None):
        """
        Update game night details.

        Args:
            game_night_id: ID of the game night
            name: New name (optional)
            game_date: New date (optional)

        Returns:
            The updated GameNight object
        """
        game_night = GameNight.query.get_or_404(game_night_id)

        if name:
            game_night.name = name

        if game_date:
            if isinstance(game_date, str):
                game_date = datetime.strptime(game_date, '%Y-%m-%d').date()
            game_night.date = game_date

        db.session.commit()

        return game_night
