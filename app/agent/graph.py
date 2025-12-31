"""
LangGraph State Graph
=====================

This is the heart of our agent - the graph that defines the flow:
1. AGENT node: LLM decides what to do
2. TOOLS node: Execute tool calls
3. Loop back to AGENT until done
4. FORMAT node: Convert tool results to widgets

Key Concepts:
- StateGraph: A graph where nodes modify shared state
- Nodes: Functions that take state and return updates
- Edges: Connections between nodes (can be conditional)
- The graph compiles to a runnable that processes queries
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from typing import Literal
import json
import uuid

from app.agent.state import AgentState
from app.agent.tools import ALL_TOOLS
from app.agent.prompts import SYSTEM_PROMPT
from app.config import settings


# =============================================================================
# SETUP
# =============================================================================

# Create the LLM with tool-calling capability
llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0.1,
)

# Bind the tools to the LLM - this tells the LLM what tools are available
llm_with_tools = llm.bind_tools(ALL_TOOLS)


# =============================================================================
# NODE DEFINITIONS
# =============================================================================

def agent_node(state: AgentState) -> dict:
    """
    The AGENT node - the brain of our system.
    
    This node:
    1. Takes the current conversation (messages)
    2. Sends to LLM to decide what to do
    3. Returns the LLM's response (might include tool calls)
    
    The LLM will either:
    - Call tools to get data
    - Return a final response to the user
    """
    messages = state["messages"]
    
    # Call the LLM with the conversation history
    response = llm_with_tools.invoke(messages)
    
    # Return the response to be added to messages
    # LangGraph will automatically append it due to our state annotation
    return {"messages": [response]}


def format_output_node(state: AgentState) -> dict:
    """
    The FORMAT node - converts tool results into widgets.
    
    Handles both old mock format and new format_for_widget output.
    """
    messages = state["messages"]
    widgets = []
    
    widget_row = 1
    widget_col = 1
    
    for msg in messages:
        if isinstance(msg, ToolMessage):
            try:
                tool_result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if not tool_result:
                    continue
                
                # Handle format_for_widget output (has "component" key)
                if "component" in tool_result and "data" in tool_result:
                    widget_id = f"widget-{uuid.uuid4().hex[:8]}"
                    widgets.append({
                        "id": widget_id,
                        "component": tool_result["component"],
                        "position": {"column": widget_col, "row": widget_row, "width": 6, "height": 2},
                        "data": tool_result["data"],
                        "config": tool_result.get("config", {}),
                    })
                    widget_col += 6
                    if widget_col > 12:
                        widget_col = 1
                        widget_row += 2
                    continue
                
                # Handle call_api raw data output
                if "data" in tool_result and not tool_result.get("error"):
                    data = tool_result["data"]
                    widget = auto_format_data(data, widget_row, widget_col)
                    if widget:
                        widgets.append(widget)
                        widget_col += widget["position"]["width"]
                        if widget_col > 12:
                            widget_col = 1
                            widget_row += widget["position"]["height"]
                
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    
    # Get the final AI message
    final_message = "Here's what I found for you."
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            final_message = msg.content
            break
    
    return {
        "widgets": widgets,
        "final_response": final_message
    }


def auto_format_data(data: any, row: int, col: int) -> dict | None:
    """Auto-format raw API data into a widget."""
    widget_id = f"widget-{uuid.uuid4().hex[:8]}"
    
    # List of objects -> Table
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        columns = list(data[0].keys())[:10]  # Limit columns
        rows = [[str(item.get(c, ""))[:50] for c in columns] for item in data[:20]]
        return {
            "id": widget_id,
            "component": "Table",
            "position": {"column": 1, "row": row, "width": 12, "height": 2},
            "data": {"columns": columns, "rows": rows},
            "config": {"title": "Results"}
        }
    
    # Dict with numeric values -> BarChart
    if isinstance(data, dict):
        numeric_items = [(k, v) for k, v in data.items() if isinstance(v, (int, float))]
        if numeric_items:
            return {
                "id": widget_id,
                "component": "BarChart",
                "position": {"column": col, "row": row, "width": 6, "height": 2},
                "data": {
                    "labels": [k for k, v in numeric_items],
                    "values": [v for k, v in numeric_items],
                },
                "config": {"title": "Distribution"}
            }
        
        # Single object -> Table
        return {
            "id": widget_id,
            "component": "Table",
            "position": {"column": 1, "row": row, "width": 12, "height": 2},
            "data": {
                "columns": ["Property", "Value"],
                "rows": [[k, str(v)[:100]] for k, v in list(data.items())[:15]]
            },
            "config": {"title": "Details"}
        }
    
    return None


def convert_tool_result_to_widget(result: dict, row: int, col: int) -> dict | None:
    """
    Convert a tool result into a widget configuration.
    
    The frontend expects widgets in this format:
    {
        id: unique string,
        component: "Table" | "BarChart" | "LineChart" | "MetricCard",
        position: { column, row, width, height },
        data: component-specific data,
        config: { title, etc }
    }
    """
    widget_id = f"widget-{uuid.uuid4().hex[:8]}"
    
    # Handle metric results
    if "metric_name" in result and "data" in result:
        data = result["data"]
        return {
            "id": widget_id,
            "component": "MetricCard",
            "position": {"column": col, "row": row, "width": 4, "height": 1},
            "data": {
                "value": data.get("value", "N/A"),
                "label": result["metric_name"].replace("_", " ").title(),
                "change": data.get("change", ""),
                "changeType": data.get("changeType", "neutral"),
                "subtext": data.get("subtext", ""),
            },
            "config": {}
        }
    
    # Handle chart results
    if "chart_type" in result and "data" in result:
        chart_type = result["chart_type"]
        category = result.get("category", "Chart")
        data = result["data"]
        
        component = "BarChart"
        if chart_type == "line" or "growth" in category or "trend" in category or "monthly" in category:
            component = "LineChart"
        elif chart_type == "pie":
            component = "PieChart"
        
        # For LineChart, we need datasets format
        if component == "LineChart":
            chart_data = {
                "labels": data.get("labels", []),
                "datasets": [{"label": category.replace("_", " ").title(), "values": data.get("values", [])}]
            }
        else:
            chart_data = data
        
        return {
            "id": widget_id,
            "component": component,
            "position": {"column": col, "row": row, "width": 6, "height": 2},
            "data": chart_data,
            "config": {
                "title": category.replace("_", " ").title(),
            }
        }
    
    # Handle table results
    if "table_name" in result and "data" in result:
        return {
            "id": widget_id,
            "component": "Table",
            "position": {"column": 1, "row": row, "width": 12, "height": 2},
            "data": result["data"],
            "config": {
                "title": result["table_name"].replace("_", " ").title()
            }
        }
    
    return None


# =============================================================================
# ROUTING LOGIC
# =============================================================================

def should_continue(state: AgentState) -> Literal["tools", "format"]:
    """
    Decide whether to continue to tools or go to formatting.
    
    This is a CONDITIONAL EDGE - it routes based on logic.
    
    If the last message has tool_calls → go to tools
    Otherwise → go to format (we're done getting data)
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM wants to call tools, route to tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # Otherwise, we're done - go format the output
    return "format"


# =============================================================================
# BUILD THE GRAPH
# =============================================================================

def create_agent_graph():
    """
    Build the LangGraph state graph.
    
    The flow is:
    START → agent → (tools → agent)* → format → END
    
    Where * means "repeat 0 or more times"
    """
    # Create the graph with our state type
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))  # LangGraph's built-in tool executor
    workflow.add_node("format", format_output_node)
    
    # Set the entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edge from agent
    # Based on should_continue, go to either "tools" or "format"
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "format": "format",
        }
    )
    
    # After tools, always go back to agent
    workflow.add_edge("tools", "agent")
    
    # After format, we're done
    workflow.add_edge("format", END)
    
    # Compile the graph into a runnable
    return workflow.compile()


# Create the compiled graph
agent_graph = create_agent_graph()
