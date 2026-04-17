"""Carga y validación de archivos JSON de PLC y variables."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

import jsonschema

# Directorio del paquete (donde están los esquemas embebidos)
_PKG_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class PlcConfig:
    """Parámetros de conexión ADS."""

    ams_net_id: str
    port: int
    timeout_ms: int | None = None
    # IP del PLC (opcional; recomendable si difiere de los 4 primeros octetos del AMS Net ID)
    ip_address: str | None = None
    # AMS Net ID del cliente Linux (pyads); debe coincidir con la ruta remota en TwinCAT
    local_ams_net_id: str | None = None


@dataclass(frozen=True)
class VariableSpec:
    """Entrada de la lista blanca de variables."""

    id: str
    ads_path: str
    plc_type: str
    access: str
    string_length: int | None = None


@dataclass(frozen=True)
class AppConfig:
    """Configuración completa validada."""

    plc: PlcConfig
    variables: tuple[VariableSpec, ...]
    by_id: dict[str, VariableSpec]


def directorio_configuracion() -> Path:
    """Ruta del directorio que contiene plc.json y variables.json."""
    raw = os.environ.get("MCP_ADS_CONFIG_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.cwd()


def _cargar_esquema(nombre: str) -> dict[str, Any]:
    ruta = _PKG_DIR / "schemas" / nombre
    with ruta.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=2)
def _esquema_plc() -> dict[str, Any]:
    return _cargar_esquema("plc.schema.json")


@lru_cache(maxsize=2)
def _esquema_variables() -> dict[str, Any]:
    return _cargar_esquema("variables.schema.json")


def _validar(instancia: Any, esquema: dict[str, Any], etiqueta: str) -> None:
    try:
        jsonschema.validate(instance=instancia, schema=esquema)
    except jsonschema.ValidationError as e:
        raise ValueError(f"JSON inválido ({etiqueta}): {e.message}") from e


def cargar_configuracion(
    directorio: Path | None = None,
) -> AppConfig:
    """
    Lee plc.json y variables.json, valida contra JSON Schema y construye índices.

    Lanza ValueError/FileNotFoundError con mensajes claros.
    """
    base = directorio or directorio_configuracion()
    ruta_plc = base / "plc.json"
    ruta_vars = base / "variables.json"
    if not ruta_plc.is_file():
        raise FileNotFoundError(f"No existe {ruta_plc} (MCP_ADS_CONFIG_DIR={base})")
    if not ruta_vars.is_file():
        raise FileNotFoundError(f"No existe {ruta_vars} (MCP_ADS_CONFIG_DIR={base})")

    with ruta_plc.open(encoding="utf-8") as f:
        raw_plc = json.load(f)
    with ruta_vars.open(encoding="utf-8") as f:
        raw_vars = json.load(f)

    _validar(raw_plc, _esquema_plc(), "plc.json")
    _validar(raw_vars, _esquema_variables(), "variables.json")

    plc = PlcConfig(
        ams_net_id=str(raw_plc["ams_net_id"]),
        port=int(raw_plc["port"]),
        timeout_ms=raw_plc.get("timeout_ms"),
        ip_address=raw_plc.get("ip_address"),
        local_ams_net_id=raw_plc.get("local_ams_net_id"),
    )

    variables: list[VariableSpec] = []
    by_id: dict[str, VariableSpec] = {}
    for item in raw_vars:
        vid = str(item["id"])
        if vid in by_id:
            raise ValueError(f"id duplicado en variables.json: {vid}")
        spec = VariableSpec(
            id=vid,
            ads_path=str(item["ads_path"]),
            plc_type=str(item["plc_type"]),
            access=str(item["access"]),
            string_length=item.get("string_length"),
        )
        variables.append(spec)
        by_id[vid] = spec

    return AppConfig(plc=plc, variables=tuple(variables), by_id=by_id)


def iter_variables_escribibles(cfg: AppConfig) -> Iterator[VariableSpec]:
    """Variables declaradas como read_write."""
    for v in cfg.variables:
        if v.access == "read_write":
            yield v
