# Implementation Plan: Interactive Agent Chat System

## Technical Context

### Frontend Stack

- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Component Library**: shadcn/ui
- **Router**: React Router
- **API Client**: TanStack Query (React Query)
- **State Management**: TanStack Query + React Context (for UI state)

### Backend Stack

- **Framework**: FastAPI
- **Data Validation**: Pydantic
- **Configuration**: python-dotenv
- **Prompt Management**: BAML
- **Real-time**: WebSocket support via FastAPI's WebSocket
- **Authentication**: OAuth2 with JWT implementation using FastAPI security features:
  - OAuth2 authorization flow with JWT token issuance
  - FastAPI OAuth2 password bearer with JWT tokens
  - Secure token refresh and revocation endpoints
  - Cross-channel token synchronization middleware

### External Services Integration

- Gmail API for email channel (OAuth2 integration)
- Slack API for Slack channel (OAuth2 integration)
- BAML for prompt management and agent orchestration

### Infrastructure Requirements

1. WebSocket server capability for real-time chat
2. Message queue system for handling channel failures
3. Data persistence layer for conversation state
4. OAuth2 authentication server with:
   - JWT token management
   - Token refresh mechanism
   - Cross-channel state synchronization
   - Rate limiting for auth requests

## Constitution Check

### Security Requirements

- [x] OAuth2 with JWT for authentication (FR-017)
- [x] Encrypted communications in transit (FR-019)
- [x] Secure session state across channels (FR-018)
- [x] Rate limiting implementation (FR-020)

### Performance Requirements

- [x] Chat message response < 100ms
- [x] Status updates < 500ms
- [x] Channel switching < 1s
- [x] 99.9% uptime target
- [x] Rate limit: 30 req/min/user

### Reliability Requirements

- [x] Zero context loss during channel switches
- [x] 100% feedback request delivery
- [x] 99.9% channel failover success
- [x] Exponential backoff for failures

## Phase 0: Research Tasks

1. **WebSocket Implementation**

   - FastAPI WebSocket best practices
   - React WebSocket integration patterns
   - Handling reconnection logic

2. **Channel Integration**

   - Gmail API authentication and SDK usage
   - Slack API bot setup and permissions
   - Channel fallback implementation patterns

3. **State Management**

   - TanStack Query optimization for real-time data
   - Cross-channel state synchronization
   - Conversation context preservation

4. **Authentication Flow**

   - OAuth2 implementation with FastAPI:
     - Standard OAuth2 password flow
     - OAuth2 authorization code flow for external services
     - FastAPI security dependency injection
   - JWT token management:
     - Token generation and validation
     - Automatic refresh mechanism
     - Secure storage and transmission
   - Cross-channel auth state maintenance:
     - Synchronized session management
     - Consistent token validation
     - State recovery mechanisms

5. **BAML Integration**
   - BAML setup and configuration
   - Prompt management patterns
   - Agent state handling

## Phase 1: Core Components

### Data Model

- Entities defined in data-model.md
- State machines for session/channel management
- API contract specifications

### Frontend Architecture

1. **Core Components**

   ```typescript
   src/
     components/
       session/
         ChatSession.tsx       # Main session container
         MessageList.tsx       # Message history display
         MessageInput.tsx      # Message composition
         SessionStatus.tsx     # Session state indicator
       feedback/
         FeedbackRequest.tsx   # Feedback request display
         FeedbackResponse.tsx  # Response input/display
       channel/
         ChannelSelector.tsx   # Channel preference UI
         ChannelStatus.tsx     # Channel state indicator
       agent/
         AgentStatus.tsx       # Agent state display
         ThinkingIndicator.tsx # Agent processing indicator
       common/
         LoadingStates.tsx     # Shared loading states
     hooks/
       useSession.ts          # ChatSession management
       useMessage.ts          # Message operations
       useFeedback.ts         # Feedback handling
       useChannel.ts          # Channel management
       useAgent.ts            # Agent state management
       useWebSocket.ts        # WebSocket connection
     services/
       api.ts                 # API client
       websocket.ts           # WebSocket client
       channel-manager.ts     # Channel orchestration
     stores/
       session-store.ts       # Session state management
       agent-store.ts         # Agent state management
     types/
       models.ts             # Shared type definitions
   ```

   UI Component Placement: All new components from the shadcn library must be added to `frontend\src\components\ui`. Do not create a new folder for newly added shadcn components.

   Use `ComponentRef<T>` instead of `React.ElementRef` when working with component references.

2. **API Layer**
   ```typescript
   src/
     services/
       queries/
         useSession.ts         # ChatSession queries
         useMessages.ts        # Message queries
         useFeedbackRequest.ts # FeedbackRequest queries
         useAgentState.ts     # AgentState queries
         useChannels.ts       # CommunicationChannel queries
       mutations/
         useSessionMutation.ts      # Session operations
         useMessageMutation.ts      # Message operations
         useFeedbackMutation.ts     # Feedback operations
         useChannelMutation.ts      # Channel operations
   ```

### Backend Architecture

1. **Core Components**

   ```python
   src/
     api/
       routers/
         chat.py
         feedback.py
         channels.py
       websocket/
         manager.py
         connection.py
     services/
       chat_service.py
       feedback_service.py
       channel_service.py
     models/
       chat_session.py      # ChatSession model with SessionStatus enum
       message.py          # Message model with MessageType and MessageStatus enums
       feedback_request.py # FeedbackRequest model with FeedbackType and FeedbackStatus enums
       feedback_response.py # FeedbackResponse model
       agent_state.py     # AgentState model with AgentStatus enum
       communication_channel.py # CommunicationChannel model with ChannelType and ChannelStatus enums
       base.py           # Shared base models and utilities
   ```

2. **Service Layer**
   ```python
   services/
     session/
       session_manager.py   # Manages ChatSession lifecycle
       message_handler.py   # Handles Message operations
       state_manager.py    # Manages AgentState
     feedback/
       request_handler.py   # Manages FeedbackRequest lifecycle
       response_handler.py  # Handles FeedbackResponse processing
     channels/
       base_handler.py     # Abstract base channel handler
       chat_handler.py     # WebSocket chat implementation
       email_handler.py    # Gmail API integration
       slack_handler.py    # Slack API integration
       channel_manager.py  # CommunicationChannel orchestration
     agent/
       prompt_manager.py   # BAML prompt management
       context_manager.py  # Agent context preservation
   ```

## Phase 2: Implementation Strategy

### Stage 1: Foundation (Sprint 1)

1. Basic project setup (Vite + FastAPI)
2. Authentication implementation
3. WebSocket infrastructure
4. Basic chat interface

### Stage 2: Core Features (Sprint 2)

1. Real-time chat with streaming
2. Agent state management
3. Basic channel integration
4. Message persistence

### Stage 3: Channel Integration (Sprint 3)

1. Gmail integration
2. Slack integration
3. Channel fallback logic
4. Cross-channel state sync

### Stage 4: Agent Intelligence (Sprint 4)

1. BAML integration
2. Prompt management
3. Feedback workflow
4. State preservation

### Stage 5: Polish (Sprint 5)

1. UI/UX refinement
2. Performance optimization
3. Error handling
4. Testing & documentation

## Technical Decisions

1. **WebSocket Choice**: FastAPI's built-in WebSocket support

   - Rationale: Native integration, good performance
   - Alternative: Socket.IO (rejected due to overhead)

2. **State Management**: TanStack Query + Context

   - Rationale: Built-in caching, real-time updates
   - Alternative: Redux (rejected for simplicity)

3. **Channel Management**: Custom abstraction layer

   - Rationale: Unified interface for all channels
   - Alternative: Separate handlers (rejected for maintainability)

4. **Authentication**: FastAPI + JWT
   - Rationale: Built-in security, standard approach
   - Alternative: Session-based (rejected for scalability)

## Risk Assessment

1. **High Risk**

   - Cross-channel state synchronization
   - Real-time performance at scale
   - Channel failure handling

2. **Medium Risk**

   - OAuth2 token management
   - Prompt optimization
   - Rate limiting accuracy

3. **Low Risk**
   - UI component implementation
   - Basic API integration
   - Configuration management

## Success Metrics

1. **Performance**

   - Chat response time < 100ms
   - Channel switch time < 1s
   - Rate limit violations < 0.1%

2. **Reliability**

   - Uptime > 99.9%
   - Zero context loss
   - 100% feedback delivery

3. **User Experience**
   - 95% interface intuitiveness
   - 90% task completion
   - < 1% error rate

## Dependencies & Setup

### Frontend Dependencies

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.90.2",
    "@types/react": "^19.2.2",
    "react-router-dom": "^7.9.4",
    "tailwindcss": "^4.1.14",
    "shadcn-ui": "^0.9.5"
  }
}
```

### Backend Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.13.3"
fastapi = "^0.119.0"
pydantic = "^2.12.0"
python-dotenv = "^1.1.1"
baml = "^0.211.2"
websockets = "^15.0.1"
```
