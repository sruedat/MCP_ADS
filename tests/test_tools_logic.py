"""Tests de la lógica de herramientas con cliente ADS simulado."""

from __future__ import annotations

from typing import Any

import pytest

from mcp_ads.config import AppConfig, PlcConfig, VariableSpec
from mcp_ads.server import _tool_read, _tool_write


class _ClienteFalso:
    """Simula AdsPlcClient sin pyads."""

    def __init__(self) -> None:
        self.escritos: list[tuple[str, str, int | None, Any]] = []

    def leer_por_ruta(self, ads_path: str, plc_type: str, string_length: int | None) -> Any:
        if ads_path == "MAIN.nContador":
            return 7
        raise RuntimeError("fallo simulado")

    def escribir_por_ruta(
        self, ads_path: str, plc_type: str, string_length: int | None, valor: Any
    ) -> None:
        self.escritos.append((ads_path, plc_type, string_length, valor))


def _cfg_minima() -> AppConfig:
    plc = PlcConfig(ams_net_id="1.1.1.1.1.1", port=851)
    vars_ = (
        VariableSpec("c", "MAIN.nContador", "DINT", "read_write"),
        VariableSpec("solo", "MAIN.x", "BOOL", "read"),
    )
    by_id = {v.id: v for v in vars_}
    return AppConfig(plc=plc, variables=vars_, by_id=by_id)


def test_ads_read_parcial(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg_minima()
    monkeypatch.setattr("mcp_ads.server.cargar_configuracion", lambda: cfg)
    cli = _ClienteFalso()
    out = _tool_read(cli, {"ids": ["c", "desconocido"]})
    assert out["ok"] is False
    assert out["values"]["c"] == 7
    assert "desconocido" in (out["errors"] or {})


def test_ads_write_rechaza_solo_lectura(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg_minima()
    monkeypatch.setattr("mcp_ads.server.cargar_configuracion", lambda: cfg)
    cli = _ClienteFalso()
    with pytest.raises(ValueError, match="solo lectura"):
        _tool_write(cli, {"id": "solo", "value": True})


def test_ads_write_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg_minima()
    monkeypatch.setattr("mcp_ads.server.cargar_configuracion", lambda: cfg)
    cli = _ClienteFalso()
    r = _tool_write(cli, {"id": "c", "value": 42})
    assert r["ok"] is True
    assert cli.escritos == [("MAIN.nContador", "DINT", None, 42)]
