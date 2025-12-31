"""
Swagger Parser
==============

Parses OpenAPI/Swagger JSON specs and extracts endpoints for the registry.

Key responsibilities:
1. Fetch and parse Swagger JSON
2. Extract endpoint information (path, method, summary, params)
3. Create searchable text for embeddings
"""

import httpx
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class EndpointParameter:
    """A parameter for an API endpoint."""
    name: str
    location: str  # path, query, body, header
    required: bool
    param_type: str
    description: str = ""


@dataclass
class Endpoint:
    """Represents a single API endpoint."""
    id: str  # Unique identifier (e.g., "get_/pet/{petId}")
    path: str
    method: str
    summary: str
    description: str
    tags: list[str]
    parameters: list[EndpointParameter] = field(default_factory=list)
    response_schema: Optional[dict] = None
    
    @property
    def searchable_text(self) -> str:
        """Create text for embedding/search."""
        tags_str = ", ".join(self.tags)
        params_str = ", ".join([p.name for p in self.parameters])
        return f"{self.summary}. {self.description}. Tags: {tags_str}. Parameters: {params_str}. Path: {self.path}"


class SwaggerParser:
    """Parse Swagger/OpenAPI spec and extract endpoints."""
    
    def __init__(self, swagger_url: str):
        self.swagger_url = swagger_url
        self.spec: dict = {}
        self.endpoints: list[Endpoint] = []
        self.base_url: str = ""
        
    async def load(self) -> list[Endpoint]:
        """Load and parse the Swagger spec."""
        # Fetch the spec
        async with httpx.AsyncClient() as client:
            response = await client.get(self.swagger_url)
            response.raise_for_status()
            self.spec = response.json()
        
        # Extract base URL
        host = self.spec.get("host", "")
        base_path = self.spec.get("basePath", "")
        schemes = self.spec.get("schemes", ["https"])
        self.base_url = f"{schemes[0]}://{host}{base_path}"
        
        # Parse endpoints
        self.endpoints = self._extract_endpoints()
        return self.endpoints
    
    def load_sync(self) -> list[Endpoint]:
        """Synchronous version for initialization."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.load())
    
    def _extract_endpoints(self) -> list[Endpoint]:
        """Extract all endpoints from the spec."""
        endpoints = []
        paths = self.spec.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                # Skip non-HTTP methods (like 'parameters')
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                endpoint_id = f"{method.upper()}_{path}"
                
                # Extract parameters
                parameters = []
                for param in details.get("parameters", []):
                    parameters.append(EndpointParameter(
                        name=param.get("name", ""),
                        location=param.get("in", "query"),
                        required=param.get("required", False),
                        param_type=param.get("type", "string"),
                        description=param.get("description", ""),
                    ))
                
                # Extract response schema (for 200 response)
                response_schema = None
                responses = details.get("responses", {})
                if "200" in responses:
                    response_schema = responses["200"].get("schema", {})
                
                endpoint = Endpoint(
                    id=endpoint_id,
                    path=path,
                    method=method.upper(),
                    summary=details.get("summary", ""),
                    description=details.get("description", ""),
                    tags=details.get("tags", []),
                    parameters=parameters,
                    response_schema=response_schema,
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    def get_full_url(self, endpoint: Endpoint) -> str:
        """Get the full URL for an endpoint."""
        return f"{self.base_url}{endpoint.path}"
