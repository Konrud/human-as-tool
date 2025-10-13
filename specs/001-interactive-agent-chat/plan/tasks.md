# Implementation Tasks: Interactive Agent Chat System

## Phase 1: Frontend Setup

### Development Environment

T001. Configure VS Code settings

- Add recommended extensions
- Set up TypeScript analysis configuration
- Configure Prettier and ESLint

### Frontend Project Initialization

T002. [P] Initialize frontend project structure

- Set up Vite with React and TypeScript
- Install core dependencies (React, TypeScript, TanStack Query)
- Configure environment files
- Set up data validation:
  - Install and configure Zod for runtime type validation
  - Create TypeScript interfaces matching data model
  - Implement shared validation schemas
  - Add validation error handling utilities

T003. [P] Set up shadcn/ui framework with mobile-first configuration

- Install and configure shadcn/ui
- Set up tailwind.css with mobile-first breakpoints
- Configure component themes and styling
- Set up responsive design system variables
- Configure touch-friendly component defaults

T004. [P] Set up frontend authentication

- Implement OAuth2 client configuration
- Set up JWT token management
- Create protected route handlers

## Phase 2: Frontend Core Features [US1]

### Chat Interface Components

T005. [P] Create mobile-first chat layout components

- Implement mobile-first responsive layout with shadcn/ui
- Create chat container using Card component with mobile-optimized spacing
- Set up dark/light theme support
- Implement touch-friendly gesture controls
- Add responsive breakpoints (mobile → tablet → desktop)
- Ensure minimum touch target sizes (44px)

T006. [P] Build mobile-optimized message components

- Create message list using shadcn/ui ScrollArea with touch scrolling
- Implement message bubbles with responsive sizing and Avatar component
- Add message timestamp and status indicators
- Optimize tap targets for touch interaction
- Implement swipe gestures for message actions
- Add responsive spacing based on device size

T007. [P] Create mobile-friendly input components

- Implement message input using shadcn/ui Input with virtual keyboard support
- Add command palette using cmdk with touch-optimized UI
- Create typing indicators
- Handle soft keyboard appearance and viewport adjustments
- Implement responsive input sizing and padding
- Add haptic feedback for touch interactions

### Real-Time Features

T008. [P] Implement WebSocket client

- Create WebSocket hook
- Set up connection management
- Implement reconnection logic

T009. Implement real-time message streaming

- Create streaming message display
- Add typing animation effects
- Implement progress indicators

T010. [P] Add chat status and rate limit components

- Create status bar using shadcn/ui Alert
- Implement thinking state display
- Add connection status indicators
- Add rate limit status display:
  - Show request quota progress bar
  - Display remaining requests count
  - Add rate limit warning toasts
  - Show retry countdown timers
  - Implement graceful degradation UI

## Phase 3: Frontend User Interaction [US2]

### Pause/Resume Interface

T011. [P] Create pause state components

- Implement pause status using shadcn/ui Alert
- Add approval pending display
- Create resume state indicators

T012. [P] Build interaction components

- Implement action buttons using shadcn/ui Button
- Create state transition animations
- Add user feedback tooltips

## Phase 4: Frontend Channel Management [US3, US4]

### Channel Interface

T013. [P] Create responsive channel selection components

- Implement channel selector using shadcn/ui Select with touch-friendly dropdowns
- Add channel status badges with adaptive sizing
- Create mobile-first preference management UI
- Implement bottom sheet for mobile channel selection
- Add responsive grid/list view based on screen size
- Ensure touch-friendly spacing between options

T014. [P] Build channel feedback interface

- Create feedback forms using shadcn/ui Form
- Implement response handling UI
- Add timeout indicators

### Channel Fallback UI

T015. [P] Implement channel fallback components

- Create fallback notification alerts
- Implement channel switch UI
- Add reconnection status display

## Phase 5: Backend Setup

### Backend Environment

T016. [P] Initialize backend project structure

- Set up FastAPI with Poetry
- Install core dependencies
- Configure environment files

T017. [P] Set up BAML framework

- Initialize BAML project structure
- Configure BAML settings
- Set up agent templates

T018. Configure backend authentication

- Set up OAuth2 with FastAPI
- Implement JWT backend support
- Configure security middleware

## Phase 6: Backend Core Features

### Agent Infrastructure

T019. [P] Implement BAML agent setup

- Create base agent configuration
- Set up agent state management
- Implement prompt templates

T020. [P] Create WebSocket handler with comprehensive rate limiting

- Implement WebSocket connection manager
- Add message routing system
- Configure multi-level rate limiting:
  - Implement token bucket algorithm for 30 req/min per user
  - Add per-session limit of 10 req/min
  - Add per-channel limit of 20 req/min
  - Track limits across reconnections using user ID
  - Implement in-memory rate limiting with persistence
  - Add distributed rate limit synchronization via database
- Implement rate limit error handling:
  - Add standardized rate limit error responses
  - Implement graceful request queuing with priorities
  - Add exponential backoff (1s initial, doubling up to 1h max, max 10 attempts)
  - Implement rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
  - Add WebSocket-specific error codes for rate limits
- Create rate limit monitoring:
  - Track rate limit violations per user/session
  - Monitor queue lengths and backoff states
  - Log rate limit events for analysis
  - Create rate limit dashboards
- Implement client-side handling:
  - Add automatic request throttling
  - Implement client-side rate tracking
  - Show remaining quota in UI
  - Display user-friendly limit warnings
  - Add automatic retry with backoff

T021. Create session management with validation

- Implement session tracking
- Set up message persistence
- Create state management system
- Implement validation rules:
  - ChatSession validation:
    - Enforce 3 concurrent active sessions limit
    - Validate userId and preferredChannel
    - Prevent updates to ended sessions
  - Message validation:
    - Verify non-empty content
    - Validate sessionId and channel
    - Check timestamp validity
  - FeedbackRequest validation:
    - Verify sessionId and type
    - Enforce 48-hour expiration
    - Prevent expired request modifications
    - Validate channel configuration
  - FeedbackResponse validation:
    - Verify requestId and content
    - Validate responder authorization
    - Prevent processed response modifications
  - AgentState validation:
    - Validate sessionId and status
    - Check context size limits
    - Verify status/action consistency
  - CommunicationChannel validation:
    - Validate priority (1-3)
    - Enforce retry limit (max 10)
    - Verify timeout limits (max 1h)

## Phase 7: Backend Channel Integration

### Channel Services

T022. [P] Implement Gmail integration

- Set up Gmail API client
- Create email service
- Implement response handlers

T023. [P] Implement Slack integration

- Set up Slack Bolt SDK
- Create message service
- Implement webhook handlers

T024. Create channel orchestration

- Implement channel router
- Set up fallback mechanism
- Create retry logic

### State Synchronization

T025. Implement cross-channel sync

- Create state sync system
- Implement message history sync
- Add conversation continuity

## Dependencies

Frontend-first development order:

1. Frontend Setup (T001-T004) → Required for all frontend features
2. Frontend Core (T005-T010) → Basic chat interface [US1]
3. Frontend Interaction (T011-T012) → Pause/Resume [US2]
4. Frontend Channels (T013-T015) → Channel management [US3, US4]
5. Backend Setup (T016-T018) → Required for all backend features
6. Backend Core (T019-T021) → Agent and session management
7. Backend Channels (T022-T025) → Channel integration and sync

## Parallel Execution Examples

### Frontend Setup:

- Parallel: T002 (Project) + T003 (shadcn) + T004 (Auth)
- Sequential: T001 (VS Code) before others

### Frontend Core:

- Parallel: T005 (Layout) + T006 (Messages) + T007 (Input)
- Sequential: T009 (Streaming) after T008 (WebSocket)

### Backend Setup:

- Parallel: T016 (Project) + T017 (BAML)
- Sequential: T018 (Auth) after setup

## Implementation Strategy

### MVP Scope (Frontend First):

1. Complete frontend chat interface with shadcn/ui
2. Basic WebSocket client integration
3. Core UI components with proper styling
4. Minimal backend for testing

### Incremental Delivery:

1. Frontend chat interface [US1]
2. Frontend pause/resume [US2]
3. Frontend channel management [US3, US4]
4. Backend BAML integration
5. Backend channel services
6. Full system integration

## Summary

- Total Tasks: 25
- Tasks per Phase:

  - Frontend Setup: 4 tasks
  - Frontend Core (US1): 6 tasks
  - Frontend Interaction (US2): 2 tasks
  - Frontend Channels (US3, US4): 3 tasks
  - Backend Setup: 3 tasks
  - Backend Core: 3 tasks
  - Backend Channels: 4 tasks

- Parallel Opportunities: 15 tasks marked with [P]
- Independent Test Criteria: Available for each phase
- Suggested MVP: Frontend chat interface with shadcn/ui components
