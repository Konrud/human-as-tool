# Backend - Interactive Agent Chat System

Backend API for the Interactive Agent Chat System, built with FastAPI and supporting WebSocket-based real-time communication with multi-channel feedback support.

## Prerequisites

- Python 3.13 or higher
- Poetry (Python dependency management)

## Setup Instructions

### 1. Install Poetry

If you don't have Poetry installed:

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Add Poetry to your PATH if needed.

### 2. Install Dependencies

```bash
cd backend
poetry install
```

This will create a virtual environment and install all required dependencies.

### 3. Configure Environment

A `.env` file should already exist in the `backend/` directory. Update the configuration values as needed:

```env
# Security - IMPORTANT: Change SECRET_KEY in production
SECRET_KEY=your-secret-key-here-change-in-production

# Add your external service credentials when ready
GMAIL_CLIENT_ID=your_gmail_client_id
SLACK_CLIENT_ID=your_slack_client_id
OPENAI_API_KEY=your_openai_api_key
```

### 4. Initialize BAML (Phase 6)

BAML framework setup will be completed in Phase 6. For now, you can check if BAML is installed:

```bash
poetry run baml-cli --version
```

To initialize BAML structure (will be done in Phase 6):

```bash
cd backend
poetry run baml-cli init
poetry run baml-cli generate
```

### 5. Run Development Server

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative docs (ReDoc)**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health
- **Root info**: http://localhost:8000/

## Authentication

### Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

### Get Current User

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## Project Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── routers/
│   │   │   └── auth.py              # Authentication endpoints
│   │   ├── websocket/
│   │   │   ├── connection.py        # WebSocket connection handler
│   │   │   └── manager.py           # Connection manager
│   │   └── dependencies.py          # Security dependencies
│   ├── models/
│   │   ├── base.py                  # Base models (Session, Message, etc.)
│   │   └── user.py                  # User and auth models
│   ├── services/
│   │   └── auth_service.py          # Authentication service (JWT, passwords)
│   ├── storage/
│   │   └── memory_store.py          # In-memory data storage
│   ├── config.py                    # Application configuration
│   └── main.py                      # FastAPI application
├── baml_src/                        # BAML templates (Phase 6)
├── pyproject.toml                   # Poetry dependencies
├── .env                             # Environment configuration
├── .gitignore                       # Git ignore patterns
└── README.md                        # This file
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
# Install development dependencies
poetry install --with dev

# Run tests with coverage
poetry run pytest --cov=src
```

### Adding Dependencies

```bash
# Production dependency
poetry add package-name

# Development dependency
poetry add --group dev package-name
```

## Features

### ✅ Phase 5 Complete

- **Poetry Dependency Management**: Clean dependency management with pyproject.toml
- **Environment Configuration**: Centralized settings with Pydantic Settings
- **OAuth2 Authentication**: User registration and login with JWT tokens
- **Password Security**: Bcrypt password hashing
- **In-Memory Storage**: User and session storage (upgradable to database)
- **Rate Limiting Structure**: Ready for implementation
- **CORS Configuration**: Frontend integration ready
- **API Documentation**: Auto-generated with FastAPI

### 🚧 Coming in Phase 6

- **BAML Agent Integration**: AI agent templates and orchestration
- **WebSocket Authentication**: Secure WebSocket connections
- **Rate Limiting Middleware**: Request rate limiting enforcement
- **Session Management**: Full chat session lifecycle
- **Channel Services**: Gmail and Slack integration
- **Feedback System**: Request/response handling

## Configuration

### JWT Tokens

- **Access Token**: Expires in 25 minutes (configurable)
- **Refresh Token**: Expires in 7 days (configurable)
- **Algorithm**: HS256

### Rate Limiting

- **Per User**: 30 requests/minute
- **Per Session**: 10 requests/minute
- **Per Channel**: 20 requests/minute

### Session Limits

- **Max Concurrent Sessions**: 3 per user
- **Session Timeout**: 24 hours
- **Feedback Timeout**: 48 hours

## Security Notes

⚠️ **Important for Production**:

1. Change `SECRET_KEY` in `.env` to a long random string
2. Set `DEBUG=false` in production
3. Use HTTPS in production
4. Restrict CORS origins to your frontend domain
5. Add proper database instead of in-memory storage
6. Implement proper logging and monitoring
7. Add rate limiting enforcement

## Troubleshooting

### Poetry Not Found

Make sure Poetry is in your PATH. Restart your terminal after installation.

### Import Errors

Make sure you're running commands with `poetry run`:

```bash
poetry run uvicorn src.main:app --reload
```

### Port Already in Use

Change the port:

```bash
poetry run uvicorn src.main:app --reload --port 8001
```

### BAML Issues

BAML setup will be completed in Phase 6. If you encounter issues:

```bash
poetry add baml-py
pip install baml-cli
```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

See LICENSE file in the project root.

## Next Steps

Continue with Phase 6 to implement:

- BAML agent templates
- WebSocket authentication
- Rate limiting middleware
- Session management service
- Channel services (Gmail, Slack)
- Feedback request/response handling
