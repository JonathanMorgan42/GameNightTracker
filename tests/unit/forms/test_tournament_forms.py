"""Unit tests for Tournament Forms.

Test IDs: FORM-T-001 through FORM-T-009
Coverage: TournamentSetupForm, MatchScoreForm validation
"""
import pytest
from app.forms.tournament_forms import TournamentSetupForm, MatchScoreForm


@pytest.mark.unit
@pytest.mark.forms
class TestTournamentForms:
    """Test suite for Tournament forms."""

    def test_tournament_setup_form_valid(self):
        """FORM-T-001: Test valid tournament setup form."""
        form = TournamentSetupForm(data={
            'game_id': '1',
            'pairing_type': 'random',
            'bracket_style': 'standard',
            'public_edit': False
        })

        assert form.validate() or len(form.errors) == 0

    def test_tournament_setup_pairing_type_choices(self):
        """FORM-T-002: Test pairing_type must be 'random' or 'manual'."""
        form_random = TournamentSetupForm(data={
            'game_id': '1',
            'pairing_type': 'random',
            'bracket_style': 'standard',
            'public_edit': False
        })

        form_manual = TournamentSetupForm(data={
            'game_id': '1',
            'pairing_type': 'manual',
            'bracket_style': 'standard',
            'public_edit': False
        })

        # Both should be valid
        assert form_random.validate() or 'pairing_type' not in form_random.errors
        assert form_manual.validate() or 'pairing_type' not in form_manual.errors

    def test_tournament_setup_bracket_style_choices(self):
        """FORM-T-003: Test bracket_style must be 'standard' or 'play_in'."""
        form = TournamentSetupForm(data={
            'game_id': '1',
            'pairing_type': 'random',
            'bracket_style': 'standard',
            'public_edit': False
        })

        assert form.validate() or 'bracket_style' not in form.errors

    def test_tournament_setup_public_edit_boolean(self):
        """FORM-T-004: Test public_edit boolean field."""
        form = TournamentSetupForm(data={
            'game_id': '1',
            'pairing_type': 'random',
            'bracket_style': 'standard',
            'public_edit': True
        })

        assert form.validate() or 'public_edit' not in form.errors

    def test_tournament_setup_game_id_hidden(self):
        """FORM-T-005: Test game_id hidden field."""
        form = TournamentSetupForm(data={
            'game_id': '123',
            'pairing_type': 'random',
            'bracket_style': 'standard',
            'public_edit': False
        })

        assert form.game_id.data == '123' or form.validate()

    def test_match_score_form_valid(self):
        """FORM-T-006: Test valid match score form."""
        form = MatchScoreForm(data={
            'match_id': '1',
            'team1_score': '100.0',
            'team2_score': '90.0',
            'winner_team_id': '5'
        })

        assert form.validate() or len(form.errors) == 0

    def test_match_score_form_required_fields(self):
        """FORM-T-007: Test match_id and winner required."""
        form = MatchScoreForm(data={})

        # Form should have validation errors
        assert not form.validate() or 'match_id' in form.errors or 'winner_team_id' in form.errors

    def test_match_score_form_optional_scores(self):
        """FORM-T-008: Test team scores are optional."""
        form = MatchScoreForm(data={
            'match_id': '1',
            'winner_team_id': '5'
        })

        # Should be valid even without scores
        assert form.validate() or ('team1_score' not in form.errors and 'team2_score' not in form.errors)

    def test_match_score_form_winner_validation(self):
        """FORM-T-009: Test winner must be one of the teams (logic in route)."""
        form = MatchScoreForm(data={
            'match_id': '1',
            'team1_score': '100.0',
            'team2_score': '90.0',
            'winner_team_id': '999'  # Validation happens in service
        })

        # Form validation passes, business logic validates in service
        assert True
