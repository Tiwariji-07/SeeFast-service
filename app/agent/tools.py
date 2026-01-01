"""
Agent Tools
===========

Tools for the LangGraph agent to:
1. Search for API endpoints
2. Get endpoint details
3. Call APIs
4. Format data for widgets
"""

from langchain_core.tools import tool
from typing import Optional, Any
import httpx
import json

from app.registry.endpoint_registry import get_registry
from app.services.cache import get_cache


@tool
def search_endpoints(query: str, top_k: int = 5) -> dict:
    """
    Search for API endpoints matching your query.
    
    Use this FIRST when you need to find what APIs are available.
    Returns a list of matching endpoints with their IDs, paths, and summaries.
    
    Args:
        query: Natural language description of what you're looking for
               e.g., "find pets", "get user info", "store inventory"
        top_k: Number of results to return (default 5)
    
    Returns:
        List of matching endpoints
    """
    registry = get_registry()
    results = registry.search(query, top_k=top_k)
    
    return {
        "query": query,
        "count": len(results),
        "endpoints": results,
        "hint": "Use get_endpoint_schema to see full details, then call_api to make requests"
    }


@tool
def get_endpoint_schema(endpoint_id: str) -> dict:
    """
    Get full details and schema for an API endpoint.
    
    Use this after search_endpoints to understand:
    - What parameters the endpoint needs
    - What the endpoint returns
    
    Args:
        endpoint_id: The endpoint ID from search results (e.g., "GET_/pet/{petId}")
    
    Returns:
        Endpoint details including URL, method, parameters
    """
    registry = get_registry()
    details = registry.get_details(endpoint_id)
    
    if not details:
        return {"error": f"Endpoint {endpoint_id} not found"}
    
    return details


@tool
async def call_api(endpoint_id: str, path_params: dict = {}, query_params: dict = {}) -> dict:
    """
    Call an API endpoint and get the response.
    
    Use this after you know which endpoint to call and what parameters it needs.
    Results are cached for performance.
    
    Args:
        endpoint_id: The endpoint ID (e.g., "GET_/pet/{petId}")
        path_params: Parameters to substitute in the path (e.g., {"petId": "1"})
        query_params: Query string parameters (e.g., {"status": "available"})
    
    Returns:
        The API response data
    """
    registry = get_registry()
    cache = get_cache()
    
    # Get endpoint details
    details = registry.get_details(endpoint_id)
    if not details:
        return {"error": f"Endpoint {endpoint_id} not found"}
    
    # Build URL with path params
    url = details["full_url"]
    for key, value in path_params.items():
        url = url.replace(f"{{{key}}}", str(value))
    
    # Check cache
    cache_key = cache.make_key("api", endpoint_id, cache.hash_params({**path_params, **query_params}))
    cached = cache.get(cache_key)
    if cached:
        return {"data": cached, "cached": True}
    
    # Make request
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method=details["method"],
                url=url,
                params=query_params if query_params else None,
                headers={"Accept": "application/json"},
            )
            
            if response.status_code >= 400:
                return {
                    "error": f"API returned {response.status_code}",
                    "message": response.text[:200]
                }
            
            data = response.json()
            
            # Cache successful response
            cache.set(cache_key, data)
            
            return {"data": data, "cached": False}
            
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


@tool
def format_for_widget(data: dict, widget_type: str, config: dict = {}) -> dict:
    """
    Transform API response data into widget format.
    
    Use this to prepare data for display in the UI.
    
    Args:
        data: The raw data from call_api. If the data is a list/array, 
              wrap it as {"items": [...]} before passing.
        widget_type: One of "Table", "BarChart", "LineChart", "MetricCard", "PieChart"
        config: Optional configuration (title, etc.)
    
    Returns:
        Widget-ready data structure
    """
    try:
        # Unwrap if data was passed as {"items": [...]} or {"data": [...]}
        actual_data = data
        if isinstance(data, dict):
            if "items" in data and isinstance(data["items"], list):
                actual_data = data["items"]
            elif "data" in data and isinstance(data["data"], list):
                actual_data = data["data"]
        
        if widget_type == "Table":
            return _format_table(actual_data, config)
        elif widget_type in ["BarChart", "PieChart"]:
            return _format_bar_chart(actual_data, config)
        elif widget_type == "LineChart":
            return _format_line_chart(actual_data, config)
        elif widget_type == "MetricCard":
            return _format_metric(actual_data, config)
        else:
            return {"error": f"Unknown widget type: {widget_type}"}
    except Exception as e:
        return {"error": f"Formatting failed: {str(e)}"}


def _format_table(data: list | dict, config: dict) -> dict:
    """Format data as table."""
    if isinstance(data, list) and len(data) > 0:
        # Array of objects -> table
        if isinstance(data[0], dict):
            columns = list(data[0].keys())
            rows = [[item.get(col, "") for col in columns] for item in data]
            return {
                "component": "Table",
                "data": {"columns": columns, "rows": rows},
                "config": {"title": config.get("title", "Results")}
            }
    elif isinstance(data, dict):
        # Single object -> key-value table
        columns = ["Property", "Value"]
        rows = [[k, str(v)[:100]] for k, v in data.items()]
        return {
            "component": "Table",
            "data": {"columns": columns, "rows": rows},
            "config": {"title": config.get("title", "Details")}
        }
    
    return {"error": "Cannot format as table"}


def _format_bar_chart(data: list | dict, config: dict) -> dict:
    """Format data as bar chart."""
    if isinstance(data, dict):
        # Dict with string keys and numeric values
        labels = list(data.keys())
        values = [v if isinstance(v, (int, float)) else 0 for v in data.values()]
        return {
            "component": "BarChart",
            "data": {"labels": labels, "values": values},
            "config": {"title": config.get("title", "Chart")}
        }
    
    return {"error": "Cannot format as bar chart"}


def _format_line_chart(data: list, config: dict) -> dict:
    """Format data as line chart."""
    if isinstance(data, list) and len(data) > 0:
        # Try to extract numeric fields
        if isinstance(data[0], dict):
            first = data[0]
            label_key = config.get("label_key", list(first.keys())[0])
            value_key = config.get("value_key")
            
            if not value_key:
                # Find first numeric field
                for k, v in first.items():
                    if isinstance(v, (int, float)):
                        value_key = k
                        break
            
            if value_key:
                labels = [str(item.get(label_key, i)) for i, item in enumerate(data)]
                values = [item.get(value_key, 0) for item in data]
                return {
                    "component": "LineChart",
                    "data": {
                        "labels": labels,
                        "datasets": [{"label": value_key, "values": values}]
                    },
                    "config": {"title": config.get("title", "Trend")}
                }
    
    return {"error": "Cannot format as line chart"}


def _format_metric(data: dict, config: dict) -> dict:
    """Format data as metric card."""
    if isinstance(data, dict):
        # Try to find a primary value
        value_key = config.get("value_key") or list(data.keys())[0]
        value = data.get(value_key, "N/A")
        
        return {
            "component": "MetricCard",
            "data": {
                "value": str(value),
                "label": config.get("label", value_key.replace("_", " ").title()),
            },
            "config": {}
        }
    
    return {"error": "Cannot format as metric"}


# Export all tools
ALL_TOOLS = [search_endpoints, get_endpoint_schema, call_api, format_for_widget]
