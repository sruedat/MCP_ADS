"""Tests de carga y validación de configuración."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_ads.config import cargar_configuracion

_EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
_EJEMPLO_WSL = _EXAMPLES / "wsl-tc3"


def test_cargar_ejemplos_valida() -> None:
    cfg = cargar_configuracion(_EXAMPLES)
    assert cfg.plc.ams_net_id == "192.168.0.10.1.1"
    assert cfg.plc.port == 851
    assert cfg.plc.ip_address is None
    assert cfg.plc.local_ams_net_id is None
    assert "contador" in cfg.by_id
    assert cfg.by_id["nombre"].access == "read"


def test_ejemplo_wsl_tc3_valida() -> None:
    """Carpeta de ejemplo para PLC remoto desde WSL."""
    cfg = cargar_configuracion(_EJEMPLO_WSL)
    assert cfg.plc.local_ams_net_id == "192.168.1.11.1.1"
    assert cfg.plc.ip_address == "192.168.1.21"
    assert "test" in cfg.by_id


def test_plc_opciones_red(tmp_path: Path) -> None:
    import json

    (tmp_path / "plc.json").write_text(
        json.dumps(
            {
                "ams_net_id": "192.168.1.21.1.1",
                "port": 851,
                "ip_address": "192.168.1.21",
                "local_ams_net_id": "192.168.1.11.1.1",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "variables.json").write_text(
        json.dumps(
            [
                {
                    "id": "t",
                    "ads_path": "MAIN.test",
                    "plc_type": "BOOL",
                    "access": "read",
                }
            ]
        ),
        encoding="utf-8",
    )
    cfg = cargar_configuracion(tmp_path)
    assert cfg.plc.ip_address == "192.168.1.21"
    assert cfg.plc.local_ams_net_id == "192.168.1.11.1.1"


def test_id_duplicado_rechazado(tmp_path: Path) -> None:
    import json

    (tmp_path / "plc.json").write_text(
        json.dumps({"ams_net_id": "1.2.3.4.5.6", "port": 851}), encoding="utf-8"
    )
    dup = [
        {"id": "a", "ads_path": "MAIN.a", "plc_type": "BOOL", "access": "read"},
        {"id": "a", "ads_path": "MAIN.b", "plc_type": "BOOL", "access": "read"},
    ]
    (tmp_path / "variables.json").write_text(json.dumps(dup), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicado"):
        cargar_configuracion(tmp_path)
