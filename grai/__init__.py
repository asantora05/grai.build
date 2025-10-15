"""
grai.build - Declarative knowledge graph modeling tool.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("grai-build")
except PackageNotFoundError:
    # Package not installed - user needs to run: pip install -e .
    __version__ = "unknown (not installed)"
