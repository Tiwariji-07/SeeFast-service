"""
Conversation Memory
===================

Maintains conversation history for contextual interactions.

Features:
- Short-term memory (current session in Redis)
- Long-term memory (archived conversations in ChromaDB)
- Retrieval of relevant past context
"""

import json
from typing import Optional
from datetime import datetime

from app.services.cache import get_cache, CacheService


class ConversationMemory:
    """Manages conversation context per session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.cache = get_cache()
        self._history_key = f"session:{session_id}:history"
    
    def add_turn(self, user_message: str, assistant_message: str, widgets: list = None):
        """Add a conversation turn to memory."""
        turn = {
            "user": user_message,
            "assistant": assistant_message,
            "widgets": widgets or [],
            "timestamp": datetime.now().isoformat(),
        }
        
        # Get existing history
        history = self.get_history()
        history.append(turn)
        
        # Keep only last 20 turns
        history = history[-20:]
        
        # Save back
        self.cache.set(self._history_key, history, ttl=3600)  # 1 hour
    
    def get_history(self) -> list[dict]:
        """Get conversation history."""
        return self.cache.get(self._history_key) or []
    
    def get_context_messages(self, limit: int = 5) -> list[dict]:
        """Get recent messages formatted for the agent."""
        history = self.get_history()
        messages = []
        
        for turn in history[-limit:]:
            messages.append({
                "role": "user",
                "content": turn["user"]
            })
            messages.append({
                "role": "assistant", 
                "content": turn["assistant"]
            })
        
        return messages
    
    def get_context_summary(self) -> str:
        """Get a brief summary of the conversation context."""
        history = self.get_history()
        if not history:
            return "This is a new conversation."
        
        recent = history[-3:]
        summary_parts = []
        for turn in recent:
            summary_parts.append(f"User asked: {turn['user'][:100]}")
        
        return "Previous context: " + " | ".join(summary_parts)
    
    def clear(self):
        """Clear conversation history."""
        self.cache.delete(self._history_key)


# Memory cache per session
_memories: dict[str, ConversationMemory] = {}


def get_memory(session_id: str) -> ConversationMemory:
    """Get or create memory for a session."""
    if session_id not in _memories:
        _memories[session_id] = ConversationMemory(session_id)
    return _memories[session_id]
