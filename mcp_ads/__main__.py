"""Punto de entrada: servidor MCP por stdio."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from mcp.server.stdio import stdio_server

from mcp_ads.ads_connection import AdsPlcClient
from mcp_ads.config import cargar_configuracion
from mcp_ads.server import crear_servidor, opciones_inicializacion


def main() -> None:
    """Arranca el servidor MCP (stdio)."""
    nivel = os.environ.get("MCP_ADS_LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(
        level=getattr(logging, nivel, logging.WARNING),
        stream=sys.stderr,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    try:
        cfg = cargar_configuracion()
    except Exception as e:  # noqa: BLE001
        print(f"[mcp-ads] Error cargando configuración: {e}", file=sys.stderr)
        sys.exit(1)

    cliente = AdsPlcClient(cfg.plc)
    server = crear_servidor(cliente)
    opts = opciones_inicializacion(server)

    async def _run() -> None:
        try:
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, opts, raise_exceptions=False)
        finally:
            cliente.cerrar()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
