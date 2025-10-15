"""
grai.build - Declarative knowledge graph modeling tool.
"""

try:
    from importlib.metadata import version

    __version__ = version("grai-build")
except Exception:
    # Fallback for development or if package metadata is not available
    __version__ = "0.3.2"
