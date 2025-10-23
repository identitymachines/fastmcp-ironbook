"""
FastMCP-IronBook Integration Package

Provides Iron Book agent-based security for FastMCP servers.
"""

__version__ = "0.1.0"

from .middleware import ClientInfoMiddleware
from .agent import get_or_register_agent, identify_agent, extract_agent_capabilities
from .policy import enforce_policy
from .decorator import setup, require_policy

__all__ = [
    "ClientInfoMiddleware",
    "get_or_register_agent",
    "identify_agent",
    "extract_agent_capabilities",
    "enforce_policy",
    "setup",
    "require_policy",
]

