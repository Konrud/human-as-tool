# Quickstart Guide: Interactive Agent Chat System

## Prerequisites

1. Node.js >= 22.14.0
2. Python >= 3.13.3
3. Poetry (Python dependency management)
4. Gmail API credentials
5. Slack App credentials
6. VS Code with recommended extensions

### VS Code Configuration

Add the following to your VS Code User Settings for better Python and BAML support:

```json
{
  "python.analysis.typeCheckingMode": "basic"
}
```

## Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Konrud/human-as-tool.git
cd human-as-tool
git checkout 001-interactive-agent-chat
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env

# Start development server
npm run dev
```

Required environment variables:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_OAUTH_CLIENT_ID=your_oauth_client_id
```

### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
poetry install

# Install BAML
poetry add baml-py

# Set up environment
cp .env.example .env

# Initialize BAML project structure (creates baml_src directory)
poetry run baml-cli init

# Generate the baml_client Python module from .baml files
poetry run baml-cli generate

# Start development server
poetry run uvicorn main:app --reload
```

Required environment variables:

```env
# Server Configuration
PORT=8000
ENVIRONMENT=development

# Security
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=25
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_PER_USER=30
RATE_LIMIT_WINDOW_MINUTES=1

# External Services
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REDIRECT_URI=http://localhost:8000/auth/gmail/callback

SLACK_APP_ID=your_slack_app_id
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
SLACK_SIGNING_SECRET=your_slack_signing_secret

# BAML Configuration
OPENAI_API_KEY=your_openai_api_key  # Only needed if using OpenAI models
# Add other model-specific API keys as needed
```

## Development Workflow

### Frontend Development

1. **Component Development**

   ```bash
   # Create new component
   npm run gen:component ComponentName
   ```

2. **API Integration**

   ```bash
   # Create new query/mutation
   npm run gen:query QueryName
   ```

3. **Testing**

   ```bash
   # Run tests
   npm run test

   # Run tests in watch mode
   npm run test:watch
   ```

### Backend Development

1. **API Development**

   ```bash
   # Create new router
   poetry run python scripts/create_router.py RouterName
   ```

2. **BAML Development**

   ```bash
   # Generate Python client from BAML files
   poetry run baml-cli generate
   ```

   Note: If you have the VS Code BAML extension installed, it will automatically run
   `baml-cli generate` when saving a BAML file.

3. **Testing**

   ```bash
   # Run tests
   poetry run pytest

   # Run tests with coverage
   poetry run pytest --cov
   ```

## Common Tasks

### Adding a New Channel

1. Create channel handler:

   ```python
   # backend/services/channels/new_channel_handler.py
   from .base import BaseChannelHandler

   class NewChannelHandler(BaseChannelHandler):
       async def send_message(self, message: Message) -> bool:
           # Implementation
           pass
   ```

2. Register channel:
   ```python
   # backend/services/channel_service.py
   channel_manager.register_handler("new_channel", NewChannelHandler())
   ```

### Adding a New Prompt

1. Create BAML prompt:

   ```baml
   class ClarificationRequest {
    intent "request_more_information" @description("you can request more information from me")
    message string
    }

    class DoneForNow {
    intent "done_for_now"

    message string @description(#"
        message to send to the user about the work that was done.
    "#)
    }
    class ProcessRefund {
    intent "process_refund"
    order_id string
    amount int | float
    reason string
    }

    type HumanTools = ClarificationRequest | DoneForNow
    type CalculatorTools = AddTool | SubtractTool | MultiplyTool | DivideTool
    type CustomerSupportTools = ProcessRefund

    function DetermineNextStep(
        thread: string
    ) -> HumanTools | CalculatorTools | CustomerSupportTools {
        client "openai/gpt-4o"

        prompt #"
            {{ _.role("system") }}

            You are a helpful assistant that can help with tasks.

            {{ _.role("user") }}

            You are working on the following thread:

            {{ thread }}

            What should the next step be?

            {{ ctx.output_format }}

            Always think about what to do next first, like:

            - ...
            - ...
            - ...

            {...} // schema
        "#
    }
   ```

2. Compile and use:

   ```python
    from baml_client.sync_client import b
    from baml_client.types import Resume
    def example(raw_resume: str) -> Resume:
    # BAML's internal parser guarantees ExtractResume
    # to be always return a Resume type
    response = b.ExtractResume(raw_resume)
    return response
    def example_stream(raw_resume: str) -> Resume:
    stream = b.stream.ExtractResume(raw_resume)
    for msg in stream:
        print(msg) # This will be a PartialResume type

    # This will be a Resume type
    final = stream.get_final_response()
    return final
   ```

## Troubleshooting

### Frontend Issues

1. **WebSocket Connection Failing**

   - Check VITE_WS_URL in .env
   - Verify backend is running
   - Check browser console for errors

2. **Authentication Issues**
   - Clear local storage
   - Verify OAuth configuration
   - Check token expiration

### Backend Issues

1. **Channel Integration Failing**

   - Verify API credentials
   - Check rate limits
   - Review error logs

2. **BAML Issues**
   - Run `baml doctor` to check setup
   - Check prompt syntax and schema
   - Verify model-specific API keys if using external models
   - Run `baml compile` to ensure prompts are valid

## Deployment

### Production Checklist

1. Frontend:

   - Build optimization
   - Environment variables
   - SSL configuration

2. Backend:

   - Database migrations
   - Environment configuration
   - Service dependencies

3. Monitoring:
   - Logging setup
   - Error tracking
   - Performance monitoring

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [BAML Documentation](https://docs.boundaryml.com/guide/installation-language/python)
- [Slack API Documentation](https://api.slack.com/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
