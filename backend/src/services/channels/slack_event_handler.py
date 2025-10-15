"""Slack event and interaction handler."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json
import uuid

from ...models.base import (
    FeedbackResponse,
    FeedbackStatus,
    ChannelType,
)
from ...storage.memory_store import store
from ...services.session_service import session_service


class SlackEventHandler:
    """
    Handle Slack events and interactive components.
    
    Processes button clicks, message events, and other Slack interactions.
    """
    
    async def handle_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Slack interactive component interactions.
        
        Args:
            payload: Slack interaction payload
            
        Returns:
            Response to send back to Slack
        """
        interaction_type = payload.get('type')
        
        if interaction_type == 'block_actions':
            return await self._handle_block_action(payload)
        elif interaction_type == 'view_submission':
            return await self._handle_view_submission(payload)
        else:
            return {"response_type": "ephemeral", "text": "Unknown interaction type"}
    
    async def _handle_block_action(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle button clicks and other block actions."""
        actions = payload.get('actions', [])
        
        if not actions:
            return {}
        
        action = actions[0]
        action_id = action.get('action_id')
        value = action.get('value')
        
        if not value:
            return {}
        
        try:
            value_data = json.loads(value)
            request_id = value_data.get('request_id')
            session_id = value_data.get('session_id')
            action_type = value_data.get('action')
            
            if not request_id or not session_id:
                return self._error_response("Invalid request data")
            
            # Get feedback request
            feedback_request = store.get_feedback_request(request_id)
            
            if not feedback_request:
                return self._error_response("Feedback request not found")
            
            if feedback_request.status != FeedbackStatus.PENDING:
                return self._error_response("Feedback request already processed")
            
            # Get user who clicked
            user = payload.get('user', {})
            slack_user_id = user.get('id')
            
            # Handle different action types
            if action_type == 'approve':
                return await self._handle_approval(
                    request_id, session_id, slack_user_id, True
                )
            elif action_type == 'reject':
                return await self._handle_approval(
                    request_id, session_id, slack_user_id, False
                )
            elif action_type == 'input':
                return await self._open_input_modal(
                    payload, request_id, session_id
                )
            
        except json.JSONDecodeError:
            return self._error_response("Invalid action data")
        except Exception as e:
            return self._error_response(f"Error processing action: {str(e)}")
        
        return {}
    
    async def _handle_approval(
        self,
        request_id: str,
        session_id: str,
        slack_user_id: str,
        approved: bool
    ) -> Dict[str, Any]:
        """Handle approval/rejection button click."""
        try:
            # Create feedback response
            response_content = "APPROVE" if approved else "REJECT"
            
            feedback_response = FeedbackResponse(
                id=str(uuid.uuid4()),
                request_id=request_id,
                content=response_content,
                timestamp=datetime.now(timezone.utc),
                channel=ChannelType.SLACK
            )
            
            # Submit response through session service
            success = session_service.submit_feedback_response(
                request_id,
                feedback_response
            )
            
            if success:
                # Update message to show response
                return {
                    "response_type": "in_channel",
                    "replace_original": True,
                    "text": f"✅ {'Approved' if approved else 'Rejected'} by <@{slack_user_id}>",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"{'✅ Approved' if approved else '❌ Rejected'} by <@{slack_user_id}>"
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Request ID: `{request_id[:8]}`"
                                }
                            ]
                        }
                    ]
                }
            else:
                return self._error_response("Failed to submit response. May have been already processed.")
                
        except Exception as e:
            return self._error_response(f"Error submitting response: {str(e)}")
    
    async def _open_input_modal(
        self,
        payload: Dict[str, Any],
        request_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Open modal for input feedback."""
        trigger_id = payload.get('trigger_id')
        
        if not trigger_id:
            return self._error_response("No trigger ID available")
        
        # Return view to open modal
        return {
            "response_action": "push",
            "view": {
                "type": "modal",
                "callback_id": f"feedback_input_{request_id}",
                "title": {
                    "type": "plain_text",
                    "text": "Provide Input"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Submit"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "input_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "input_value",
                            "multiline": True,
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Enter your response..."
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Your Input"
                        }
                    }
                ],
                "private_metadata": json.dumps({
                    "request_id": request_id,
                    "session_id": session_id
                })
            }
        }
    
    async def _handle_view_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle modal submission."""
        view = payload.get('view', {})
        callback_id = view.get('callback_id', '')
        
        if not callback_id.startswith('feedback_input_'):
            return {}
        
        try:
            # Get metadata
            private_metadata = view.get('private_metadata', '{}')
            metadata = json.loads(private_metadata)
            request_id = metadata.get('request_id')
            session_id = metadata.get('session_id')
            
            # Get input value
            values = view.get('state', {}).get('values', {})
            input_block = values.get('input_block', {})
            input_value = input_block.get('input_value', {}).get('value', '')
            
            if not input_value:
                return {
                    "response_action": "errors",
                    "errors": {
                        "input_block": "Please provide your input"
                    }
                }
            
            # Get user who submitted
            user = payload.get('user', {})
            slack_user_id = user.get('id')
            
            # Create feedback response
            feedback_response = FeedbackResponse(
                id=str(uuid.uuid4()),
                request_id=request_id,
                content=input_value,
                timestamp=datetime.now(timezone.utc),
                channel=ChannelType.SLACK
            )
            
            # Submit response
            success = session_service.submit_feedback_response(
                request_id,
                feedback_response
            )
            
            if success:
                return {"response_action": "clear"}
            else:
                return {
                    "response_action": "errors",
                    "errors": {
                        "input_block": "Failed to submit response. May have been already processed."
                    }
                }
                
        except Exception as e:
            return {
                "response_action": "errors",
                "errors": {
                    "input_block": f"Error: {str(e)}"
                }
            }
    
    async def handle_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle Slack events.
        
        Args:
            event: Slack event payload
            
        Returns:
            Optional response
        """
        event_type = event.get('type')
        
        # Handle different event types
        if event_type == 'message':
            return await self._handle_message_event(event)
        
        return None
    
    async def _handle_message_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming message events."""
        # This could be used to process replies to bot messages
        # For now, we rely on button interactions
        return None
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create error response for Slack."""
        return {
            "response_type": "ephemeral",
            "text": f"❌ {message}"
        }


# Global event handler instance
slack_event_handler = SlackEventHandler()

