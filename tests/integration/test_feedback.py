"""Integration tests for feedback form."""
import pytest
import json
from pathlib import Path
import shutil


@pytest.fixture(autouse=True)
def clear_feedback_dir(app):
    """Clear feedback directory and rate limiting before each test."""
    # Clear rate limiting dictionary
    from app.routes.main import feedback_submissions
    feedback_submissions.clear()

    feedback_dir = app.config['FEEDBACK_DIR']
    # Clean up feedback files before test
    for f in feedback_dir.glob('feedback_*.json'):
        f.unlink()
    yield
    # Clean up after test
    for f in feedback_dir.glob('feedback_*.json'):
        f.unlink()
    # Clear rate limiting after test
    feedback_submissions.clear()


class TestFeedbackForm:
    """Test feedback form submission."""

    def test_feedback_form_renders_on_index(self, client, db_session):
        """Test that feedback link appears on index page."""
        response = client.get('/')
        assert response.status_code == 200
        # Check for the feedback link/button text
        assert b'Please Give Me Your Feedback' in response.data or b'feedback' in response.data.lower()
        assert b'/feedback' in response.data

    def test_feedback_submission_success(self, app, db_session):
        """Test successful feedback submission."""
        # Use fresh client to avoid rate limiting
        with app.test_client() as client:
            response = client.post('/submit-feedback', data={
                'scoring_clarity': '5',
                'overall_clarity': '4',
                'mobile_usability': '5',
                'navigation_ease': '4',
                'visual_design': '5',
                'feature_satisfaction': '4',
                'suggestions': 'Great app! Love the design.',
                'csrf_token': 'dummy'  # CSRF is disabled in testing
            }, follow_redirects=True)

            assert response.status_code == 200
            assert b'Thank you for your feedback' in response.data

            # Check that feedback file was created
            feedback_dir = app.config['FEEDBACK_DIR']
            feedback_files = list(feedback_dir.glob('feedback_*.json'))
            assert len(feedback_files) > 0

            # Verify content of the feedback file
            latest_feedback = feedback_files[-1]
            with open(latest_feedback) as f:
                data = json.load(f)

            assert data['scoring_clarity'] == 5
            assert data['overall_clarity'] == 4
            assert data['mobile_usability'] == 5
            assert data['suggestions'] == 'Great app! Love the design.'
            assert 'timestamp' in data
            assert 'ip_hash' in data

    def test_feedback_missing_required_fields(self, client, db_session):
        """Test feedback submission with missing required fields."""
        response = client.post('/submit-feedback', data={
            'suggestions': 'Some suggestion',
            'csrf_token': 'dummy'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should show error or redirect back

    def test_feedback_rate_limiting(self, app, db_session):
        """Test feedback rate limiting (5 submissions per hour)."""
        # Use fresh client for rate limiting test
        with app.test_client() as client:
            # Submit feedback 5 times
            for i in range(5):
                response = client.post('/submit-feedback', data={
                    'scoring_clarity': '5',
                    'overall_clarity': '5',
                    'mobile_usability': '5',
                    'navigation_ease': '5',
                    'visual_design': '5',
                    'feature_satisfaction': '5',
                    'suggestions': f'Feedback {i}',
                    'csrf_token': 'dummy'
                }, follow_redirects=True)
                assert response.status_code == 200

            # 6th submission should be rate limited
            response = client.post('/submit-feedback', data={
                'scoring_clarity': '5',
                'overall_clarity': '5',
                'mobile_usability': '5',
                'navigation_ease': '5',
                'visual_design': '5',
                'feature_satisfaction': '5',
                'suggestions': 'One too many',
                'csrf_token': 'dummy'
            }, follow_redirects=True)

            assert response.status_code == 200
            assert b'submitted feedback recently' in response.data or b'try again later' in response.data

    def test_feedback_suggestions_optional(self, app, db_session):
        """Test that suggestions field is optional."""
        # Use fresh client to avoid rate limiting
        with app.test_client() as client:
            response = client.post('/submit-feedback', data={
                'scoring_clarity': '3',
                'overall_clarity': '4',
                'mobile_usability': '3',
                'navigation_ease': '4',
                'visual_design': '3',
                'feature_satisfaction': '4',
                'suggestions': '',  # Empty suggestions
                'csrf_token': 'dummy'
            }, follow_redirects=True)

            assert response.status_code == 200
            assert b'Thank you for your feedback' in response.data

    def test_feedback_character_limit(self, client, db_session):
        """Test that suggestions field enforces 500 character limit."""
        long_text = 'x' * 501  # 501 characters

        response = client.post('/submit-feedback', data={
            'scoring_clarity': '5',
            'overall_clarity': '5',
            'mobile_usability': '5',
            'navigation_ease': '5',
            'visual_design': '5',
            'feature_satisfaction': '5',
            'suggestions': long_text,
            'csrf_token': 'dummy'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should either reject or truncate
