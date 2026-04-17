# TwinCAT 2 vs TwinCAT 3 y ADS

Este servidor usa **pyads**, que abstrae gran parte del protocolo ADS, pero el comportamiento del **runtime** y los **puertos** difieren entre versiones.

## Puertos ADS habituales

| Contexto | Puerto típico | Notas |
|----------|---------------|--------|
| TwinCAT 3 — PLC proyecto 1 | **851** (`PORT_TC3PLC1` en pyads) | El más usado en ejemplos. |
| TwinCAT 2 | **801** u otros según configuración | Ver documentación del sistema concreto. |

El puerto correcto siempre debe coincidir con el **AMS router** y el servicio ADS del destino.

## Rutas simbólicas

- TwinCAT 3 suele usar rutas tipo `MAIN.variable`, `GVL.nombre`, etc.
- TwinCAT 2 puede diferir en convenciones de nombres y estructura del proyecto.

Use siempre las rutas que muestre **TwinCAT** en el editor o las que ya funcionen con otras herramientas ADS.

## Herramienta `ads_browse_symbols`

Internamente usa `Connection.get_all_symbols()` de pyads.

- En **TwinCAT 3**, normalmente devuelve la tabla de símbolos expuesta por el runtime.
- En **TwinCAT 2**, la disponibilidad y el formato pueden ser **limitados** o **no soportados** según versión y configuración. Si falla, use variables declaradas manualmente en `variables.json` y la herramienta `ads_read`.

## Enrutamiento AMS

Cuando el MCP corre en **otro equipo** que el runtime TwinCAT:

1. El **AMS Net ID** del PLC debe ser alcanzable (rutas estáticas o `pyads.add_route_to_plc` según política de red).
2. Ajuste firewalls para el tráfico ADS (véase README principal).

## Referencias

- [pyads — documentación](https://pyads.readthedocs.io/)
- Documentación Beckhoff sobre ADS y AMS Net ID (versión correspondiente a su TwinCAT).
