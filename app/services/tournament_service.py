import math
import random
from typing import List, Dict, Optional, Tuple
from app import db
from app.models import Tournament, Match, Team, Game


class TournamentService:

    @staticmethod
    def create_tournament(game_id: int, pairing_type: str = 'random',
                         bracket_style: str = 'standard', public_edit: bool = False,
                         manual_pairings: Optional[List[Tuple[int, int]]] = None,
                         included_team_ids: Optional[List[int]] = None) -> Tournament:
        """
        Create a tournament bracket for a game.

        Args:
            game_id: The game ID to create tournament for
            pairing_type: 'random' or 'manual'
            bracket_style: 'standard' (simpler, better) or 'play_in' (complex)
            public_edit: Allow public editing of match results
            manual_pairings: List of (team1_id, team2_id) tuples for manual pairing
            included_team_ids: List of team IDs to include (None = all teams)

        Returns:
            Tournament object
        """
        game = Game.query.get_or_404(game_id)

        # Create tournament
        tournament = Tournament(
            game_id=game_id,
            pairing_type=pairing_type,
            bracket_style=bracket_style,
            public_edit=public_edit
        )
        db.session.add(tournament)
        db.session.flush()  # Get tournament ID

        # Get teams (filter by included_team_ids if provided)
        if included_team_ids:
            teams = Team.query.filter(Team.id.in_(included_team_ids)).all()
        else:
            teams = Team.query.all()
        team_count = len(teams)

        if team_count < 2:
            raise ValueError("At least 2 teams are required for a tournament")

        # Generate bracket
        TournamentService._generate_simple_bracket(tournament, teams, pairing_type, manual_pairings)

        db.session.commit()
        return tournament

    @staticmethod
    def _generate_simple_bracket(tournament: Tournament, teams: List[Team],
                                 pairing_type: str, manual_pairings: Optional[List[Tuple[int, int]]]):
        """
        Generate a simple single-elimination bracket.

        This creates a clean bracket where:
        - Teams are paired in round 1
        - If odd number of teams, one team gets a bye (automatic win to round 2)
        - Winners advance through subsequent rounds to the final
        """
        team_count = len(teams)

        # Prepare team order
        if pairing_type == 'random' and not manual_pairings:
            team_list = teams.copy()
            random.shuffle(team_list)
        else:
            team_list = teams

        # Calculate bracket structure
        # We need enough matches to accommodate all teams
        # For N teams: need ceil(N/2) first round matches
        # Then each subsequent round has half the matches

        # Find nearest power of 2 >= team_count for bracket size
        bracket_size = 1
        while bracket_size < team_count:
            bracket_size *= 2

        # Total rounds = log2(bracket_size)
        total_rounds = int(math.log2(bracket_size))

        # Build bracket from final backwards
        matches_by_round = {}

        # Create final match (last round)
        final = Match(
            tournament_id=tournament.id,
            round_number=total_rounds,
            position_in_round=0,
            status='pending'
        )
        db.session.add(final)
        db.session.flush()
        matches_by_round[total_rounds] = [final]

        # Create intermediate rounds working backwards
        # Round 1 has most matches, final round has 1 match
        for round_num in range(total_rounds - 1, 0, -1):
            num_matches = 2 ** (total_rounds - round_num)
            round_matches = []

            for pos in range(num_matches):
                match = Match(
                    tournament_id=tournament.id,
                    round_number=round_num,
                    position_in_round=pos,
                    status='pending'
                )

                # Link to next round
                next_round_pos = pos // 2
                next_match = matches_by_round[round_num + 1][next_round_pos]
                match.next_match_id = next_match.id
                match.next_match_position = 'team1' if pos % 2 == 0 else 'team2'

                db.session.add(match)
                db.session.flush()
                round_matches.append(match)

            matches_by_round[round_num] = round_matches

        # Assign teams to first round
        first_round = matches_by_round[1]
        team_idx = 0

        # Use manual pairings if provided
        if manual_pairings:
            for match_idx, match in enumerate(first_round):
                if match_idx < len(manual_pairings):
                    t1_id, t2_id = manual_pairings[match_idx]
                    match.team1_id = t1_id
                    match.team2_id = t2_id
                else:
                    # Fill remaining matches with unpaired teams
                    if team_idx < len(team_list):
                        match.team1_id = team_list[team_idx].id
                        team_idx += 1
                    if team_idx < len(team_list):
                        match.team2_id = team_list[team_idx].id
                        team_idx += 1
        else:
            # Auto-pair teams sequentially
            for match in first_round:
                if team_idx < len(team_list):
                    match.team1_id = team_list[team_idx].id
                    team_idx += 1

                if team_idx < len(team_list):
                    match.team2_id = team_list[team_idx].id
                    team_idx += 1
                elif match.team1_id:
                    # Odd team - gets a bye
                    match.is_bye = True
                    match.status = 'completed'
                    match.winner_team_id = match.team1_id

                    # Advance them immediately
                    if match.next_match_id:
                        next_match = match.next_match
                        if match.next_match_position == 'team1':
                            next_match.team1_id = match.team1_id
                        else:
                            next_match.team2_id = match.team1_id

    @staticmethod
    def get_tournament_by_game(game_id: int) -> Optional[Tournament]:
        """Get tournament for a game."""
        return Tournament.query.filter_by(game_id=game_id).first()

    @staticmethod
    def get_bracket_structure(tournament_id: int) -> Dict:
        """
        Get the bracket structure for display.

        Returns:
            Dictionary with rounds and matches organized for visualization
        """
        tournament = Tournament.query.get_or_404(tournament_id)
        matches = Match.query.filter_by(tournament_id=tournament_id).order_by(
            Match.round_number, Match.position_in_round
        ).all()

        # Organize by rounds
        bracket = {}
        for match in matches:
            round_num = match.round_number
            if round_num not in bracket:
                bracket[round_num] = []

            bracket[round_num].append({
                'id': match.id,
                'position': match.position_in_round,
                'team1': {'id': match.team1_id, 'name': match.team1.name, 'color': match.team1.color} if match.team1 else None,
                'team2': {'id': match.team2_id, 'name': match.team2.name, 'color': match.team2.color} if match.team2 else None,
                'team1_score': match.team1_score,
                'team2_score': match.team2_score,
                'winner_id': match.winner_team_id,
                'status': match.status,
                'is_bye': match.is_bye,
                'is_play_in': match.is_play_in,
                'is_ready': match.is_ready
            })

        return {
            'tournament': tournament,
            'bracket': bracket,
            'rounds': sorted(bracket.keys())
        }

    @staticmethod
    def update_match_result(match_id: int, team1_score: Optional[float],
                           team2_score: Optional[float], winner_team_id: int):
        """
        Update match result and advance winner.

        Args:
            match_id: Match ID
            team1_score: Score for team 1
            team2_score: Score for team 2
            winner_team_id: ID of winning team
        """
        match = Match.query.get_or_404(match_id)

        # Validate winner is one of the teams
        if winner_team_id not in [match.team1_id, match.team2_id]:
            raise ValueError("Winner must be one of the two teams in the match")

        # Update scores
        match.team1_score = team1_score
        match.team2_score = team2_score

        # Set winner and advance
        match.set_winner(winner_team_id)

        # Check if tournament is complete
        tournament = match.tournament
        if match.next_match_id is None:  # This was the final match
            tournament.is_completed = True
            tournament.winner_team_id = winner_team_id

        db.session.commit()

    @staticmethod
    def finalize_tournament(tournament_id: int) -> Tournament:
        """
        Finalize a tournament by marking the game as complete.
        This syncs the tournament winner to the game's completion status.

        Args:
            tournament_id: Tournament ID to finalize

        Returns:
            Tournament object

        Raises:
            ValueError: If tournament is not complete or has no winner
        """
        tournament = Tournament.query.get_or_404(tournament_id)

        # Validate tournament is complete with a winner
        if not tournament.is_completed:
            raise ValueError("Tournament is not yet complete. All matches must be scored first.")

        if not tournament.winner_team_id:
            raise ValueError("Tournament has no winner determined.")

        # Mark the associated game as completed
        game = Game.query.get_or_404(tournament.game_id)
        if game.isCompleted:
            raise ValueError("Game is already finalized.")

        game.isCompleted = True

        # Optionally, you could also add the winner to the Score table here
        # to integrate with the overall leaderboard system
        from app.services.score_service import ScoreService
        from app.models import Team

        # Get all teams that participated
        teams_in_tournament = set()
        matches = Match.query.filter_by(tournament_id=tournament_id).all()
        for match in matches:
            if match.team1_id:
                teams_in_tournament.add(match.team1_id)
            if match.team2_id:
                teams_in_tournament.add(match.team2_id)

        # Award points based on final placement
        # Winner gets full points, others get participation points
        team_count = len(teams_in_tournament)
        for team_id in teams_in_tournament:
            if team_id == tournament.winner_team_id:
                # Winner gets points as if they placed 1st
                points = team_count * game.point_scheme
            else:
                # Others get reduced points (you can adjust this logic)
                points = 1 * game.point_scheme

            # Create or update score
            ScoreService.save_scores(
                game.id,
                {team_id: {'points': points}},
                is_completed=False  # Don't mark again, we already did
            )

        db.session.commit()
        return tournament

    @staticmethod
    def reset_tournament(tournament_id: int):
        """Reset tournament to initial state."""
        tournament = Tournament.query.get_or_404(tournament_id)

        # Reset all matches
        matches = Match.query.filter_by(tournament_id=tournament_id).all()

        # First, clear all next round progressions
        for match in matches:
            if not match.is_bye:
                match.status = 'pending'
                match.team1_score = None
                match.team2_score = None
                match.winner_team_id = None

                # Clear next round assignments (keep only round 1 teams)
                if match.round_number > 1:
                    match.team1_id = None
                    match.team2_id = None

        tournament.is_completed = False
        tournament.winner_team_id = None

        db.session.commit()
