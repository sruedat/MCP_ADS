"""Paquete del servidor MCP para acceso ADS a TwinCAT."""

__all__ = ["__version__"]

try:
    from importlib.metadata import version

    __version__ = version("mcp-ads")
except Exception:  # pragma: no cover - desarrollo sin instalación editable
    __version__ = "0.0.0"
