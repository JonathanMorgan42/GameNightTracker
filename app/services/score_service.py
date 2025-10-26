from app import db
from app.models import Score, Game, Team, Round, RoundScore


class ScoreService:

    @staticmethod
    def get_scores_for_game(game_id, ordered=True):
        """
        Get all scores for a game.

        Args:
            game_id: Game ID
            ordered: If True, order by points descending

        Returns:
            List of Score objects
        """
        query = Score.query.filter_by(game_id=game_id)
        if ordered:
            query = query.order_by(Score.points.desc())
        return query.all()

    @staticmethod
    def get_score(team_id, game_id):
        """Get a specific score."""
        return Score.query.filter_by(team_id=team_id, game_id=game_id).first()

    @staticmethod
    def get_existing_scores_dict(game_id):
        """
        Get existing scores as a dictionary.

        Args:
            game_id: Game ID

        Returns:
            Dict mapping team_id to Score object
        """
        scores = Score.query.filter_by(game_id=game_id).all()
        return {score.team_id: score for score in scores}

    @staticmethod
    def calculate_points_from_rank(rank, increment, total_teams):
        """
        Calculate points based on rank.

        Args:
            rank: Team rank (0-indexed, 0 = first place)
            increment: Point increment (from game.point_scheme)
            total_teams: Total number of teams

        Returns:
            Points awarded
        """
        points = (total_teams - rank) * increment
        return max(points, 0)

    @staticmethod
    def rank_teams_by_scores(scores_data, lower_is_better=True):
        """
        Rank teams based on their scores.

        Args:
            scores_data: Dict mapping team_id to score value
            lower_is_better: If True, lower scores rank higher

        Returns:
            List of (team_id, score, rank) tuples, sorted by rank
        """
        # Create list of (team_id, score) tuples
        team_scores = [(tid, score) for tid, score in scores_data.items() if score is not None]

        # Sort by score
        team_scores.sort(key=lambda x: x[1], reverse=not lower_is_better)

        # Add ranks (0-indexed)
        ranked = [(tid, score, idx) for idx, (tid, score) in enumerate(team_scores)]

        return ranked

    @staticmethod
    def save_scores(game_id, scores_data, is_completed=False, notes=None):
        """
        Save or update scores for a game.

        Args:
            game_id: Game ID
            scores_data: Dict mapping team_id to dict with 'score', 'points', 'notes'
            is_completed: Mark game as completed
            notes: Optional game notes

        Returns:
            Updated Game object
        """
        game = Game.query.get_or_404(game_id)

        # Update game completion status
        game.isCompleted = is_completed

        # Process each team's score
        for team_id_str, score_data in scores_data.items():
            team_id = int(team_id_str)

            # Verify team exists
            team = Team.query.get(team_id)
            if not team:
                continue

            # Find or create score
            score = Score.query.filter_by(team_id=team_id, game_id=game_id).first()
            if not score:
                score = Score(team_id=team_id, game_id=game_id)
                db.session.add(score)

            # Update score data
            if 'score' in score_data and score_data['score'] is not None:
                try:
                    score.score_value = float(score_data['score'])
                except (ValueError, TypeError):
                    score.score_value = None

            if 'points' in score_data:
                try:
                    score.points = int(score_data['points'])
                except (ValueError, TypeError):
                    score.points = 0

            if 'notes' in score_data:
                score.notes = score_data['notes']

        # Commit all changes
        db.session.commit()
        return game

    @staticmethod
    def auto_calculate_and_save_scores(game_id, raw_scores, is_completed=False):
        """
        Automatically calculate points from raw scores and save.

        Args:
            game_id: Game ID
            raw_scores: Dict mapping team_id to raw score value
            is_completed: Mark game as completed

        Returns:
            Updated Game object
        """
        game = Game.query.get_or_404(game_id)

        # Rank teams
        lower_is_better = (game.scoring_direction == 'lower_better')
        ranked_teams = ScoreService.rank_teams_by_scores(
            raw_scores,
            lower_is_better
        )

        # Calculate points for each team
        total_teams = len(ranked_teams)
        scores_data = {}

        for team_id, score_value, rank in ranked_teams:
            points = ScoreService.calculate_points_from_rank(
                rank,
                game.point_scheme,
                total_teams
            )
            scores_data[team_id] = {
                'score': score_value,
                'points': points
            }

        # Save using the main save method
        return ScoreService.save_scores(game_id, scores_data, is_completed)

    @staticmethod
    def get_aggregate_scores_for_round_game(game_id):
        """
        Get aggregate scores for a round-based game.

        For games with rounds, this calculates total points across all rounds
        and stores them in the main Score table for compatibility with leaderboard.

        Args:
            game_id: Game ID

        Returns:
            Dict mapping team_id to total points
        """
        game = Game.query.get_or_404(game_id)

        if not game.has_rounds:
            # Not a round-based game, return regular scores
            scores = Score.query.filter_by(game_id=game_id).all()
            return {score.team_id: score.points for score in scores}

        # Get all rounds for this game
        rounds = Round.query.filter_by(game_id=game_id).order_by(Round.round_number).all()

        if not rounds:
            return {}

        # Calculate cumulative points for each team
        team_points = {}

        for round_obj in rounds:
            round_scores = RoundScore.query.filter_by(round_id=round_obj.id).all()
            for round_score in round_scores:
                if round_score.team_id not in team_points:
                    team_points[round_score.team_id] = 0
                team_points[round_score.team_id] += round_score.points or 0

        return team_points

    @staticmethod
    def sync_round_scores_to_main_scores(game_id):
        """
        Synchronize cumulative round scores to the main Score table.

        This is useful for maintaining compatibility with existing leaderboard
        and scoring displays that read from the Score table.

        Args:
            game_id: Game ID

        Returns:
            Number of scores synchronized
        """
        game = Game.query.get_or_404(game_id)

        if not game.has_rounds:
            return 0

        team_points = ScoreService.get_aggregate_scores_for_round_game(game_id)

        synced_count = 0
        for team_id, total_points in team_points.items():
            # Find or create score record
            score = Score.query.filter_by(game_id=game_id, team_id=team_id).first()
            if not score:
                score = Score(game_id=game_id, team_id=team_id)
                db.session.add(score)

            score.points = total_points
            # Set score_value to cumulative total as well for display purposes
            score.score_value = float(total_points)
            synced_count += 1

        db.session.commit()
        return synced_count