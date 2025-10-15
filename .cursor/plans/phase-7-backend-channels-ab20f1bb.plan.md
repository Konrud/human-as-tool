<!-- ab20f1bb-c5ee-499d-9d6b-cc4fa278054c 6b4ee7fa-9553-44e3-95fd-2f03d7fb9416 -->
# Phase 7: Backend Channel Integration

## Overview

Implement Phase 7 (T022-T025) from the project plan, adding full-featured channel integration for Gmail and Slack with OAuth2 authentication, webhook handlers, channel orchestration with intelligent fallback, and cross-channel state synchronization. All features will use the existing in-memory storage from Phase 6.

## Tasks from specs/001-interactive-agent-chat/plan/tasks.md

### T022: Gmail Integration (Implement Gmail integration)

### T023: Slack Integration (Implement Slack integration)

### T024: Channel Orchestration (Create channel orchestration)

### T025: Cross-Channel Sync (Implement cross-channel sync)

## Implementation Details

### 1. Gmail API Integration (T022)

**Create `backend/src/services/channels/base_channel.py`:**

- Abstract base class for all channel handlers
- Define common interface: `send_message()`, `request_feedback()`, `check_health()`
- Error handling and retry logic base
- Channel status management
- Rate limiting per channel

**Create `backend/src/services/channels/gmail_channel.py`:**

- Gmail API client initialization with OAuth2
- OAuth2 token management (stored in user model)
- Send email functionality with HTML templates
- Receive email via Gmail API polling or Pub/Sub
- Parse email responses and link to feedback requests
- Email template system for agent messages and feedback requests
- Handle delivery failures with retry
- Track message threading (conversation continuity)

**Create `backend/src/api/routers/gmail.py`:**

- `GET /api/channels/gmail/auth` - Initiate OAuth2 flow
- `GET /api/channels/gmail/callback` - OAuth2 callback handler
- `POST /api/channels/gmail/webhook` - Gmail push notifications (optional)
- `GET /api/channels/gmail/status` - Connection status check
- Token refresh endpoints

**Files to create:**

- `backend/src/services/channels/__init__.py`
- `backend/src/services/channels/base_channel.py`
- `backend/src/services/channels/gmail_channel.py`
- `backend/src/api/routers/gmail.py`
- `backend/src/templates/email/` - Email HTML templates

**Dependencies to add:**

- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `google-api-python-client`

### 2. Slack API Integration (T023)

**Create `backend/src/services/channels/slack_channel.py`:**

- Slack Bot client initialization with OAuth2
- OAuth2 flow for workspace installation
- Send direct message functionality
- Interactive message buttons for feedback (approve/reject)
- Receive Slack events via webhook
- Parse button interactions and link to feedback requests
- Handle Slack rate limiting (Tier 3 limits)
- Message formatting for Slack markdown

**Create `backend/src/api/routers/slack.py`:**

- `GET /api/channels/slack/auth` - Initiate OAuth2 flow
- `GET /api/channels/slack/callback` - OAuth2 callback handler
- `POST /api/channels/slack/events` - Slack events webhook
- `POST /api/channels/slack/interactions` - Slack interactive components
- `GET /api/channels/slack/status` - Connection status check

**Files to create:**

- `backend/src/services/channels/slack_channel.py`
- `backend/src/api/routers/slack.py`
- `backend/src/services/channels/slack_event_handler.py` - Event processing

**Dependencies to add:**

- `slack-sdk`

### 3. Channel Orchestration (T024)

**Create `backend/src/services/channel_orchestrator.py`:**

- Central channel manager and router
- Channel selection logic based on user preference
- Intelligent fallback mechanism:
  - Try primary channel (user preference)
  - If fails, try secondary channels by priority
  - Track channel health and availability
  - Circuit breaker pattern for failing channels
- Retry logic with exponential backoff
- Channel-specific rate limiting enforcement
- Queue messages for offline channels
- Message delivery tracking across all channels

**Update `backend/src/storage/memory_store.py`:**

- Add channel connection storage (tokens, status)
- Add message delivery queue
- Add channel health metrics
- Track retry attempts per channel

**Update `backend/src/models/base.py`:**

- Add `ChannelConnection` model for OAuth tokens
- Add `DeliveryAttempt` model for tracking
- Enhance `CommunicationChannel` with health metrics

**Files to create/modify:**

- `backend/src/services/channel_orchestrator.py` (new)
- `backend/src/storage/memory_store.py` (modify - add channel connection storage)
- `backend/src/models/base.py` (modify - add channel models)

### 4. Cross-Channel State Synchronization (T025)

**Create `backend/src/services/state_sync.py`:**

- Synchronize conversation state across channels
- Maintain consistent message history regardless of channel
- Track feedback requests across all channels
- Handle "first valid response wins" from any channel
- Update session state when channel switches
- Notify all connected channels of state changes
- Preserve context when switching mid-conversation

**Update `backend/src/api/websocket/connection.py`:**

- Integrate channel orchestrator
- Handle channel switch requests
- Broadcast state updates to WebSocket clients
- Support channel preference updates

**Update `backend/src/services/session_service.py`:**

- Add channel switching functionality
- Track which channels have been used
- Store channel-specific metadata
- Link messages to delivery attempts

**Files to create/modify:**

- `backend/src/services/state_sync.py` (new)
- `backend/src/api/websocket/connection.py` (modify)
- `backend/src/services/session_service.py` (modify)

### 5. Integration and Testing

**Update `backend/src/main.py`:**

- Add Gmail and Slack routers
- Initialize channel orchestrator
- Add webhook endpoints

**Create integration tests:**

- `backend/tests/test_gmail_channel.py` - Gmail integration tests
- `backend/tests/test_slack_channel.py` - Slack integration tests
- `backend/tests/test_channel_orchestrator.py` - Orchestration tests
- `backend/tests/test_state_sync.py` - State sync tests

**Create documentation:**

- `backend/PHASE-7-COMPLETE.md` - Implementation summary
- Update `backend/README.md` with channel setup instructions

## File Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── gmail.py          ✅ Gmail OAuth & webhooks
│   │   │   ├── slack.py          ✅ Slack OAuth & webhooks
│   │   │   └── (existing files)
│   ├── services/
│   │   ├── channels/
│   │   │   ├── __init__.py       ✅ Channel exports
│   │   │   ├── base_channel.py   ✅ Abstract base
│   │   │   ├── gmail_channel.py  ✅ Gmail handler
│   │   │   ├── slack_channel.py  ✅ Slack handler
│   │   │   └── slack_event_handler.py ✅ Slack events
│   │   ├── channel_orchestrator.py ✅ Central orchestration
│   │   ├── state_sync.py         ✅ State synchronization
│   │   └── (existing services)
│   ├── templates/
│   │   └── email/
│   │       ├── agent_message.html    ✅ Agent message template
│   │       ├── feedback_request.html ✅ Feedback template
│   │       └── base.html             ✅ Base template
│   └── (existing structure)
├── tests/
│   ├── test_gmail_channel.py     ✅ Gmail tests
│   ├── test_slack_channel.py     ✅ Slack tests
│   ├── test_channel_orchestrator.py ✅ Orchestration tests
│   └── test_state_sync.py        ✅ Sync tests
└── PHASE-7-COMPLETE.md           ✅ Documentation
```

## Configuration Updates

The existing `backend/src/config.py` already has placeholders for Gmail and Slack credentials. Users need to add to `.env`:

```env
# Gmail Integration
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/channels/gmail/callback

# Slack Integration
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_REDIRECT_URI=http://localhost:8000/api/channels/slack/callback
```

## Success Criteria

- Gmail OAuth2 flow completes successfully
- Slack OAuth2 flow completes and installs bot
- Agent messages deliver via email with proper formatting
- Agent messages deliver via Slack DM with proper formatting
- Feedback requests send via both channels with response tracking
- Email replies link back to correct feedback request
- Slack button interactions link back to correct feedback request
- Channel fallback works (websocket → email → slack)
- Circuit breaker prevents repeated calls to failing channels
- Cross-channel state remains consistent
- Message history preserved across channel switches
- First valid response wins logic works across all channels
- Rate limiting enforced per-channel
- Channel health monitoring reports accurate status
- Exponential backoff implemented for retries
- Integration tests pass for all channels

## Implementation Order

1. **Base Channel Infrastructure** - Abstract base class
2. **Gmail Integration** - OAuth, sending, receiving
3. **Slack Integration** - OAuth, sending, receiving  
4. **Channel Orchestrator** - Routing and fallback
5. **State Sync** - Cross-channel synchronization
6. **Testing** - Integration tests for all components
7. **Documentation** - Complete Phase 7 docs

## Key Implementation Notes

- Use existing `ChannelType`, `ChannelStatus` enums from `backend/src/models/base.py`
- Leverage existing rate limiting from `backend/src/services/rate_limiter.py`
- Integrate with `backend/src/services/session_service.py` for session management
- Use `backend/src/storage/memory_store.py` for all storage
- OAuth tokens stored in user model extensions
- Email templates use Jinja2 for rendering
- Slack uses Block Kit for rich messages
- All async operations use FastAPI's async capabilities
- Error handling follows existing patterns in Phase 6
- Validation uses `backend/src/services/validation.py` patterns

## Dependencies to Install

```bash
cd backend
poetry add google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client slack-sdk jinja2
```

### To-dos

- [ ] Create base channel abstract class with common interface and error handling
- [ ] Implement Gmail OAuth2 flow and token management
- [ ] Implement Gmail message sending and email template system
- [ ] Implement Slack OAuth2 flow and bot installation
- [ ] Implement Slack messaging with interactive buttons and event handlers
- [ ] Create channel orchestrator with routing, fallback, and circuit breaker logic
- [ ] Implement cross-channel state synchronization and message history preservation
- [ ] Write integration tests for all channel components and orchestration
- [ ] Create Phase 7 completion documentation and update README