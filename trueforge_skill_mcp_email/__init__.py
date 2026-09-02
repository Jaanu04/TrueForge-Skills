"""TrueForge Email Skill + MCP proof of concept.

This package deliberately bypasses the LangGraph orchestration loop. TrueForge
owns conversational orchestration through Skills, while the MCP server exposes
validated Email capabilities backed by the existing Resulticks integrations.
"""

__all__ = ["__version__"]
__version__ = "1.0.0"
