"""
Endpoint Registry
=================

Stores API endpoints in ChromaDB for semantic search.

Responsibilities:
1. Index endpoints with embeddings
2. Search endpoints by natural language query
3. Retrieve endpoint details by ID
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import Optional
import json

from app.adapters.swagger_parser import Endpoint, SwaggerParser
from app.config import settings


class EndpointRegistry:
    """Registry for API endpoints with vector search."""
    
    def __init__(self):
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        
        # Use sentence-transformers for embeddings
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        
        # Get or create collection for endpoints
        self.collection = self.client.get_or_create_collection(
            name="api_endpoints",
            embedding_function=self.embedding_fn,
            metadata={"description": "API endpoints from Swagger specs"}
        )
        
        self._endpoints_cache: dict[str, Endpoint] = {}
        self._parser: Optional[SwaggerParser] = None
    
    async def load_swagger(self, swagger_url: str) -> int:
        """Load endpoints from a Swagger spec into the registry."""
        # Parse Swagger
        self._parser = SwaggerParser(swagger_url)
        endpoints = await self._parser.load()
        
        # Clear existing endpoints (for fresh reload)
        try:
            self.client.delete_collection("api_endpoints")
            self.collection = self.client.get_or_create_collection(
                name="api_endpoints",
                embedding_function=self.embedding_fn,
            )
        except Exception:
            pass
        
        # Add endpoints to collection
        ids = []
        documents = []
        metadatas = []
        
        for endpoint in endpoints:
            ids.append(endpoint.id)
            documents.append(endpoint.searchable_text)
            metadatas.append({
                "path": endpoint.path,
                "method": endpoint.method,
                "summary": endpoint.summary,
                "tags": json.dumps(endpoint.tags),
            })
            self._endpoints_cache[endpoint.id] = endpoint
        
        if ids:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
        
        return len(endpoints)
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search for endpoints matching query."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
        )
        
        found = []
        if results["ids"] and results["ids"][0]:
            for i, endpoint_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                found.append({
                    "id": endpoint_id,
                    "path": metadata.get("path", ""),
                    "method": metadata.get("method", ""),
                    "summary": metadata.get("summary", ""),
                    "relevance_score": 1 - (results["distances"][0][i] if results["distances"] else 0),
                })
        
        return found
    
    def get_details(self, endpoint_id: str) -> Optional[dict]:
        """Get full details for an endpoint."""
        endpoint = self._endpoints_cache.get(endpoint_id)
        if not endpoint:
            return None
        
        return {
            "id": endpoint.id,
            "path": endpoint.path,
            "method": endpoint.method,
            "summary": endpoint.summary,
            "description": endpoint.description,
            "tags": endpoint.tags,
            "full_url": self._parser.get_full_url(endpoint) if self._parser else "",
            "parameters": [
                {
                    "name": p.name,
                    "in": p.location,
                    "required": p.required,
                    "type": p.param_type,
                    "description": p.description,
                }
                for p in endpoint.parameters
            ],
        }
    
    def get_endpoint_count(self) -> int:
        """Get the number of indexed endpoints."""
        return self.collection.count()


# Singleton instance
_registry: Optional[EndpointRegistry] = None


def get_registry() -> EndpointRegistry:
    """Get or create the registry singleton."""
    global _registry
    if _registry is None:
        _registry = EndpointRegistry()
    return _registry
