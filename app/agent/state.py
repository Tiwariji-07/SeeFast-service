"""
Agent State Definition
======================

In LangGraph, "State" is the data that flows through the graph.
Think of it as a shared memory that all nodes can read and write to.

Key Concepts:
- TypedDict: Python's way of defining a dictionary with specific keys
- The state gets passed to every node in the graph
- Each node can add/modify state and pass it to the next node
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """
    The state of our Data Canvas Agent.
    
    This state flows through the graph:
    START → agent → tools → agent → ... → END
    
    Attributes:
        messages: Conversation history (system, human, AI, tool messages)
                  The Annotated[..., operator.add] means new messages get appended
        
        widgets: The visualization widgets to return to the frontend
                 Each widget is a dict with id, component, position, data, config
        
        final_response: The agent's text response to show the user
    """
    
    # Messages accumulate - new messages are added to existing ones
    # This is how LangGraph handles conversation history
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Widgets to render on the canvas
    widgets: list[dict]
    
    # Final text response for the user
    final_response: str
