# Game Night Tracker

A web application for managing competitive game nights with real-time scoring, tournaments, and leaderboards.

## Features

- **Real-Time Scoring**: Live collaborative scoring with WebSocket synchronization and auto-save
- **Tournament System**: Single-elimination brackets with automatic winner advancement
- **Leaderboard Rankings**: Dynamic rankings with customizable scoring rules and penalties
- **Team Management**: Create and manage teams with multiple participants
- **Game Library**: Flexible game types with configurable scoring directions and penalty systems
- **Timer System**: Track game times with multi-timer support and automatic averaging
- **Round-Based Games**: Support for multi-round games with independent round scoring
- **Mobile Responsive**: Optimized interface for scoring on any device

## Technology Stack

### Backend
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite (development) / PostgreSQL (production)
- **Real-time**: Socket.IO for WebSocket communication
- **Authentication**: Flask-Login with secure session management
- **Security**: CSRF protection, rate limiting, input validation

### Frontend
- **Build System**: Webpack 5 with Babel transpilation
- **JavaScript**: ES6 modules with service layer architecture
- **Styling**: Modular CSS with responsive design
- **Real-time**: Socket.IO client for live updates

### Testing
- **Coverage**: 72%+ test coverage (474 passing tests)
- **Frameworks**: Pytest, Playwright
- **Types**: Unit, integration, and end-to-end tests

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- Virtual environment tool (venv/virtualenv)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd GameNight

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Build frontend assets
npm run build

# Initialize database
flask db upgrade

# Run the application
flask run
```

Access the application at `http://localhost:5000`

### Development Mode

```bash
# Terminal 1: Run Flask with auto-reload
flask run --debug

# Terminal 2: Watch and rebuild frontend files
npm run watch
```

## Project Structure

```
GameNight/
├── app/
│   ├── models/               # Database models (SQLAlchemy)
│   ├── routes/               # Flask blueprints (main, admin, auth)
│   ├── services/             # Business logic layer
│   ├── websockets/           # WebSocket handlers and lock management
│   ├── forms/                # WTForms form definitions
│   ├── templates/            # Jinja2 templates
│   ├── static/
│   │   ├── js/src/          # ES6 source modules
│   │   ├── css/             # Stylesheets
│   │   └── dist/            # Webpack build output
│   └── utils/               # Utilities (logging, validators, helpers)
├── tests/                   # Test suite
├── migrations/              # Alembic database migrations
└── config.py                # Application configuration
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_admin_routes.py

# Run with verbose output
pytest -v
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///gamenight.db  # or PostgreSQL URL

# Optional
FLASK_ENV=production
LOG_LEVEL=INFO
```

### Production Deployment

- Set a strong `SECRET_KEY` environment variable
- Configure production database (PostgreSQL recommended)
- Run `npm run build` for optimized frontend assets
- Set up HTTPS and configure security headers
- Enable log rotation and monitoring
- Run database migrations with `flask db upgrade`

## Security

- CSRF protection on all forms
- Rate limiting on sensitive endpoints
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via Jinja2 auto-escaping
- Secure session management with HTTPOnly cookies
- Input validation on all user data

## Key Features

### Real-Time Scoring
Live score updates using WebSocket connections with collaborative editing locks to prevent conflicts. Includes auto-save functionality and visual indicators for locked fields.

### Tournament System
Automated single-elimination bracket generation with support for play-in matches, manual pairings, and team filtering. Automatic winner advancement through rounds.

### Leaderboard System
Dynamic point calculation with support for multiple scoring directions (higher/lower better), stackable and one-time penalties, and game night-specific rankings.

## License

This project is licensed under the MIT License.

## Technologies

- Flask & SQLAlchemy
- Socket.IO for real-time communication
- Webpack & Babel for frontend builds
- Pytest for testing
- Font Awesome icons
