"""
grai.build - Declarative knowledge graph modeling tool.
"""

try:
    from importlib.metadata import version

    __version__ = version("grai-build")
except Exception:
    __version__ = "0.0.0.dev0"
