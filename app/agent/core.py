"""
Agent Core
==========

Public interface for the agent with conversational memory support.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.graph import agent_graph
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.memory import get_memory


async def process_query(message: str, session_id: str = "default") -> dict:
    """
    Process a user query with conversation context.
    
    Args:
        message: User's natural language question
        session_id: Session ID for conversation memory
    
    Returns:
        dict with 'message' and 'widgets' keys
    """
    # Get conversation memory
    memory = get_memory(session_id)
    
    # Build messages with context
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    # Add conversation history for context
    context = memory.get_context_messages(limit=3)
    for ctx_msg in context:
        if ctx_msg["role"] == "user":
            messages.append(HumanMessage(content=ctx_msg["content"]))
        else:
            from langchain_core.messages import AIMessage
            messages.append(AIMessage(content=ctx_msg["content"]))
    
    # Add current query
    messages.append(HumanMessage(content=message))
    
    # Create initial state
    initial_state = {
        "messages": messages,
        "widgets": [],
        "final_response": "",
    }
    
    try:
        # Run the graph
        final_state = await agent_graph.ainvoke(initial_state)
        
        response_message = final_state.get("final_response", "Here's what I found.")
        widgets = final_state.get("widgets", [])
        
        # Save to memory
        memory.add_turn(message, response_message, widgets)
        
        return {
            "message": response_message,
            "widgets": widgets,
        }
        
    except Exception as e:
        print(f"Agent error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "message": f"I encountered an error: {str(e)}",
            "widgets": [],
        }
