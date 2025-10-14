"""
Agent service wrapper for BAML client.
Handles agent interactions, streaming responses, and state management.
"""

import asyncio
from typing import Optional, AsyncIterator, Dict, Any
from datetime import datetime

from baml_client.async_client import b as baml_client
from baml_client.types import AgentResponse

from ..models.base import (
    Message,
    MessageType,
    MessageStatus,
    ChannelType,
    AgentStatus,
)
from .session_service import session_service
from ..storage.memory_store import store


class AgentService:
    """Service for managing agent interactions via BAML."""
    
    def __init__(self):
        self.baml_client = baml_client
    
    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        channel: ChannelType
    ) -> Message:
        """
        Process a user message and generate agent response.
        
        Args:
            session_id: Session identifier
            user_message: User's message content
            channel: Channel used for communication
            
        Returns:
            Agent's response message
        """
        try:
            # Update agent status to THINKING
            session_service.update_agent_status(session_id, AgentStatus.THINKING)
            
            # Get conversation history
            conversation_history = self._build_conversation_history(session_id)
            
            # Get session context
            session = store.get_session(session_id)
            session_context = f"Session: {session_id}, Channel: {channel.value}"
            
            # Process message via BAML
            try:
                response = await self.baml_client.ProcessUserMessage(
                    user_message=user_message,
                    conversation_history=conversation_history,
                    session_context=session_context
                )
                
                response_content = response.message
                
            except Exception as e:
                # Fallback to simple echo if BAML fails
                response_content = f"I received your message: {user_message}"
                print(f"BAML processing error: {e}")
            
            # Update agent status to RESPONDING
            session_service.update_agent_status(session_id, AgentStatus.RESPONDING)
            
            # Create agent message
            agent_message = session_service.create_message(
                session_id=session_id,
                content=response_content,
                message_type=MessageType.AGENT,
                channel=channel
            )
            
            # Update agent status back to IDLE
            session_service.update_agent_status(session_id, AgentStatus.IDLE)
            
            return agent_message
            
        except Exception as e:
            # Update agent status to ERROR
            session_service.update_agent_status(session_id, AgentStatus.ERROR)
            
            # Create error message
            error_message = session_service.create_message(
                session_id=session_id,
                content=f"I encountered an error processing your message: {str(e)}",
                message_type=MessageType.SYSTEM,
                channel=channel
            )
            
            return error_message
    
    async def stream_response(
        self,
        session_id: str,
        user_message: str
    ) -> AsyncIterator[str]:
        """
        Stream agent response in real-time.
        
        Args:
            session_id: Session identifier
            user_message: User's message content
            
        Yields:
            Response chunks
        """
        try:
            # Update agent status
            session_service.update_agent_status(session_id, AgentStatus.THINKING)
            
            # Get conversation history
            conversation_history = self._build_conversation_history(session_id)
            
            # Update to RESPONDING
            session_service.update_agent_status(session_id, AgentStatus.RESPONDING)
            
            # Stream via BAML
            try:
                stream = self.baml_client.stream.StreamingChatResponse(
                    user_message=user_message,
                    conversation_history=conversation_history
                )
                
                # Yield chunks
                async for chunk in stream:
                    if chunk:
                        yield chunk
                
                # Get final response for storage
                final_response = await stream.get_final_response()
                
                # Store the complete message
                session_service.create_message(
                    session_id=session_id,
                    content=final_response,
                    message_type=MessageType.AGENT,
                    channel=ChannelType.WEBSOCKET
                )
                
            except Exception as e:
                # Fallback to simple response
                fallback = f"I understand you said: {user_message}"
                yield fallback
                
                session_service.create_message(
                    session_id=session_id,
                    content=fallback,
                    message_type=MessageType.AGENT,
                    channel=ChannelType.WEBSOCKET
                )
            
            # Update back to IDLE
            session_service.update_agent_status(session_id, AgentStatus.IDLE)
            
        except Exception as e:
            # Update to ERROR
            session_service.update_agent_status(session_id, AgentStatus.ERROR)
            yield f"Error: {str(e)}"
    
    async def determine_next_action(
        self,
        session_id: str,
        user_message: str,
        pending_tasks: list[str]
    ) -> Dict[str, Any]:
        """
        Determine what action the agent should take next.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            pending_tasks: List of pending tasks
            
        Returns:
            Action information
        """
        try:
            # Get conversation history
            conversation_history = self._build_conversation_history(session_id)
            
            # Get session context
            session = store.get_session(session_id)
            session_context = f"Session: {session_id}"
            
            # Determine action via BAML
            try:
                action = await self.baml_client.DetermineNextAction(
                    user_message=user_message,
                    conversation_history=conversation_history,
                    session_context=session_context,
                    pending_tasks=pending_tasks
                )
                
                return {
                    "action_type": action.intent if hasattr(action, 'intent') else "agent_response",
                    "data": action
                }
                
            except Exception as e:
                # Default to agent response
                return {
                    "action_type": "agent_response",
                    "data": {"message": "I'm ready to help. What would you like to know?"}
                }
                
        except Exception as e:
            return {
                "action_type": "error",
                "data": {"message": str(e)}
            }
    
    async def generate_feedback_request(
        self,
        action_description: str,
        risk_level: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Generate a feedback request for the user.
        
        Args:
            action_description: Description of the action
            risk_level: Risk level (low, medium, high)
            context: Additional context
            
        Returns:
            Feedback request information
        """
        try:
            # Generate via BAML
            feedback_req = await self.baml_client.GenerateFeedbackRequest(
                action_description=action_description,
                risk_level=risk_level,
                context=context
            )
            
            return {
                "type": feedback_req.type,
                "prompt": feedback_req.prompt,
                "context": feedback_req.context
            }
            
        except Exception as e:
            # Fallback
            return {
                "type": "approval",
                "prompt": f"Do you want to proceed with: {action_description}?",
                "context": context
            }
    
    def _build_conversation_history(
        self,
        session_id: str,
        max_messages: int = 20
    ) -> str:
        """
        Build conversation history string from session messages.
        
        Args:
            session_id: Session identifier
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted conversation history
        """
        messages = session_service.get_session_messages(session_id, limit=max_messages)
        
        if not messages:
            return "No previous conversation."
        
        history_lines = []
        for msg in messages:
            role = "User" if msg.type == MessageType.USER else "Agent"
            history_lines.append(f"{role}: {msg.content}")
        
        return "\n".join(history_lines)
    
    def get_agent_status(self, session_id: str) -> Optional[AgentStatus]:
        """Get current agent status for a session."""
        agent_state = session_service.get_agent_state(session_id)
        return agent_state.status if agent_state else None


# Global agent service instance
agent_service = AgentService()

