#!/usr/bin/env python3
"""
Comprueba plc.json + variables.json y la conexión ADS (sin protocolo MCP).

Uso (desde la raíz del repo, con el paquete instalado en modo editable):

  set MCP_ADS_CONFIG_DIR=examples\\wsl-tc3
  python verificar_ads.py

En WSL (ajusta la ruta):

  export MCP_ADS_CONFIG_DIR=/mnt/c/Users/tu_usuario/Documents/MCP_ADS/examples/wsl-tc3
  python verificar_ads.py
"""

from __future__ import annotations

import os
import sys

from mcp_ads.ads_connection import AdsPlcClient
from mcp_ads.config import cargar_configuracion


def main() -> int:
    try:
        cfg = cargar_configuracion()
    except Exception as e:  # noqa: BLE001
        print(f"[verificar_ads] Error cargando configuración: {e}", file=sys.stderr)
        return 1

    cliente = AdsPlcClient(cfg.plc)
    try:
        estado = cliente.estado_dispositivo()
        print("ads_status:", estado)
        if not estado.get("ok"):
            print("[verificar_ads] Conexión ADS falló.", file=sys.stderr)
            return 2

        for v in cfg.variables:
            valor = cliente.leer_por_ruta(v.ads_path, v.plc_type, v.string_length)
            print(f"  {v.id} ({v.ads_path}) = {valor!r}")
    except Exception as e:  # noqa: BLE001
        print(f"[verificar_ads] Error ADS: {e}", file=sys.stderr)
        return 3
    finally:
        cliente.cerrar()

    print("OK: configuración y lectura ADS correctas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
