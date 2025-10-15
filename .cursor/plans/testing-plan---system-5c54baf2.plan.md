<!-- 5c54baf2-e7d5-4f47-9817-d0fd7e312b81 55a529c9-ae14-4006-ac2b-aca49bf65e33 -->
# Testing Plan - Interactive Agent Chat System

## Overview

Test all implemented features from Phases 1-7 including backend core (authentication, sessions, WebSocket, BAML agent), frontend UI (chat interface, channels), Gmail API integration, Slack API integration, channel orchestration, and end-to-end flows.

## Pre-Testing Verification

### Check Implementation Status

**Backend Files to Verify:**

- `backend/src/api/routers/` - auth.py, chat.py, gmail.py, slack.py
- `backend/src/services/channels/` - base_channel.py, gmail_channel.py, slack_channel.py, slack_event_handler.py
- `backend/src/services/` - agent_service.py, session_service.py, channel_orchestrator.py, state_sync.py, rate_limiter.py, validation.py
- `backend/baml_src/chat_agent.baml` - BAML agent templates
- `backend/pyproject.toml` - All Phase 7 dependencies (google-auth, slack-sdk, jinja2, etc.)

**Frontend Files to Verify:**

- `frontend/src/components/channel/` - All 7 channel components
- `frontend/src/hooks/` - useWebSocket.ts, useSession.ts, useChannel.ts, etc.
- `frontend/src/pages/ChatPage.tsx` - Channel integration
- `frontend/package.json` - All dependencies installed

**Configuration to Create:**

- `backend/.env` - Environment variables (SECRET_KEY, GMAIL credentials, SLACK credentials, OPENAI_API_KEY)

## Phase 1: Environment Setup & Dependency Check

### Backend Setup (15 minutes)

1. **Verify Poetry Installation**

                                                                                                                                                                                                - Check Poetry version: `poetry --version`
                                                                                                                                                                                                - Expected: 1.5.0 or higher

2. **Install Backend Dependencies**

                                                                                                                                                                                                - Command: `cd backend && poetry install`
                                                                                                                                                                                                - Verify all Phase 7 dependencies installed:
                                                                                                                                                                                                                                                                                                                                - google-auth, google-auth-oauthlib, google-auth-httplib2
                                                                                                                                                                                                                                                                                                                                - google-api-python-client
                                                                                                                                                                                                                                                                                                                                - slack-sdk
                                                                                                                                                                                                                                                                                                                                - jinja2
                                                                                                                                                                                                                                                                                                                                - baml-py
                                                                                                                                                                                                                                                                                                                                - fastapi, uvicorn, pydantic

3. **Create .env File**

                                                                                                                                                                                                - Copy template or create new `.env` in backend/
                                                                                                                                                                                                - Add required values:
     ```env
     SECRET_KEY=your-secret-key-change-in-production
     DEBUG=true
     OPENAI_API_KEY=sk-...  # For BAML agent
     
     # Gmail (if testing Gmail)
     GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
     GMAIL_CLIENT_SECRET=your_client_secret
     GMAIL_REDIRECT_URI=http://localhost:8000/api/channels/gmail/callback
     
     # Slack (if testing Slack)
     SLACK_CLIENT_ID=your_slack_client_id
     SLACK_CLIENT_SECRET=your_slack_client_secret
     SLACK_SIGNING_SECRET=your_slack_signing_secret
     SLACK_REDIRECT_URI=http://localhost:8000/api/channels/slack/callback
     ```


4. **Generate BAML Client**

                                                                                                                                                                                                - Command: `cd backend && poetry run baml-cli generate`
                                                                                                                                                                                                - Verify: `backend/baml_client/` directory exists with Python files

5. **Test Backend Imports**

                                                                                                                                                                                                - Command: `poetry run python -c "from src.main import app; print('✅ Backend ready')"`
                                                                                                                                                                                                - Expected: No import errors

### Frontend Setup (10 minutes)

1. **Install Frontend Dependencies**

                                                                                                                                                                                                - Command: `cd frontend && npm install`
                                                                                                                                                                                                - Verify all dependencies installed (react, react-router-dom, @tanstack/react-query, lucide-react, etc.)

2. **Build Frontend**

                                                                                                                                                                                                - Command: `npm run build`
                                                                                                                                                                                                - Expected: Build succeeds without TypeScript or lint errors

3. **Check Frontend Types**

                                                                                                                                                                                                - Command: `npm run type-check` (if available) or build should catch type errors
                                                                                                                                                                                                - Expected: No type errors

## Phase 2: Backend Core Testing (30 minutes)

### Test 1: Server Startup

1. Start backend server:
   ```bash
   cd backend
   poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Verify endpoints accessible:

                                                                                                                                                                                                - http://localhost:8000/ - Root endpoint
                                                                                                                                                                                                - http://localhost:8000/health - Health check
                                                                                                                                                                                                - http://localhost:8000/docs - Swagger UI
                                                                                                                                                                                                - http://localhost:8000/redoc - ReDoc

3. Expected: All endpoints return 200 OK

### Test 2: Authentication Flow

**2.1 User Registration**

Request:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPassword123!"
  }'
```

Expected Response (201):

```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```

Save `access_token` for next tests.

**2.2 User Login**

Request:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPassword123!"
```

Expected: Same token response structure

**2.3 Get Current User**

Request:

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected Response (200):

```json
{
  "id": "user-uuid",
  "email": "test@example.com",
  "username": "testuser",
  "is_active": true,
  "created_at": "2025-10-15T..."
}
```

**2.4 Token Refresh**

Request:

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

Expected: New access token

### Test 3: Session Management via REST API

**3.1 List Sessions (should be empty)**

Request:

```bash
curl -X GET http://localhost:8000/api/sessions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected: `[]` (empty array)

### Test 4: WebSocket Connection

**4.1 WebSocket Basic Test**

Use a WebSocket client (e.g., websocat, browser console, or Postman):

```javascript
// Browser console test
const ws = new WebSocket('ws://localhost:8000/ws/test-user-id');

ws.onopen = () => {
  console.log('✅ Connected');
  
  // Start session
  ws.send(JSON.stringify({
    type: 'start_session',
    payload: { preferred_channel: 'websocket' }
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.error('❌ Error:', error);
};
```

Expected:

- Connection established
- Receive `session_started` message with session_id

**4.2 Send Message via WebSocket**

```javascript
// After session started
ws.send(JSON.stringify({
  type: 'message',
  payload: {
    content: 'Hello, agent!',
    stream: true
  }
}));
```

Expected:

- Receive `message_received` acknowledgment
- Receive `agent_status` with status "thinking"
- Receive streaming response chunks if BAML configured
- Agent state transitions: IDLE → THINKING → RESPONDING

**4.3 Rate Limit Status Check**

```javascript
ws.send(JSON.stringify({
  type: 'get_rate_limit_status',
  payload: {}
}));
```

Expected:

```json
{
  "type": "rate_limit_status",
  "payload": {
    "user": {
      "limit": 30,
      "remaining": 29,
      "reset_at": "2025-10-15T..."
    },
    "session": {
      "limit": 10,
      "remaining": 9,
      "reset_at": "2025-10-15T..."
    }
  }
}
```

**4.4 Ping/Pong Test**

```javascript
ws.send(JSON.stringify({ type: 'ping', payload: {} }));
```

Expected: Receive `pong` response

### Test 5: Rate Limiting

**5.1 Test User Rate Limit (30 req/min)**

Send 31 messages rapidly via WebSocket or REST API.

Expected:

- First 30 succeed
- 31st returns `rate_limit_exceeded` error
- Error includes `retry_after` timestamp

**5.2 Test Session Rate Limit (10 req/min)**

Similar to above but within single session.

Expected: Rate limit enforced after 10 requests

## Phase 3: Gmail Integration Testing (45 minutes)

### Prerequisites

1. **Google Cloud Console Setup** (one-time, 15 minutes)

                                                                                                                                                                                                - Go to https://console.cloud.google.com
                                                                                                                                                                                                - Create new project or select existing
                                                                                                                                                                                                - Enable Gmail API
                                                                                                                                                                                                - Create OAuth2 credentials (Web application)
                                                                                                                                                                                                - Add authorized redirect URI: `http://localhost:8000/api/channels/gmail/callback`
                                                                                                                                                                                                - Copy Client ID and Client Secret to `.env`

2. **Update Backend .env**
   ```env
   GMAIL_CLIENT_ID=123456789.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=GOCSPX-abcd1234
   GMAIL_REDIRECT_URI=http://localhost:8000/api/channels/gmail/callback
   ```

3. Restart backend server

### Test 6: Gmail OAuth2 Flow

**6.1 Initiate OAuth Flow**

Request:

```bash
curl -X GET http://localhost:8000/api/channels/gmail/auth \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected Response (200):

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

**6.2 Complete OAuth Flow**

1. Open `authorization_url` in browser
2. Sign in with Google account
3. Grant permissions (read/send email)
4. Browser redirects to callback URL
5. Backend processes callback and stores tokens

Expected:

- Browser shows success message or redirects
- Token stored in memory store

**6.3 Check Gmail Status**

Request:

```bash
curl -X GET http://localhost:8000/api/channels/gmail/status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected Response (200):

```json
{
  "connected": true,
  "email": "yourname@gmail.com",
  "last_connected": "2025-10-15T..."
}
```

### Test 7: Gmail Message Sending

**7.1 Send Test Email via Orchestrator**

This requires calling the orchestrator from backend code or creating a test endpoint.

Option A: Create test endpoint (temporary):

```python
# Add to backend/src/api/routers/gmail.py
@router.post("/test-send")
async def test_send_email(
    recipient: str,
    current_user: User = Depends(get_current_active_user)
):
    from src.services.channel_orchestrator import channel_orchestrator
    from src.models.base import Message, MessageType, MessageStatus, ChannelType
    import uuid
    from datetime import datetime, timezone
    
    message = Message(
        id=str(uuid.uuid4()),
        session_id="test-session",
        content="Test message from agent!",
        type=MessageType.AGENT,
        timestamp=datetime.now(timezone.utc),
        status=MessageStatus.SENT,
        channel=ChannelType.EMAIL,
        metadata=None
    )
    
    success = await channel_orchestrator.send_message(
        message=message,
        user_id=current_user.id,
        recipient=recipient,
        preferred_channel=ChannelType.EMAIL,
        enable_fallback=False
    )
    
    return {"success": success}
```

Request:

```bash
curl -X POST "http://localhost:8000/api/channels/gmail/test-send?recipient=test@example.com" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**7.2 Verify Email Received**

1. Check recipient inbox
2. Verify email received from your Gmail account
3. Check HTML formatting
4. Verify plain text fallback

Expected:

- Email delivered successfully
- HTML template rendered
- Contains message content

### Test 8: Gmail Disconnection

Request:

```bash
curl -X DELETE http://localhost:8000/api/channels/gmail/disconnect \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected:

- Tokens removed from memory store
- Status endpoint shows disconnected

## Phase 4: Slack Integration Testing (45 minutes)

### Prerequisites

1. **Slack App Setup** (one-time, 20 minutes)

                                                                                                                                                                                                - Go to https://api.slack.com/apps
                                                                                                                                                                                                - Create new app (from scratch)
                                                                                                                                                                                                - Add Bot Token Scopes:
                                                                                                                                                                                                                                                                                                                                - `chat:write` - Send messages
                                                                                                                                                                                                                                                                                                                                - `users:read` - Read user info
                                                                                                                                                                                                                                                                                                                                - `users:read.email` - Read user email
                                                                                                                                                                                                                                                                                                                                - `im:write` - Send DMs
                                                                                                                                                                                                                                                                                                                                - `im:history` - Read DM history
                                                                                                                                                                                                - Enable Event Subscriptions:
                                                                                                                                                                                                                                                                                                                                - Request URL: `http://your-domain/api/channels/slack/events`
                                                                                                                                                                                                                                                                                                                                - Subscribe to bot events: `message.im`
                                                                                                                                                                                                - Enable Interactivity:
                                                                                                                                                                                                                                                                                                                                - Request URL: `http://your-domain/api/channels/slack/interactions`
                                                                                                                                                                                                - Install app to workspace
                                                                                                                                                                                                - Copy Client ID, Client Secret, Signing Secret to `.env`

Note: For local testing, use ngrok to expose localhost:

   ```bash
   ngrok http 8000
   # Use the ngrok URL for webhook URLs
   ```

2. **Update Backend .env**
   ```env
   SLACK_CLIENT_ID=1234567890.1234567890
   SLACK_CLIENT_SECRET=abcd1234efgh5678
   SLACK_SIGNING_SECRET=xyz123
   SLACK_REDIRECT_URI=http://localhost:8000/api/channels/slack/callback
   ```

3. Restart backend server

### Test 9: Slack OAuth2 Flow

**9.1 Initiate OAuth Flow**

Request:

```bash
curl -X GET http://localhost:8000/api/channels/slack/auth \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected Response:

```json
{
  "authorization_url": "https://slack.com/oauth/v2/authorize?..."
}
```

**9.2 Complete OAuth Flow**

1. Open URL in browser
2. Sign in to Slack workspace
3. Authorize app
4. Browser redirects to callback
5. Backend processes and stores bot token

Expected:

- Success message or redirect
- Bot token stored in memory

**9.3 Check Slack Status**

Request:

```bash
curl -X GET http://localhost:8000/api/channels/slack/status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected Response:

```json
{
  "connected": true,
  "workspace": "Your Workspace",
  "bot_user_id": "U1234567890"
}
```

### Test 10: Slack Message Sending

**10.1 Send Test Message with Buttons**

Similar to Gmail, create test endpoint:

```python
# Add to backend/src/api/routers/slack.py
@router.post("/test-send")
async def test_send_slack(
    user_id: str,  # Slack user ID
    current_user: User = Depends(get_current_active_user)
):
    from src.services.channels.slack_channel import SlackChannel
    from src.models.base import Message, MessageType, MessageStatus, ChannelType
    import uuid
    from datetime import datetime, timezone
    
    slack_channel = SlackChannel()
    
    message = Message(
        id=str(uuid.uuid4()),
        session_id="test-session",
        content="Test message from agent! Please click a button.",
        type=MessageType.AGENT,
        timestamp=datetime.now(timezone.utc),
        status=MessageStatus.SENT,
        channel=ChannelType.SLACK,
        metadata=None
    )
    
    success = await slack_channel.send_message(
        message=message,
        recipient=user_id,
        user_id=current_user.id
    )
    
    return {"success": success}
```

Request:

```bash
curl -X POST "http://localhost:8000/api/channels/slack/test-send?user_id=U1234567890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**10.2 Verify Slack Message**

1. Check Slack DMs from bot
2. Verify message received
3. Check Block Kit formatting
4. Verify interactive buttons present

Expected:

- Message delivered to Slack DM
- Block Kit formatted
- Interactive buttons work

**10.3 Test Interactive Buttons**

1. Click "Approve" or "Reject" button in Slack
2. Backend receives interaction webhook
3. Backend processes interaction
4. Slack message updated

Expected:

- Button click registered
- Backend logs interaction
- Message updated in Slack

### Test 11: Slack Event Handling

**11.1 Send Message to Bot**

1. In Slack, send a direct message to the bot
2. Backend receives event via webhook
3. Backend processes event

Expected:

- Event received at `/api/channels/slack/events`
- Signature verified
- Event processed and logged

Check backend logs for event processing

## Phase 5: Channel Orchestration Testing (30 minutes)

### Test 12: Channel Fallback

**12.1 Test Automatic Fallback**

1. Disconnect primary channel (e.g., WebSocket)
2. Send message via orchestrator
3. Verify fallback to secondary channel

Expected:

- Orchestrator tries primary channel
- Detects failure
- Falls back to Email or Slack
- Message delivered via fallback channel
- Delivery attempt logged

**12.2 Test Circuit Breaker**

1. Cause 5 consecutive failures on one channel
2. Send 6th message
3. Verify circuit opens

Expected:

- First 5 attempts try the channel
- After 5 failures, circuit breaker opens
- 6th attempt skips failed channel immediately
- Falls back to next available channel

**12.3 Test Circuit Recovery**

1. Wait for recovery timeout
2. Send message
3. Verify circuit half-open

Expected:

- Circuit enters half-open state
- Tries one test request
- If success, circuit closes
- If failure, circuit re-opens

### Test 13: Priority-Based Routing

**13.1 Test Channel Priority**

1. Configure channel priorities (WebSocket > Slack > Email)
2. Make all channels available
3. Send message

Expected:

- Orchestrator selects highest priority available channel
- Message sent via WebSocket

**13.2 Test with Unavailable Channels**

1. Make WebSocket unavailable
2. Send message

Expected:

- Skips WebSocket
- Uses next priority (Slack)
- Message delivered

### Test 14: State Synchronization

**14.1 Test Cross-Channel Message History**

1. Send message via WebSocket
2. Query message history via REST API
3. Switch to Email channel
4. Send message via Email
5. Query history again

Expected:

- All messages in single history
- Regardless of channel used
- Chronological order maintained

**14.2 Test Feedback First-Response-Wins**

1. Create feedback request
2. Send to multiple channels (Email + Slack)
3. Respond via Slack
4. Try to respond via Email

Expected:

- Slack response accepted and processed
- Email response rejected (already processed)
- Feedback request marked complete

## Phase 6: Frontend Testing (30 minutes)

### Test 15: Frontend Startup

1. Start frontend dev server:
   ```bash
   cd frontend
   npm run dev
   ```

2. Open browser to http://localhost:5173

Expected:

- App loads without errors
- Login page displayed
- No console errors

### Test 16: Frontend Authentication

**16.1 Register**

1. Navigate to register page
2. Fill in form (email, username, password)
3. Submit

Expected:

- Registration succeeds
- Redirected to chat page or dashboard
- Token stored in localStorage

**16.2 Login**

1. Logout if logged in
2. Go to login page
3. Enter credentials
4. Submit

Expected:

- Login succeeds
- Redirected to chat page
- Token stored

### Test 17: Chat Interface

**17.1 Start Chat Session**

1. Open chat page
2. Verify UI components load:

                                                                                                                                                                                                - Message list
                                                                                                                                                                                                - Input box
                                                                                                                                                                                                - Channel selector
                                                                                                                                                                                                - Session status
                                                                                                                                                                                                - Connection status

Expected:

- All components render
- WebSocket connects automatically
- Connection status shows "Connected"

**17.2 Send Message**

1. Type message in input box
2. Press Enter or click Send

Expected:

- Message appears in chat
- Agent thinking indicator appears
- Agent response streams in
- Rate limit indicator updates

**17.3 Check Rate Limit Display**

Expected:

- Rate limit status visible in UI
- Shows remaining requests
- Updates after each message
- Warning appears when limit approaching

### Test 18: Channel Management UI

**18.1 Channel Selector**

1. Click channel selector dropdown
2. Verify all channels listed:

                                                                                                                                                                                                - Chat (WebSocket)
                                                                                                                                                                                                - Email
                                                                                                                                                                                                - Slack

Expected:

- All channels with status badges
- Connected channels enabled
- Disconnected channels disabled

**18.2 Switch Channel**

1. Select different channel (e.g., Email)
2. Verify preference changes

Expected:

- Channel changes in UI
- WebSocket sends channel change message
- Session status updates

**18.3 Channel Status View**

1. Open channel status section
2. Verify status for each channel

Expected:

- Real-time status for all channels
- Error messages if any
- Last active timestamps
- Retry buttons for failed channels

**18.4 Channel Settings**

1. Open channel settings dialog
2. Configure priorities
3. Set retry limits
4. Save

Expected:

- Settings saved
- Applied to future messages
- UI updates immediately

### Test 19: Fallback Notifications

**19.1 Simulate Channel Failure**

1. Disconnect WebSocket (close tab or disconnect network briefly)
2. Send message
3. Verify fallback alert appears

Expected:

- Alert shows channel switch
- Shows previous and current channel
- Countdown for retry
- Manual retry button available

**19.2 Test Reconnection UI**

1. Network disconnected
2. UI shows reconnecting indicator
3. Network restored

Expected:

- Reconnecting progress bar
- Attempt count displayed
- Success notification on reconnection

## Phase 7: End-to-End Integration Testing (45 minutes)

### Test 20: Complete User Journey - WebSocket Channel

1. Register/login to app
2. Start chat session
3. Send message: "Hello"
4. Receive agent response
5. Send follow-up: "What can you help with?"
6. Receive response
7. Check message history
8. End session

Expected:

- Smooth flow from start to finish
- All messages persisted
- Agent responses contextual
- No errors

### Test 21: Complete User Journey - Email Channel

1. Login to app
2. Connect Gmail account via OAuth
3. Change preferred channel to Email
4. Send message
5. Check email inbox for agent response
6. Verify HTML formatting
7. Check message history in app

Expected:

- Email delivered
- HTML template rendered correctly
- Message appears in history
- Context preserved

### Test 22: Complete User Journey - Slack Channel

1. Login to app
2. Connect Slack workspace via OAuth
3. Change preferred channel to Slack
4. Send message
5. Check Slack DMs for agent message
6. Interact with buttons if present
7. Check message history in app

Expected:

- Slack message received
- Block Kit formatting correct
- Buttons functional
- Interaction tracked

### Test 23: Multi-Channel Feedback Flow

1. Start session via WebSocket
2. Agent sends feedback request
3. Request delivered to Email AND Slack
4. Respond via Slack (click button)
5. Verify Email response link no longer works

Expected:

- Feedback request in both channels
- First response wins (Slack)
- Email response rejected
- Session resumes
- Agent acknowledges feedback

### Test 24: Channel Failover Scenario

1. Start chat session
2. Send message
3. Kill backend server (simulate crash)
4. Frontend shows reconnecting
5. Restart backend
6. Frontend reconnects
7. Send message
8. If WebSocket fails, falls back to Email/Slack

Expected:

- Graceful handling of failures
- Automatic reconnection
- Fallback works correctly
- No message loss
- Context preserved

## Phase 8: Load & Performance Testing (Optional, 30 minutes)

### Test 25: Rate Limiting Under Load

1. Use tool like `hey` or `ab` to send many requests
2. Verify rate limiting kicks in
3. Check rate limit headers
```bash
# Install hey: go install github.com/rakyll/hey@latest
hey -n 100 -c 10 -m POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPassword123!"
```


Expected:

- First 30 requests succeed (per user limit)
- Subsequent requests return 429
- Rate limit headers present

### Test 26: Concurrent WebSocket Connections

1. Open 10 browser tabs
2. Connect WebSocket in each
3. Send messages from all tabs

Expected:

- All connections maintained
- Rate limiting enforced per session
- No cross-talk between sessions

### Test 27: Channel Orchestrator Performance

1. Send 100 messages rapidly
2. Verify orchestrator handles load
3. Check circuit breaker doesn't trip

Expected:

- All messages processed
- Appropriate channel selection
- No circuit breaker false positives

## Success Criteria

All tests should meet these criteria:

### Backend

- ✅ Server starts without errors
- ✅ All API endpoints respond correctly
- ✅ Authentication works (register, login, refresh)
- ✅ Rate limiting enforces all 3 levels
- ✅ WebSocket connections stable
- ✅ Session management functional

### Gmail Integration

- ✅ OAuth2 flow completes successfully
- ✅ Emails send with HTML templates
- ✅ Gmail API calls succeed
- ✅ Token refresh works
- ✅ Connection status accurate

### Slack Integration

- ✅ OAuth2 flow completes successfully
- ✅ Messages send with Block Kit
- ✅ Interactive buttons work
- ✅ Webhooks receive events
- ✅ Signature verification passes

### Channel Orchestration

- ✅ Fallback mechanism works
- ✅ Circuit breaker prevents repeated failures
- ✅ Priority routing correct
- ✅ Delivery tracking accurate
- ✅ State sync consistent

### Frontend

- ✅ App loads without errors
- ✅ Authentication UI works
- ✅ Chat interface functional
- ✅ Channel selector works
- ✅ Real-time updates display
- ✅ Fallback alerts appear
- ✅ Responsive on mobile/desktop

### Integration

- ✅ End-to-end flows complete
- ✅ No message loss
- ✅ Context preserved across channels
- ✅ First-response-wins works
- ✅ Graceful error handling

## Test Report Template

After testing, document results:

```markdown
# Test Execution Report

**Date:** YYYY-MM-DD
**Tester:** Your Name
**Duration:** X hours

## Summary
- Total Tests: XX
- Passed: XX
- Failed: XX
- Skipped: XX

## Environment
- OS: 
- Python:
- Node:
- Backend URL:
- Frontend URL:

## Test Results

### Backend Core
- [ ] Test 1: Server Startup - PASS/FAIL
- [ ] Test 2: Authentication - PASS/FAIL
...

### Issues Found
1. Issue description
   - Severity: High/Medium/Low
   - Steps to reproduce
   - Expected vs Actual

## Recommendations
- List of improvements or fixes needed
```

## Notes

- Some tests require external services (Gmail, Slack) to be configured
- Use test accounts for Gmail and Slack (not production)
- Circuit breaker may need time to reset between tests
- Rate limits reset after 60 seconds
- Backend uses in-memory storage (data lost on restart)
- For webhook testing (Slack events), use ngrok or similar tunnel

### To-dos

- [ ] Verify environment setup: check Poetry, Node, dependencies, and create .env file
- [ ] Test backend core features: server startup, authentication, sessions, WebSocket, rate limiting
- [ ] Set up Gmail API credentials in Google Cloud Console and configure OAuth2
- [ ] Test Gmail integration: OAuth flow, message sending, status checks, disconnection
- [ ] Set up Slack App with bot scopes, webhooks, and configure OAuth2
- [ ] Test Slack integration: OAuth flow, message sending, interactive buttons, events
- [ ] Test channel orchestration: fallback mechanism, circuit breaker, priority routing, state sync
- [ ] Test frontend UI: startup, authentication, chat interface, channel management, notifications
- [ ] Run end-to-end integration tests for all channels and multi-channel scenarios
- [ ] Document test results, issues found, and recommendations in test report