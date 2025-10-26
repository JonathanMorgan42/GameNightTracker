from app import db
from app.models import Game, Penalty


class GameService:

    @staticmethod
    def get_all_games(ordered=True, game_night_id=None):
        """
        Get all games, optionally filtered by game night.

        Args:
            ordered: If True, order by sequence_number
            game_night_id: If provided, filter games by game night

        Returns:
            List of Game objects
        """
        query = Game.query

        if game_night_id:
            query = query.filter_by(game_night_id=game_night_id)

        if ordered:
            return query.order_by(Game.sequence_number).all()
        return query.all()

    @staticmethod
    def get_game_by_id(game_id):
        """Get game by ID."""
        return Game.query.get_or_404(game_id)

    @staticmethod
    def create_game(form_data, penalties_data=None, game_night_id=None):
        """
        Create a new game.

        Args:
            form_data: Dict with game data from form
            penalties_data: List of penalty dicts (optional)
            game_night_id: Optional game night ID to associate with

        Returns:
            Created Game object
        """
        # Auto-associate with working context game night if not specified
        if game_night_id is None:
            from app.services.game_night_service import GameNightService
            working_context = GameNightService.get_working_context_game_night()
            if working_context:
                game_night_id = working_context.id

        new_sequence = form_data['sequence_number']

        # Shift existing games to make room for the new game
        # Only shift games within the same game night
        if game_night_id:
            existing_games = Game.query.filter(
                Game.sequence_number >= new_sequence,
                Game.game_night_id == game_night_id
            ).all()
        else:
            existing_games = Game.query.filter(Game.sequence_number >= new_sequence).all()
        for existing_game in existing_games:
            existing_game.sequence_number += 1

        game = Game(
            name=form_data['name'],
            type=form_data['type'],
            sequence_number=new_sequence,
            point_scheme=form_data['point_scheme'],
            metric_type=form_data['metric_type'],
            scoring_direction=form_data.get('scoring_direction', 'lower_better'),
            public_input=form_data.get('public_input', False),
            game_night_id=game_night_id,
            isCompleted=False,
            has_rounds=form_data.get('has_rounds', False),
            number_of_rounds=form_data.get('number_of_rounds')
        )
        db.session.add(game)
        db.session.flush()  # Get game.id for penalties

        # Add penalties if provided
        if penalties_data:
            for penalty_data in penalties_data:
                penalty = Penalty(
                    game_id=game.id,
                    name=penalty_data['name'],
                    value=penalty_data['value'],
                    stackable=penalty_data.get('stackable', False)
                )
                db.session.add(penalty)

        db.session.commit()
        return game

    @staticmethod
    def update_game(game_id, form_data, penalties_data=None):
        """
        Update game.

        Args:
            game_id: Game ID
            form_data: Dict with updated game data
            penalties_data: List of penalty dicts (optional)
        """
        game = Game.query.get_or_404(game_id)
        old_sequence = game.sequence_number
        new_sequence = form_data['sequence_number']

        # If sequence number changed, handle reordering
        if old_sequence != new_sequence:
            # Only shift games within the same game night
            base_query = Game.query.filter(Game.id != game_id)
            if game.game_night_id:
                base_query = base_query.filter(Game.game_night_id == game.game_night_id)

            if new_sequence < old_sequence:
                # Moving up (lower number): shift games between new and old position down
                games_to_shift = base_query.filter(
                    Game.sequence_number >= new_sequence,
                    Game.sequence_number < old_sequence
                ).all()
                for g in games_to_shift:
                    g.sequence_number += 1
            else:
                # Moving down (higher number): shift games between old and new position up
                games_to_shift = base_query.filter(
                    Game.sequence_number > old_sequence,
                    Game.sequence_number <= new_sequence
                ).all()
                for g in games_to_shift:
                    g.sequence_number -= 1

        game.name = form_data['name']
        game.type = form_data['type']
        game.sequence_number = new_sequence
        game.point_scheme = form_data['point_scheme']
        game.metric_type = form_data['metric_type']
        game.scoring_direction = form_data.get('scoring_direction', 'lower_better')
        game.public_input = form_data.get('public_input', False)
        game.has_rounds = form_data.get('has_rounds', False)
        game.number_of_rounds = form_data.get('number_of_rounds')

        # Delete existing penalties
        Penalty.query.filter_by(game_id=game_id).delete()

        # Add new penalties if provided
        if penalties_data:
            for penalty_data in penalties_data:
                penalty = Penalty(
                    game_id=game_id,
                    name=penalty_data['name'],
                    value=penalty_data['value'],
                    stackable=penalty_data.get('stackable', False)
                )
                db.session.add(penalty)

        db.session.commit()
        return game

    @staticmethod
    def delete_game(game_id):
        """
        Delete game and all associated data (scores, penalties, tournaments).
        Uses SQLAlchemy cascade to automatically delete related data.

        Args:
            game_id: Game ID to delete
        """
        game = Game.query.get_or_404(game_id)

        # Simply delete the game - cascade will handle scores, penalties, tournaments, and matches
        db.session.delete(game)
        db.session.commit()

    @staticmethod
    def get_completed_games():
        """Get all completed games."""
        return Game.query.filter_by(isCompleted=True).order_by(Game.sequence_number).all()

    @staticmethod
    def get_upcoming_games():
        """Get all upcoming games."""
        return Game.query.filter_by(isCompleted=False).order_by(Game.sequence_number).all()