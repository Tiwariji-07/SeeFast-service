"""
API Routes
==========

This file defines all the API endpoints for the Data Canvas Agent.

Key Concepts:
- APIRouter: Groups related routes together (like Express Router)
- Pydantic models: Define request/response shapes with validation
- async/await: Non-blocking I/O for better performance
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.agent.core import process_query

# Create a router instance
# All routes here will be prefixed with /api (set in main.py)
router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================
# Pydantic models define the "shape" of data coming in and going out.
# They automatically validate data and generate OpenAPI docs.

class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""
    message: str                      # The user's question
    session_id: str = "default"       # For conversation memory (later)
    
    class Config:
        # Example shown in API docs
        json_schema_extra = {
            "example": {
                "message": "Show me top 10 customers by revenue",
                "session_id": "user-123"
            }
        }


class WidgetPosition(BaseModel):
    """Position of a widget on the canvas grid."""
    column: int    # Starting column (1-12)
    row: int       # Starting row
    width: int     # How many columns to span
    height: int    # How many rows to span


class Widget(BaseModel):
    """A single visualization widget."""
    id: str                           # Unique identifier
    component: str                    # Type: Table, BarChart, etc.
    position: WidgetPosition          # Where on the canvas
    data: dict                        # Data to display
    config: dict = {}                 # Component-specific settings


class CanvasResponse(BaseModel):
    """Response from the /query endpoint."""
    message: str                      # Agent's text response
    widgets: list[Widget]             # Widgets to render on canvas
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Here are the top 10 customers by revenue.",
                "widgets": [
                    {
                        "id": "table-1",
                        "component": "Table",
                        "position": {"column": 1, "row": 1, "width": 12, "height": 2},
                        "data": {
                            "columns": ["Customer", "Revenue"],
                            "rows": [["Acme Corp", "$125,000"]]
                        },
                        "config": {"title": "Top Customers"}
                    }
                ]
            }
        }


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/query", response_model=CanvasResponse)
async def query(request: QueryRequest):
    """
    Process a natural language query and return visualization widgets.
    
    This is the main endpoint that:
    1. Takes user's question
    2. Sends to AI agent
    3. Returns widgets for the canvas
    """
    try:
        result = await process_query(
            message=request.message,
            session_id=request.session_id
        )
        return result
    except Exception as e:
        # In production, log the error properly
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get conversation history for a session (for future use).
    """
    # TODO: Implement session retrieval
    return {
        "session_id": session_id,
        "history": [],
        "widgets": []
    }
