"""Cliente ADS fino sobre pyads (importación diferida para entornos sin DLL local)."""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

from mcp_ads.config import PlcConfig
from mcp_ads.plc_types import pythonizar_valor_lectura, resolver_tipo_plc

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Valores habituales (pyads.constants / Beckhoff ADS)
_NOMBRES_ADS_STATE: dict[int, str] = {
    0: "ADSSTATE_INVALID",
    1: "ADSSTATE_IDLE",
    2: "ADSSTATE_RESET",
    3: "ADSSTATE_INIT",
    4: "ADSSTATE_START",
    5: "ADSSTATE_RUN",
    6: "ADSSTATE_STOP",
    7: "ADSSTATE_SAVECFG",
    8: "ADSSTATE_LOADCFG",
}


def _import_pyads() -> Any:
    """Importa pyads solo en tiempo de ejecución (p. ej. Linux con adslib o Windows con TcAdsDll)."""
    import pyads  # type: ignore[import-untyped]

    return pyads


def _con_reintento(op: Callable[[], T], intentos: int = 2) -> T:
    """Reintento mínimo ante fallos transitorios de red."""
    ultimo: Exception | None = None
    for i in range(intentos):
        try:
            return op()
        except Exception as e:  # noqa: BLE001 - ADS puede lanzar varias excepciones
            ultimo = e
            logger.warning("Operación ADS falló (intento %s/%s): %s", i + 1, intentos, e)
    assert ultimo is not None
    raise ultimo


class AdsPlcClient:
    """Conexión pyads opcionalmente persistente."""

    def __init__(self, plc: PlcConfig) -> None:
        self._plc = plc
        self._conn: Any | None = None

    def _asegurar_abierta(self) -> Any:
        pyads = _import_pyads()
        if self._conn is not None and self._conn.is_open:
            return pyads
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:  # noqa: BLE001
                pass
        # En Linux, la AMS del cliente debe coincidir con la ruta remota en TwinCAT
        if self._plc.local_ams_net_id:
            try:
                from pyads import ads as _pyads_ads  # type: ignore[import-untyped]

                if _pyads_ads.linux:
                    pyads.set_local_address(self._plc.local_ams_net_id)
            except Exception as e:  # noqa: BLE001
                logger.warning("No se pudo aplicar local_ams_net_id: %s", e)

        self._conn = pyads.Connection(
            self._plc.ams_net_id,
            self._plc.port,
            ip_address=self._plc.ip_address,
        )
        if self._plc.timeout_ms is not None:
            self._conn.default_timeout = self._plc.timeout_ms / 1000.0
        self._conn.open()
        return pyads

    def cerrar(self) -> None:
        if self._conn is not None:
            try:
                if self._conn.is_open:
                    self._conn.close()
            except Exception:  # noqa: BLE001
                pass
            self._conn = None

    def estado_dispositivo(self) -> dict[str, Any]:
        """Devuelve estado ADS y del dispositivo si la conexión es posible."""
        _import_pyads()
        self._asegurar_abierta()
        assert self._conn is not None
        try:
            st = self._conn.read_state()
            if st is None:
                return {"ok": False, "error": "read_state devolvió None"}
            ads_state, dev_state = st
            return {
                "ok": True,
                "ams_net_id": self._plc.ams_net_id,
                "port": self._plc.port,
                "ads_state": int(ads_state),
                "device_state": int(dev_state),
                "ads_state_str": _NOMBRES_ADS_STATE.get(int(ads_state), f"UNKNOWN({ads_state})"),
            }
        except Exception as e:  # noqa: BLE001
            self.cerrar()
            return {"ok": False, "error": str(e)}

    def leer_por_ruta(self, ads_path: str, plc_type: str, string_length: int | None) -> Any:
        """Lee una variable por ruta simbólica."""
        _import_pyads()
        self._asegurar_abierta()
        assert self._conn is not None
        dtype = resolver_tipo_plc(plc_type, string_length)

        def _read() -> Any:
            return self._conn.read_by_name(ads_path, dtype)

        raw = _con_reintento(_read)
        return pythonizar_valor_lectura(plc_type, raw)

    def escribir_por_ruta(
        self,
        ads_path: str,
        plc_type: str,
        string_length: int | None,
        valor: Any,
    ) -> None:
        """Escribe un valor ya normalizado."""
        _import_pyads()
        self._asegurar_abierta()
        assert self._conn is not None
        dtype = resolver_tipo_plc(plc_type, string_length)

        def _write() -> None:
            self._conn.write_by_name(ads_path, valor, dtype)

        _con_reintento(_write)

    def listar_simbolos(self, prefijo: str = "", limite: int = 500) -> list[dict[str, Any]]:
        """
        Lista símbolos del dispositivo (TwinCAT 3 típico; en TC2 puede fallar o ser limitado).

        :param prefijo: filtra por nombre (prefijo), comparación sensible a mayúsculas/minúsculas del PLC
        :param limite: máximo de filas devueltas
        """
        _import_pyads()
        self._asegurar_abierta()
        assert self._conn is not None

        def _list() -> list[Any]:
            return self._conn.get_all_symbols()

        simbolos = _con_reintento(_list)
        salida: list[dict[str, Any]] = []
        for s in simbolos:
            nombre = getattr(s, "name", "") or ""
            if prefijo and not str(nombre).startswith(prefijo):
                continue
            salida.append(
                {
                    "name": nombre,
                    "symtype": getattr(s, "symtype", None) or getattr(s, "symbol_type", None),
                    "comment": getattr(s, "comment", None),
                    "index_group": getattr(s, "index_group", None),
                    "index_offset": getattr(s, "index_offset", None),
                }
            )
            if len(salida) >= limite:
                break
        return salida
