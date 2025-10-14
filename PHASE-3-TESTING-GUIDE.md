# Phase 3: Feedback Workflow Testing Guide

## Quick Start

1. **Open the application**: Navigate to `http://localhost:5173/`
2. **Login**: Use the placeholder auth (any email/password)
3. **Access Feedback Demo**: Click "View Feedback Demo" button on dashboard

## Testing Checklist

### ✅ Basic Feedback Display

#### Test 1: View Feedback Requests

- [ ] Navigate to `/feedback-demo`
- [ ] Verify you see 3 mock feedback requests:
  - Approval request (47.5h remaining)
  - Input request (1.5h remaining - expiring soon)
  - Completed approval request (collapsed)
- [ ] Check that pending requests show "Action Required (2)" header
- [ ] Verify completed section shows "Completed (1)" and is collapsed

#### Test 2: Expiration Countdown

- [ ] Watch the countdown timer on pending requests
- [ ] Verify it updates in real-time (every second)
- [ ] Check format changes based on time:
  - > 1 hour: Shows "Xh Ym"
  - < 1 hour: Shows "Xm Ys"
  - < 1 minute: Shows "Xs"
- [ ] Verify the "expiring soon" request has an orange pulsing badge
- [ ] Verify the border turns orange for expiring requests

### ✅ Approval Workflow

#### Test 3: Approve Request

- [ ] Find the first approval request (production deployment)
- [ ] Hover over the "Approve" button
- [ ] Verify tooltip appears: "Approve this request and resume the agent"
- [ ] Click "Approve" button
- [ ] Verify loading spinner appears briefly
- [ ] Verify request moves to "Completed" section
- [ ] Verify status badge changes to green "Approved"
- [ ] Verify response appears with "approved" content
- [ ] Expand completed section to see the approved request

#### Test 4: Reject Request

- [ ] Click "Add Approval Request" to create a new one
- [ ] Hover over the "Reject" button
- [ ] Verify tooltip appears: "Reject this request and resume the agent"
- [ ] Click "Reject" button
- [ ] Verify loading spinner appears
- [ ] Verify request moves to "Completed" section
- [ ] Verify status badge changes to red "Rejected"

### ✅ Input Workflow

#### Test 5: Submit Text Input

- [ ] Find the input request (API key request)
- [ ] Click in the textarea
- [ ] Type: "test-api-key-12345"
- [ ] Verify character counter updates (shows "21 / 2000 characters")
- [ ] Verify "Submit Response" button is enabled
- [ ] Click "Submit Response"
- [ ] Verify loading spinner appears on button
- [ ] Verify request moves to "Completed" section
- [ ] Verify response shows your input text

#### Test 6: Empty Input Validation

- [ ] Click "Add Input Request" to create a new one
- [ ] Leave textarea empty
- [ ] Verify "Submit Response" button is disabled
- [ ] Type a space character only
- [ ] Verify button is still disabled (whitespace trimmed)
- [ ] Type actual content
- [ ] Verify button becomes enabled

#### Test 7: Keyboard Shortcuts

- [ ] Click "Add Input Request"
- [ ] Click in the textarea
- [ ] Type some text
- [ ] Press Ctrl+Enter (or Cmd+Enter on Mac)
- [ ] Verify the response submits via keyboard shortcut
- [ ] Verify you didn't need to click the button

#### Test 8: Character Limit

- [ ] Click "Add Input Request"
- [ ] Paste or type a very long text (>2000 chars)
- [ ] Verify textarea stops accepting input at 2000 characters
- [ ] Verify counter shows "2000 / 2000 characters"

### ✅ List Interactions

#### Test 9: Collapsible Completed Section

- [ ] Verify completed section is collapsed by default
- [ ] Click the "Completed (X)" button
- [ ] Verify section expands smoothly
- [ ] Verify completed requests appear with reduced opacity
- [ ] Click again to collapse
- [ ] Verify smooth collapse animation

#### Test 10: Dynamic Request Addition

- [ ] Click "Add Approval Request" multiple times
- [ ] Verify new requests appear at the top
- [ ] Verify counter updates: "Action Required (X)"
- [ ] Click "Add Input Request" multiple times
- [ ] Verify input requests also appear
- [ ] Verify both types work correctly

### ✅ Mobile Responsiveness

#### Test 11: Mobile Layout (< 640px)

- [ ] Resize browser window to 375px width (iPhone size)
- [ ] Verify feedback cards stack vertically
- [ ] Verify text remains readable (no overflow)
- [ ] Verify buttons are touch-friendly (44px height)
- [ ] Verify approve/reject buttons stack properly
- [ ] Verify no horizontal scrolling

#### Test 12: Touch Targets

- [ ] On mobile view, tap all interactive elements
- [ ] Verify all buttons have minimum 44px tap target
- [ ] Verify textarea is easy to tap and focus
- [ ] Verify collapsible button is easy to tap

#### Test 13: Tablet Layout (640px - 1024px)

- [ ] Resize to 768px (iPad size)
- [ ] Verify layout adapts smoothly
- [ ] Verify cards have appropriate width
- [ ] Verify spacing is comfortable

#### Test 14: Desktop Layout (> 1024px)

- [ ] Resize to full desktop width
- [ ] Verify cards have maximum width constraint
- [ ] Verify content is centered
- [ ] Verify spacing is generous but not excessive

### ✅ Visual States

#### Test 15: Badge Variants

- [ ] Verify pending badge is blue (default)
- [ ] Verify expiring badge is red with pulse animation
- [ ] Verify approved badge is green
- [ ] Verify rejected badge is red
- [ ] Verify expired badge is orange/gray

#### Test 16: Icons

- [ ] Verify pending requests show clock icon
- [ ] Verify approved requests show checkmark icon
- [ ] Verify rejected requests show X icon
- [ ] Verify expired requests show alert icon

#### Test 17: Animations

- [ ] Add a new request
- [ ] Verify smooth slide-in animation
- [ ] Complete a request
- [ ] Verify smooth transition to completed section
- [ ] Verify pulse animation on expiring requests
- [ ] Verify loading spinners are smooth

### ✅ Error Handling

#### Test 18: Error Display

- [ ] Error states are handled by the useFeedback hook
- [ ] In production, errors would display in red below the request
- [ ] Currently, no errors in demo mode (all succeed)

### ✅ Integration with Chat Session

#### Test 19: Feedback in Chat Context

- [ ] Navigate to `/chat` (if backend is ready)
- [ ] OR check the ChatSession.tsx implementation
- [ ] Verify FeedbackList appears above messages when paused
- [ ] Verify SessionStatus shows pending count
- [ ] Verify session status shows urgency for expiring feedback

### ✅ SessionStatus Component

#### Test 20: Status Display (Manual Code Review)

- [ ] Open `src/components/session/SessionStatus.tsx`
- [ ] Verify it accepts `feedbackRequests` prop
- [ ] Verify it counts pending requests
- [ ] Verify it checks for urgent feedback (< 2 hours)
- [ ] Verify it shows badge with count
- [ ] Verify it uses destructive variant for urgent

## Browser Testing

### Desktop Browsers

- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (if available)

### Mobile Browsers (DevTools)

- [ ] Chrome DevTools mobile emulation
- [ ] Firefox Responsive Design Mode
- [ ] iPhone 12/13/14 viewport
- [ ] Android viewport

## Accessibility Testing

- [ ] Tab through all interactive elements
- [ ] Verify focus indicators are visible
- [ ] Verify buttons are keyboard accessible
- [ ] Verify textarea can be focused with Tab
- [ ] Verify Ctrl+Enter works in textarea

## Performance Checks

- [ ] Countdown timers update smoothly (no lag)
- [ ] Animations are smooth (60fps)
- [ ] No console errors or warnings
- [ ] Network tab shows no failed requests
- [ ] React DevTools shows no unnecessary re-renders

## Edge Cases

### Test 21: Multiple Simultaneous Requests

- [ ] Add 5 approval requests
- [ ] Add 5 input requests
- [ ] Verify all display correctly
- [ ] Verify scrolling works if needed
- [ ] Complete them all
- [ ] Verify completed section handles many items

### Test 22: Rapid Interactions

- [ ] Rapidly click "Add Approval Request" 10 times
- [ ] Verify no UI glitches
- [ ] Rapidly approve/reject multiple requests
- [ ] Verify state updates correctly

### Test 23: Long Text Content

- [ ] Add input request
- [ ] Type a very long response (1000+ characters)
- [ ] Submit
- [ ] Verify response displays correctly in completed section
- [ ] Verify no layout breaks

## Console Output

Monitor browser console during testing:

- [ ] No error messages
- [ ] No warning messages
- [ ] Feedback submissions log correctly
- [ ] State updates log (if debug mode enabled)

## Success Criteria

All tests above should pass with:

- ✅ No visual glitches
- ✅ Smooth animations
- ✅ Proper touch targets
- ✅ Correct state management
- ✅ Accurate timers
- ✅ Validation working
- ✅ Responsive on all sizes
- ✅ No console errors

## Known Limitations (Expected)

1. **No Backend**: All operations are client-side only
2. **No Persistence**: Refresh loses state (mock data resets)
3. **No Real WebSocket**: Simulated events only
4. **Expiration**: Client-side only, no server enforcement

## Next Steps After Testing

Once all tests pass:

1. ✅ Mark Phase 3 as complete
2. ✅ Update phase-3-frontend-implementation.plan.md
3. ✅ Document any issues found
4. ✅ Prepare for Phase 4 (Channel Management)

## Quick Test Script

For rapid testing, follow this sequence:

1. Open `/feedback-demo`
2. Approve first request → Check completed section
3. Reject second request → Check completed section
4. Submit text input for third request → Check response
5. Add new approval → Approve it
6. Add new input → Type "test" → Submit
7. Resize to 375px → Verify mobile layout
8. Resize to 1920px → Verify desktop layout
9. ✅ All working!

## Screenshots to Capture

Recommended screenshots for documentation:

1. Pending requests view (desktop)
2. Approval buttons with tooltips
3. Input textarea with character count
4. Completed section expanded
5. Mobile view (375px)
6. Tablet view (768px)
7. Expiring request with pulse badge
8. Loading state during submission
