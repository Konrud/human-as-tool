// Chat Agent BAML Templates
// Interactive Agent Chat System

// =====================================================
// Data Models
// =====================================================

class ClarificationRequest {
  intent "request_clarification" @description("Request more information from the user")
  message string @description("The clarification question to ask")
  context string[] @description("Related context that needs clarification")
}

class ThinkingUpdate {
  intent "thinking_update" @description("Update about what the agent is currently thinking")
  status string @description("Current thinking status")
  progress int @description("Progress percentage (0-100)")
}

class AgentResponse {
  intent "agent_response" @description("Direct response to user's message")
  message string @description("The response message to send to the user")
  requires_feedback bool @description("Whether this response requires user feedback")
  feedback_type string? @description("Type of feedback needed: 'approval' or 'input'")
}

class FeedbackRequestGeneration {
  intent "feedback_request" @description("Generate a feedback request for the user")
  type string @description("Type: 'approval' or 'input'")
  prompt string @description("The feedback request prompt")
  context string @description("Context for why feedback is needed")
}

class ErrorResponse {
  intent "error_response" @description("Error occurred during processing")
  message string @description("Error message to display")
  recoverable bool @description("Whether the error is recoverable")
}

// Union type for all possible agent actions
type AgentAction = ClarificationRequest | ThinkingUpdate | AgentResponse | FeedbackRequestGeneration | ErrorResponse

// =====================================================
// Functions
// =====================================================

function ProcessUserMessage(
  user_message: string,
  conversation_history: string,
  session_context: string
) -> AgentResponse {
  client CustomGPT4o
  
  prompt #"
    {{ _.role("system") }}
    
    You are a helpful AI assistant in an interactive chat system. You can:
    - Answer user questions directly
    - Request clarification when needed
    - Ask for approval before taking actions
    - Request additional input from users
    
    Your responses should be:
    - Clear and concise
    - Helpful and accurate
    
    {{ _.role("user") }}
    
    Session Context:
    {{ session_context }}
    
    Conversation History:
    {{ conversation_history }}
    
    Current User Message:
    {{ user_message }}
    
    Provide a response to the user's message.
    
    {{ ctx.output_format }}
  "#
}

function DetermineNextAction(
  user_message: string,
  conversation_history: string,
  session_context: string,
  pending_tasks: string[]
) -> AgentAction {
  client CustomGPT4o
  
  prompt #"
    {{ _.role("system") }}
    
    You are an AI assistant that determines what action to take next in a conversation.
    
    Available actions:
    1. ClarificationRequest - When you need more information from the user
    2. ThinkingUpdate - When processing takes time and you want to update status
    3. AgentResponse - When you have a direct response to the user
    4. FeedbackRequestGeneration - When you need approval or input for an action
    5. ErrorResponse - When an error occurs
    
    {{ _.role("user") }}
    
    Session Context:
    {{ session_context }}
    
    Conversation History:
    {{ conversation_history }}
    
    Current User Message:
    {{ user_message }}
    
    Pending Tasks:
    {% for task in pending_tasks %}
    - {{ task }}
    {% endfor %}
    
    Determine the next action to take.
    
    {{ ctx.output_format }}
  "#
}

function GenerateFeedbackRequest(
  action_description: string,
  risk_level: string,
  context: string
) -> FeedbackRequestGeneration {
  client CustomGPT4o
  
  prompt #"
    {{ _.role("system") }}
    
    You are generating a feedback request for a user.
    
    The feedback request should:
    - Clearly explain what action will be taken
    - Explain why approval/input is needed
    - Be concise but informative
    
    {{ _.role("user") }}
    
    Action Description:
    {{ action_description }}
    
    Risk Level:
    {{ risk_level }}
    
    Context:
    {{ context }}
    
    Generate a feedback request prompt.
    
    {{ ctx.output_format }}
  "#
}

function StreamingChatResponse(
  user_message: string,
  conversation_history: string
) -> string {
  client CustomGPT4o
  
  prompt #"
    {{ _.role("system") }}
    
    You are a helpful AI assistant. Provide a conversational response to the user.
    Keep responses natural, and helpful.
    
    {{ _.role("user") }}
    
    Conversation History:
    {{ conversation_history }}
    
    User Message:
    {{ user_message }}
    
    Your Response:
  "#
}

// =====================================================
// Tests
// =====================================================

test simple_greeting {
  functions [ProcessUserMessage]
  args {
    user_message "Hello, how are you?"
    conversation_history ""
    session_context "New session started"
  }
}

test clarification_needed {
  functions [DetermineNextAction]
  args {
    user_message "Can you help me with that?"
    conversation_history ""
    session_context "No prior context"
    pending_tasks []
  }
}

test feedback_approval {
  functions [GenerateFeedbackRequest]
  args {
    action_description "Delete all files in the project directory"
    risk_level "high"
    context "User requested cleanup"
  }
}

test streaming_response {
  functions [StreamingChatResponse]
  args {
    user_message "Tell me about the weather"
    conversation_history "User: Hello\nAgent: Hi! How can I help you today?"
  }
}

