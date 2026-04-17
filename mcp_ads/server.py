"""Servidor MCP de bajo nivel: herramientas ADS."""

from __future__ import annotations

import json
import logging
from typing import Any

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from mcp_ads import __version__ as mcp_ads_version
from mcp_ads.ads_connection import AdsPlcClient
from mcp_ads.config import cargar_configuracion
from mcp_ads.plc_types import normalizar_valor_escritura

logger = logging.getLogger(__name__)

# Límite de variables por llamada a ads_read
_MAX_IDS_LECTURA = 32


def crear_servidor(cliente: AdsPlcClient) -> Server:
    """Registra herramientas MCP enlazadas al cliente ADS (variables.json se recarga por herramienta)."""
    server = Server(
        name="beckhoff-ads",
        version=mcp_ads_version,
        instructions=(
            "Servidor MCP para TwinCAT ADS. Usa ids declarados en variables.json; "
            "no inventes rutas ADS. ads_write solo en variables read_write."
        ),
    )

    @server.list_tools()
    async def _listar_herramientas(_req: types.ListToolsRequest) -> types.ListToolsResult:
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name="ads_read",
                    title="Leer variables ADS",
                    description=(
                        "Lee una o varias variables del PLC por su id lógico "
                        f"(máximo {_MAX_IDS_LECTURA} a la vez). Solo ids listados en variables.json."
                    ),
                    inputSchema={
                        "type": "object",
                        "required": ["ids"],
                        "properties": {
                            "ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                                "maxItems": _MAX_IDS_LECTURA,
                            }
                        },
                    },
                ),
                types.Tool(
                    name="ads_write",
                    title="Escribir variable ADS",
                    description=(
                        "Escribe una variable por id lógico. Requiere access=read_write en variables.json "
                        "y valor compatible con plc_type."
                    ),
                    inputSchema={
                        "type": "object",
                        "required": ["id", "value"],
                        "properties": {
                            "id": {"type": "string"},
                            "value": {},
                        },
                    },
                ),
                types.Tool(
                    name="ads_status",
                    title="Estado de conexión ADS",
                    description="Comprueba conectividad con el PLC (read_state).",
                    inputSchema={"type": "object", "properties": {}},
                ),
                types.Tool(
                    name="ads_browse_symbols",
                    title="Listar símbolos ADS (descubrimiento)",
                    description=(
                        "Lista símbolos expuestos por el runtime (get_all_symbols). "
                        "En TwinCAT 3 suele funcionar bien; en TwinCAT 2 puede no estar disponible o ser limitado."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prefix": {"type": "string", "description": "Prefijo de nombre a filtrar"},
                            "limit": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 5000,
                                "default": 500,
                            },
                        },
                    },
                ),
            ]
        )

    @server.call_tool()
    async def _invocar_herramienta(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        args = arguments or {}
        try:
            if name == "ads_read":
                return [_texto(_tool_read(cliente, args))]
            if name == "ads_write":
                return [_texto(_tool_write(cliente, args))]
            if name == "ads_status":
                return [_texto(_tool_status(cliente))]
            if name == "ads_browse_symbols":
                return [_texto(_tool_browse(cliente, args))]
        except Exception as e:  # noqa: BLE001
            logger.exception("Error en herramienta %s", name)
            return [_texto({"ok": False, "error": str(e)})]
        raise ValueError(f"Herramienta desconocida: {name}")

    return server


def _texto(payload: Any) -> types.TextContent:
    return types.TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))


def _tool_read(cliente: AdsPlcClient, args: dict[str, Any]) -> dict[str, Any]:
    """Recarga variables.json en cada llamada para reflejar cambios sin reiniciar el proceso MCP."""
    cfg = cargar_configuracion()
    ids = args.get("ids")
    if not isinstance(ids, list) or not ids:
        raise ValueError("ids debe ser un array no vacío")
    if len(ids) > _MAX_IDS_LECTURA:
        raise ValueError(f"Máximo {_MAX_IDS_LECTURA} ids por llamada")

    resultados: dict[str, Any] = {}
    errores: dict[str, str] = {}
    for vid in ids:
        if not isinstance(vid, str):
            errores[str(vid)] = "id debe ser cadena"
            continue
        spec = cfg.by_id.get(vid)
        if spec is None:
            errores[vid] = "id no permitido (no está en variables.json)"
            continue
        try:
            val = cliente.leer_por_ruta(spec.ads_path, spec.plc_type, spec.string_length)
            resultados[vid] = val
        except Exception as e:  # noqa: BLE001
            errores[vid] = str(e)
    return {"ok": len(errores) == 0, "values": resultados, "errors": errores or None}


def _tool_write(cliente: AdsPlcClient, args: dict[str, Any]) -> dict[str, Any]:
    """Recarga variables.json antes de validar access (read_write) y escribir."""
    cfg = cargar_configuracion()
    vid = args.get("id")
    if not isinstance(vid, str):
        raise ValueError("id debe ser cadena")
    if "value" not in args:
        raise ValueError("falta value")
    spec = cfg.by_id.get(vid)
    if spec is None:
        raise ValueError("id no permitido (no está en variables.json)")
    if spec.access != "read_write":
        raise ValueError("esta variable es solo lectura (access=read)")
    valor_norm = normalizar_valor_escritura(spec.plc_type, args["value"], spec.string_length)
    cliente.escribir_por_ruta(spec.ads_path, spec.plc_type, spec.string_length, valor_norm)
    return {"ok": True, "id": vid}


def _tool_status(cliente: AdsPlcClient) -> dict[str, Any]:
    return cliente.estado_dispositivo()


def _tool_browse(cliente: AdsPlcClient, args: dict[str, Any]) -> dict[str, Any]:
    prefijo = args.get("prefix") or ""
    if prefijo is not None and not isinstance(prefijo, str):
        raise ValueError("prefix debe ser cadena")
    limite = args.get("limit", 500)
    if isinstance(limite, bool) or not isinstance(limite, int):
        raise ValueError("limit debe ser entero")
    if not 1 <= limite <= 5000:
        raise ValueError("limit fuera de rango [1, 5000]")
    filas = cliente.listar_simbolos(prefijo, limite)
    return {"ok": True, "count": len(filas), "symbols": filas}


def opciones_inicializacion(server: Server) -> InitializationOptions:
    """InitializationOptions coherentes con el servidor."""
    return InitializationOptions(
        server_name=server.name,
        server_version=server.version or "0.1.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
        instructions=server.instructions,
        website_url=server.website_url,
        icons=server.icons,
    )
