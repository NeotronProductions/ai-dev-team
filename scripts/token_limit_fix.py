"""
Token Limit Fix for OpenAI API Calls

This module provides utilities to reduce token usage and handle rate limits.
"""

import os
from pathlib import Path
from typing import Optional

# Token limits for different models (tokens per minute)
TOKEN_LIMITS = {
    'gpt-4o-mini': 200000,
    'gpt-4o': 2000000,
    'gpt-4-turbo': 2000000,
    'gpt-3.5-turbo': 2000000,
}

# Approximate tokens per character (rough estimate: 1 token ≈ 4 characters)
CHARS_PER_TOKEN = 4

def estimate_tokens(text: str) -> int:
    """Estimate token count from text (rough approximation)"""
    return len(text) // CHARS_PER_TOKEN

def truncate_text(text: str, max_tokens: int) -> str:
    """Truncate text to fit within token limit"""
    max_chars = max_tokens * CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... truncated to fit token limit ...]"

def limit_file_content(file_path: Path, max_chars: int = 5000) -> str:
    """Read file content with size limit"""
    if not file_path.exists():
        return ""
    
    try:
        content = file_path.read_text(encoding='utf-8')
        if len(content) > max_chars:
            # Try to keep the beginning (most important) and truncate
            return content[:max_chars] + "\n\n[... file truncated ...]"
        return content
    except Exception as e:
        return f"[Error reading file: {e}]"

def get_model_token_limit(model_name: Optional[str] = None) -> int:
    """Get token limit for a model"""
    if not model_name:
        model_name = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # Extract base model name (remove any suffixes)
    base_model = model_name.split(':')[0].split('/')[-1]
    
    return TOKEN_LIMITS.get(base_model, 200000)  # Default to 200k

def reduce_context_size(context: str, max_tokens: int = 150000) -> str:
    """
    Reduce context size to fit within token limits.
    Keeps the most important parts (beginning) and truncates the rest.
    """
    estimated_tokens = estimate_tokens(context)
    
    if estimated_tokens <= max_tokens:
        return context
    
    # Calculate how much to keep (leave some buffer)
    keep_ratio = (max_tokens * 0.9) / estimated_tokens  # Keep 90% of limit
    max_chars = int(len(context) * keep_ratio)
    
    truncated = context[:max_chars]
    truncated += "\n\n[... context truncated to fit token limits ...]"
    
    return truncated

def get_safe_context_size(model_name: Optional[str] = None) -> int:
    """
    Get a safe context size (in tokens) that leaves room for:
    - Agent backstories
    - Task descriptions
    - API response
    - Buffer for safety
    """
    token_limit = get_model_token_limit(model_name)
    
    # Reserve:
    # - 20% for agent backstories and task descriptions
    # - 20% for API response
    # - 10% buffer
    # = 50% reserved, so use 50% for context
    
    return int(token_limit * 0.5)
