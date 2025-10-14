<!-- 1d9efc70-04d0-428b-8d38-b5f75f08a797 f2b77213-2d78-4255-93c5-e2ac6c7d41c8 -->
# Phase 4: Frontend Channel Management Implementation

## Overview

Implement channel selection, feedback UI, and fallback components to enable multi-channel communication (chat, email, Slack) and user preference management for User Stories 3 and 4.

## Current State

**Completed:**

- Phase 1: Frontend setup with shadcn/ui and TypeScript
- Phase 2: Real-time chat interface with WebSocket (US1)
- Phase 3: Pause/Resume functionality with feedback UI (US2)

**Available:**

- `ChannelType` enum (WEBSOCKET, EMAIL, SLACK) in `types/models.ts`
- `ChannelStatus` enum (ACTIVE, INACTIVE, ERROR, RECONNECTING)
- `CommunicationChannel` interface with status tracking
- `useSession` hook with `channelStatus` state for all three channels
- `ChatSession.preferredChannel` field in data model
- shadcn/ui components: Select, Alert, Badge (from Phase 3), Button, Card

**Missing:**

- Channel selection UI components
- Channel preference management
- Channel status display and indicators
- Channel fallback notification UI
- Reconnection and channel switching UI
- Hook for managing channel operations

## Implementation Plan

### 1. Install Missing UI Components

**Files: Terminal**

Add shadcn/ui components needed for channel UI:

- Badge component (if not already added in Phase 3)
- Tooltip component for hover information
- Dialog component for channel settings
```bash
npx shadcn@latest add badge tooltip dialog
```


### 2. Create Channel Hook

**File: `frontend/src/hooks/useChannel.ts` (NEW)**

Manage channel operations and state:

- Track available channels and their status
- Change preferred channel
- Handle channel fallback scenarios
- Subscribe to channel status updates via WebSocket
- Calculate next fallback channel
```typescript
export function useChannel({ sessionId, send }: UseChannelOptions) {
  // Track channel status for WEBSOCKET, EMAIL, SLACK
  // changePreferredChannel(channel: ChannelType)
  // getNextFallbackChannel() - returns next in priority order
  // isChannelAvailable(channel: ChannelType)
}
```


### 3. Create ChannelSelector Component

**File: `frontend/src/components/channel/ChannelSelector.tsx` (NEW)**

Mobile-first channel selection dropdown:

- Use shadcn/ui Select component
- Display all three channels (Chat, Email, Slack)
- Show status badge for each option (active/inactive/error)
- Touch-friendly dropdown items (44px minimum)
- Update session's preferredChannel on change
- Disabled state when session paused/ended
- Responsive layout (compact on mobile, expanded on desktop)

Example structure:

```tsx
<Select value={preferredChannel} onValueChange={handleChannelChange}>
  <SelectTrigger className="min-h-touch">
    <Mail className="w-4 h-4 mr-2" />
    {channelLabels[preferredChannel]}
  </SelectTrigger>
  <SelectContent>
    {channels.map(channel => (
      <SelectItem value={channel}>
        <ChannelIcon /> {label}
        <Badge variant={statusVariant}>{status}</Badge>
      </SelectItem>
    ))}
  </SelectContent>
</Select>
```

### 4. Create ChannelStatusBadge Component

**File: `frontend/src/components/channel/ChannelStatusBadge.tsx` (NEW)**

Visual status indicator for channels:

- Badge component from shadcn/ui
- Color coding: green (active), gray (inactive), red (error), yellow (reconnecting)
- Icon + text (e.g., "🟢 Active", "🔴 Error")
- Tooltip with detailed status information
- Responsive sizing (smaller on mobile)
```tsx
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger>
      <Badge variant={variant}>
        <StatusIcon /> {statusText}
      </Badge>
    </TooltipTrigger>
    <TooltipContent>Last active: {lastActive}</TooltipContent>
  </Tooltip>
</TooltipProvider>
```


### 5. Create ChannelStatus Component

**File: `frontend/src/components/channel/ChannelStatus.tsx` (NEW)**

Comprehensive channel status display:

- Show status for all three channels
- Grid layout on desktop (3 columns), stack on mobile
- Each channel shows: icon, name, status badge, last active time
- Expandable details (errors, retry info)
- Touch-friendly expand/collapse
- Alert-based warnings for channel errors

### 6. Create ChannelFallbackAlert Component

**File: `frontend/src/components/channel/ChannelFallbackAlert.tsx` (NEW)**

Notification when channel fallback occurs:

- Alert component with warning styling
- Shows: "Chat unavailable, switched to Email"
- Displays new channel and reason for fallback
- Countdown to next retry attempt
- Action button to manually retry failed channel
- Dismissible (but persists across component re-renders)
- Animated slide-in entrance
```tsx
<Alert variant="warning" className="animate-in slide-in-from-top">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Channel Switched</AlertTitle>
  <AlertDescription>
    Chat unavailable. Now using Email. 
    <Button onClick={retryChannel}>Retry Chat</Button>
  </AlertDescription>
</Alert>
```


### 7. Create ChannelReconnecting Component

**File: `frontend/src/components/channel/ChannelReconnecting.tsx` (NEW)**

Display reconnection status:

- Shows during RECONNECTING status
- Progress spinner animation
- Attempt counter (e.g., "Attempt 2 of 5")
- Time until next retry with countdown
- Cancel reconnection button (falls back to next channel)
- Minimal UI that doesn't block content

### 8. Create ChannelSettings Dialog

**File: `frontend/src/components/channel/ChannelSettings.tsx` (NEW)**

Advanced channel preferences dialog:

- Dialog component for full-screen settings on mobile
- Manage channel priority order (Chat → Email → Slack by default)
- Enable/disable specific channels
- Set retry limits per channel
- Configure timeout settings
- Save button sends preferences to backend via WebSocket
- Responsive: full-screen on mobile, modal on desktop

### 9. Update ChatPage

**File: `frontend/src/pages/ChatPage.tsx` (UPDATE)**

Integrate channel components into chat page:

```tsx
// In header area (next to theme toggle):
<ChannelSelector 
  preferredChannel={session?.preferredChannel}
  channelStatus={channelStatus}
  onChange={handleChannelChange}
  disabled={session?.status !== 'active'}
/>

// Below header, above chat:
{showChannelFallback && (
  <ChannelFallbackAlert 
    previousChannel={previousChannel}
    currentChannel={currentChannel}
    reason={fallbackReason}
    onRetry={handleRetryChannel}
    onDismiss={() => setShowChannelFallback(false)}
  />
)}

{channelStatus.websocket === 'reconnecting' && (
  <ChannelReconnecting
    attempts={reconnectAttempts}
    maxAttempts={5}
    nextRetryIn={nextRetrySeconds}
    onCancel={handleCancelReconnect}
  />
)}

// Settings button opens ChannelSettings dialog
```

### 10. Update useSession Hook

**File: `frontend/src/hooks/useSession.ts` (UPDATE)**

Add channel-related event handling:

```typescript
// In handleMessage callback, add new cases:
case "channel_status_update":
  setState(prev => ({
    ...prev,
    channelStatus: {
      ...prev.channelStatus,
      [data.payload.channel]: data.payload.status
    }
  }));
  break;

case "channel_fallback":
  // Trigger fallback alert UI
  // Update preferred channel
  break;

case "channel_reconnect_attempt":
  // Update reconnection UI state
  break;
```

Add action:

```typescript
const changePreferredChannel = useCallback((channel: ChannelType) => {
  send({
    type: "change_preferred_channel",
    payload: { sessionId, channel }
  });
}, [send, sessionId]);
```

### 11. Update SessionStatus Component

**File: `frontend/src/components/session/SessionStatus.tsx` (UPDATE)**

Show channel information in session status:

- Display current active channel
- Show "via Email" or "via Slack" when not using WebSocket
- Update styling to accommodate channel info
- Add tooltip showing all channel statuses

### 12. Create ChannelIcon Utility

**File: `frontend/src/components/channel/ChannelIcon.tsx` (NEW)**

Reusable channel icon component:

- Map ChannelType to lucide-react icon
- WEBSOCKET → MessageSquare
- EMAIL → Mail  
- SLACK → MessageCircle or Hash
- Size and color customization props
- Consistent styling across all channel components

### 13. Update Types (if needed)

**File: `frontend/src/types/models.ts` (CHECK)**

Verify types match requirements:

- Ensure `ChannelType` includes WEBSOCKET, EMAIL, SLACK
- Ensure `ChannelStatus` includes RECONNECTING
- Add `ChannelPreferences` interface if needed for settings
- Add WebSocket message types for channel events

## File Structure

```
frontend/src/
├── components/
│   ├── channel/                    # NEW FOLDER
│   │   ├── ChannelSelector.tsx     # NEW
│   │   ├── ChannelStatusBadge.tsx  # NEW
│   │   ├── ChannelStatus.tsx       # NEW
│   │   ├── ChannelFallbackAlert.tsx # NEW
│   │   ├── ChannelReconnecting.tsx # NEW
│   │   ├── ChannelSettings.tsx     # NEW
│   │   └── ChannelIcon.tsx         # NEW
│   ├── session/
│   │   └── SessionStatus.tsx       # UPDATE
│   └── ui/
│       ├── badge.tsx               # Verify exists (from Phase 3)
│       ├── tooltip.tsx             # NEW
│       └── dialog.tsx              # NEW
├── hooks/
│   ├── useChannel.ts               # NEW
│   └── useSession.ts               # UPDATE
├── pages/
│   └── ChatPage.tsx                # UPDATE
└── types/
    └── models.ts                   # CHECK/UPDATE if needed
```

## Key Features

### Channel Selection

- Dropdown with all available channels
- Real-time status indicators
- Touch-friendly mobile interface
- Automatic fallback on failure

### Channel Status Display

- Visual badges for each channel
- Detailed status information
- Error messages and retry info
- Historical connection data

### Channel Fallback

- Automatic switching on failure
- Clear notifications to user
- Manual retry capability
- Configurable fallback order

### Channel Settings

- Customize channel priorities
- Enable/disable channels
- Configure retry behavior
- Timeout configuration

## Success Criteria

- ✅ Channel selector displays all three channels with status
- ✅ User can change preferred channel via dropdown
- ✅ Channel fallback alert appears when channel switches
- ✅ Reconnection UI shows attempt count and countdown
- ✅ Channel settings dialog allows priority customization
- ✅ All touch targets meet 44px minimum
- ✅ Responsive design works on mobile and desktop
- ✅ WebSocket events trigger appropriate UI updates
- ✅ No TypeScript or linter errors
- ✅ Dark mode support for all new components

## Testing Approach

Without backend:

1. Mock channel status changes in useChannel hook
2. Test channel selector dropdown interaction
3. Verify fallback alert displays correctly
4. Test reconnection UI countdown
5. Verify channel settings dialog functionality
6. Check responsive layouts on all screen sizes
7. Test dark mode appearance

## Technical Decisions

1. **Channel Priority**: Use fixed order (Chat → Email → Slack) with future configurability via settings
2. **Fallback Trigger**: Client-side detection + backend notification via WebSocket
3. **Status Polling**: Use WebSocket events instead of HTTP polling for real-time updates
4. **Settings Persistence**: Store in backend, sync via WebSocket
5. **UI Pattern**: Non-blocking alerts and indicators, avoid modal dialogs except for settings
6. **Mobile Experience**: Bottom sheet for channel selector, full-screen settings dialog

## Dependencies

- Phases 1, 2, 3 must be complete (all are ✅)
- shadcn/ui components: Badge, Tooltip, Dialog
- lucide-react icons for channels
- WebSocket connection from Phase 2

### To-dos

- [x] Install shadcn/ui Badge, Tooltip, and Dialog components
- [x] Create useChannel hook for channel state management and operations
- [x] Create ChannelIcon utility component for consistent icon display
- [x] Create ChannelStatusBadge component with tooltip and status indicators
- [x] Create ChannelSelector dropdown component with mobile-first design
- [x] Create ChannelStatus component showing all channel states
- [x] Create ChannelFallbackAlert component for channel switch notifications
- [x] Create ChannelReconnecting component with countdown and progress
- [x] Create ChannelSettings dialog for advanced channel configuration
- [x] Update useSession hook to handle channel events and changePreferredChannel action
- [x] Update SessionStatus component to display current channel information
- [x] Integrate all channel components into ChatPage layout
- [x] Test all channel features with mock data and verify responsive design

