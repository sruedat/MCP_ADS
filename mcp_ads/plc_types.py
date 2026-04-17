"""Mapeo de tipos PLC declarados en JSON a tipos ctypes compatibles con pyads."""

from __future__ import annotations

from ctypes import (
    c_bool,
    c_char,
    c_double,
    c_float,
    c_int8,
    c_int16,
    c_int32,
    c_ubyte,
    c_uint8,
    c_uint16,
    c_uint32,
)
from typing import Any, Type, Union

# Tipos simples: mismos ctypes que usa pyads.constants (sin importar el paquete pyads).
_SIMPLE: dict[str, type] = {
    "BOOL": c_bool,
    "BYTE": c_ubyte,
    "WORD": c_uint16,
    "DWORD": c_uint32,
    "SINT": c_int8,
    "USINT": c_uint8,
    "INT": c_int16,
    "UINT": c_uint16,
    "DINT": c_int32,
    "UDINT": c_uint32,
    "REAL": c_float,
    "LREAL": c_double,
}


def resolver_tipo_plc(plc_type: str, string_length: int | None) -> Union[type, Any]:
    """
    Devuelve el descriptor de tipo para read_by_name / write_by_name.

    Para STRING devuelve un array c_char de tamaño string_length + 1 (nulo ADS).
    """
    if plc_type == "STRING":
        if string_length is None:
            raise ValueError("plc_type STRING requiere string_length en la configuración")
        return c_char * (string_length + 1)
    base = _SIMPLE.get(plc_type)
    if base is None:
        raise ValueError(f"plc_type no soportado: {plc_type}")
    return base


def normalizar_valor_escritura(plc_type: str, valor: Any, string_length: int | None) -> Any:
    """Convierte y valida el valor entrante (JSON/MCP) antes de enviarlo al PLC."""
    if plc_type == "BOOL":
        if isinstance(valor, bool):
            return valor
        if valor in (0, 1):
            return bool(valor)
        raise TypeError("BOOL: se esperaba boolean o 0/1")

    if plc_type in {"BYTE", "WORD", "DWORD", "USINT", "UINT", "UDINT"}:
        n = int(valor)
        limites: dict[str, tuple[int, int]] = {
            "BYTE": (0, 255),
            "USINT": (0, 255),
            "WORD": (0, 65535),
            "UINT": (0, 65535),
            "DWORD": (0, 4_294_967_295),
            "UDINT": (0, 4_294_967_295),
        }
        if plc_type in limites:
            lo, hi = limites[plc_type]
            if not lo <= n <= hi:
                raise ValueError(f"{plc_type}: fuera de rango [{lo}, {hi}]")
        return n

    if plc_type == "SINT":
        n = int(valor)
        if not -128 <= n <= 127:
            raise ValueError("SINT: fuera de rango [-128, 127]")
        return n

    if plc_type == "INT":
        n = int(valor)
        if not -32768 <= n <= 32767:
            raise ValueError("INT: fuera de rango [-32768, 32767]")
        return n

    if plc_type == "DINT":
        n = int(valor)
        if not -2147483648 <= n <= 2147483647:
            raise ValueError("DINT: fuera de rango")
        return n

    if plc_type in {"REAL", "LREAL"}:
        return float(valor)

    if plc_type == "STRING":
        if string_length is None:
            raise ValueError("STRING requiere string_length")
        if not isinstance(valor, str):
            raise TypeError("STRING: se esperaba cadena")
        encoded = valor.encode("utf-8")
        if len(encoded) > string_length:
            raise ValueError(f"STRING: excede string_length={string_length}")
        return valor

    raise ValueError(f"plc_type no soportado para escritura: {plc_type}")


def pythonizar_valor_lectura(plc_type: str, raw: Any) -> Any:
    """Convierte el resultado de pyads a tipos JSON-serializables."""
    if plc_type == "BOOL":
        return bool(raw)
    if plc_type == "STRING":
        if raw is None:
            return ""
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace").rstrip("\x00")
        return str(raw).rstrip("\x00")
    if plc_type in {"REAL", "LREAL"}:
        return float(raw)
    if plc_type in _SIMPLE:
        return int(raw)
    return raw
