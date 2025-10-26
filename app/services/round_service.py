"""Service layer for round management in multi-round games."""
from app import db
from app.models import Round, RoundScore, Game, Team
from sqlalchemy.exc import SQLAlchemyError

MAX_ROUNDS = 50


class RoundService:
    """Service class for managing game rounds and round scoring."""

    @staticmethod
    def create_rounds_for_game(game_id, number_of_rounds, descriptions=None):
        """
        Create rounds for a game.

        Args:
            game_id: Game ID
            number_of_rounds: Number of rounds to create
            descriptions: Optional list of descriptions for each round

        Returns:
            List of created Round objects

        Raises:
            ValueError: If game not found or invalid parameters
            SQLAlchemyError: If database operation fails
        """
        game = Game.query.get(game_id)
        if not game:
            raise ValueError(f"Game with ID {game_id} not found")

        if number_of_rounds < 1:
            raise ValueError("Number of rounds must be at least 1")

        if number_of_rounds > MAX_ROUNDS:
            raise ValueError(f"Number of rounds cannot exceed {MAX_ROUNDS}")

        # Check if rounds already exist
        existing_rounds = Round.query.filter_by(game_id=game_id).count()
        if existing_rounds > 0:
            raise ValueError(f"Game {game_id} already has rounds. Delete existing rounds first.")

        rounds = []
        descriptions = descriptions or []

        try:
            for i in range(1, number_of_rounds + 1):
                description = descriptions[i - 1] if i - 1 < len(descriptions) else None
                round_obj = Round(
                    game_id=game_id,
                    round_number=i,
                    description=description
                )
                db.session.add(round_obj)
                rounds.append(round_obj)

            db.session.commit()
            return rounds
        except SQLAlchemyError as e:
            db.session.rollback()
            raise SQLAlchemyError(f"Error creating rounds: {str(e)}")

    @staticmethod
    def get_rounds_for_game(game_id, ordered=True):
        """
        Get all rounds for a game.

        Args:
            game_id: Game ID
            ordered: If True, order by round number

        Returns:
            List of Round objects
        """
        query = Round.query.filter_by(game_id=game_id)
        if ordered:
            query = query.order_by(Round.round_number)
        return query.all()

    @staticmethod
    def get_round_by_id(round_id):
        """
        Get a specific round by ID.

        Args:
            round_id: Round ID

        Returns:
            Round object or None
        """
        return Round.query.get(round_id)

    @staticmethod
    def get_round_by_game_and_number(game_id, round_number):
        """
        Get a specific round by game ID and round number.

        Args:
            game_id: Game ID
            round_number: Round number

        Returns:
            Round object or None
        """
        return Round.query.filter_by(
            game_id=game_id,
            round_number=round_number
        ).first()

    @staticmethod
    def save_round_score(round_id, team_id, score_value, points, notes=None):
        """
        Save or update a score for a team in a specific round.

        Args:
            round_id: Round ID
            team_id: Team ID
            score_value: Raw score value
            points: Calculated points
            notes: Optional notes

        Returns:
            RoundScore object

        Raises:
            ValueError: If round or team not found
            SQLAlchemyError: If database operation fails
        """
        round_obj = Round.query.get(round_id)
        if not round_obj:
            raise ValueError(f"Round with ID {round_id} not found")

        team = Team.query.get(team_id)
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        try:
            # Find or create round score
            round_score = RoundScore.query.filter_by(
                round_id=round_id,
                team_id=team_id
            ).first()

            if not round_score:
                round_score = RoundScore(
                    round_id=round_id,
                    team_id=team_id
                )
                db.session.add(round_score)

            # Update score data
            round_score.score_value = score_value
            round_score.points = points
            if notes is not None:
                round_score.notes = notes

            db.session.commit()
            return round_score
        except SQLAlchemyError as e:
            db.session.rollback()
            raise SQLAlchemyError(f"Error saving round score: {str(e)}")

    @staticmethod
    def get_round_scores(round_id, ordered=True):
        """
        Get all scores for a specific round.

        Args:
            round_id: Round ID
            ordered: If True, order by points descending

        Returns:
            List of RoundScore objects
        """
        query = RoundScore.query.filter_by(round_id=round_id)
        if ordered:
            query = query.order_by(RoundScore.points.desc())
        return query.all()

    @staticmethod
    def get_round_score_for_team(round_id, team_id):
        """
        Get a specific team's score for a round.

        Args:
            round_id: Round ID
            team_id: Team ID

        Returns:
            RoundScore object or None
        """
        return RoundScore.query.filter_by(
            round_id=round_id,
            team_id=team_id
        ).first()

    @staticmethod
    def get_cumulative_scores_for_game(game_id):
        """
        Calculate cumulative scores across all rounds for a game.

        Returns a dictionary with team statistics including:
        - Total points across all rounds
        - Round-by-round breakdown
        - Average score per round

        Args:
            game_id: Game ID

        Returns:
            Dict mapping team_id to cumulative score data:
            {
                team_id: {
                    'total_points': int,
                    'rounds': [
                        {'round_number': int, 'score_value': float, 'points': int},
                        ...
                    ],
                    'average_score': float
                }
            }
        """
        game = Game.query.get(game_id)
        if not game or not game.has_rounds:
            return {}

        rounds = RoundService.get_rounds_for_game(game_id)
        if not rounds:
            return {}

        # Get all teams for this game's game night
        if game.game_night_id:
            teams = Team.query.filter_by(game_night_id=game.game_night_id).all()
        else:
            teams = Team.query.all()

        cumulative_data = {}

        for team in teams:
            team_data = {
                'total_points': 0,
                'rounds': [],
                'average_score': 0.0,
                'rounds_played': 0
            }

            total_score_value = 0.0
            rounds_with_scores = 0

            for round_obj in rounds:
                round_score = RoundService.get_round_score_for_team(
                    round_obj.id,
                    team.id
                )

                if round_score:
                    team_data['total_points'] += round_score.points or 0

                    team_data['rounds'].append({
                        'round_number': round_obj.round_number,
                        'round_id': round_obj.id,
                        'description': round_obj.description,
                        'score_value': round_score.score_value,
                        'points': round_score.points,
                        'notes': round_score.notes
                    })

                    if round_score.score_value is not None:
                        total_score_value += round_score.score_value
                        rounds_with_scores += 1
                else:
                    # No score for this round yet
                    team_data['rounds'].append({
                        'round_number': round_obj.round_number,
                        'round_id': round_obj.id,
                        'description': round_obj.description,
                        'score_value': None,
                        'points': 0,
                        'notes': None
                    })

            team_data['rounds_played'] = rounds_with_scores
            if rounds_with_scores > 0:
                team_data['average_score'] = total_score_value / rounds_with_scores

            cumulative_data[team.id] = team_data

        return cumulative_data

    @staticmethod
    def calculate_and_save_round_scores(round_id, raw_scores):
        """
        Calculate points from raw scores and save for a round.

        This mirrors the auto-calculation logic from ScoreService but for rounds.

        Args:
            round_id: Round ID
            raw_scores: Dict mapping team_id to raw score value

        Returns:
            List of saved RoundScore objects

        Raises:
            ValueError: If round not found
        """
        round_obj = Round.query.get(round_id)
        if not round_obj:
            raise ValueError(f"Round with ID {round_id} not found")

        game = round_obj.game

        # Rank teams
        lower_is_better = (game.scoring_direction == 'lower_better')
        team_scores = [(tid, score) for tid, score in raw_scores.items() if score is not None]
        team_scores.sort(key=lambda x: x[1], reverse=not lower_is_better)

        # Calculate points for each team
        total_teams = len(team_scores)
        saved_scores = []

        for rank, (team_id, score_value) in enumerate(team_scores):
            points = (total_teams - rank) * game.point_scheme
            points = max(points, 0)

            round_score = RoundService.save_round_score(
                round_id,
                team_id,
                score_value,
                points
            )
            saved_scores.append(round_score)

        return saved_scores

    @staticmethod
    def delete_round(round_id):
        """
        Delete a round and all associated scores.

        Args:
            round_id: Round ID

        Raises:
            ValueError: If round not found
            SQLAlchemyError: If database operation fails
        """
        round_obj = Round.query.get(round_id)
        if not round_obj:
            raise ValueError(f"Round with ID {round_id} not found")

        try:
            db.session.delete(round_obj)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise SQLAlchemyError(f"Error deleting round: {str(e)}")

    @staticmethod
    def update_round_description(round_id, description):
        """
        Update the description for a round.

        Args:
            round_id: Round ID
            description: New description text

        Returns:
            Updated Round object

        Raises:
            ValueError: If round not found
        """
        round_obj = Round.query.get(round_id)
        if not round_obj:
            raise ValueError(f"Round with ID {round_id} not found")

        round_obj.description = description
        db.session.commit()
        return round_obj
