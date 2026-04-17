"""Tests de tipos PLC (sin pyads)."""

from __future__ import annotations

import pytest

from mcp_ads.plc_types import normalizar_valor_escritura, resolver_tipo_plc


def test_resolver_string_requiere_longitud() -> None:
    with pytest.raises(ValueError):
        resolver_tipo_plc("STRING", None)


def test_normalizar_bool() -> None:
    assert normalizar_valor_escritura("BOOL", True, None) is True
    assert normalizar_valor_escritura("BOOL", 1, None) is True


def test_normalizar_int_rango() -> None:
    with pytest.raises(ValueError):
        normalizar_valor_escritura("INT", 40000, None)


def test_normalizar_string_longitud() -> None:
    normalizar_valor_escritura("STRING", "ok", 10)
    with pytest.raises(ValueError):
        normalizar_valor_escritura("STRING", "x" * 20, 10)
