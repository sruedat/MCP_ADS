# MCP_ADS

Servidor **MCP** (Model Context Protocol) en **Python** que accede a variables **TwinCAT** mediante el protocolo **ADS**, usando [pyads](https://github.com/stlehmann/pyads). Transporte: **stdio** (adecuado para Cursor y contenedores con `docker run -i`).

## Características

- Lectura y escritura por **id lógico** definido en `variables.json` (lista blanca).
- Tipos PLC declarados en JSON; **escritura** con validación previa según `plc_type`.
- `ads_status` para comprobar conectividad (`read_state`).
- `ads_browse_symbols` para listar símbolos (`get_all_symbols`; ver limitaciones TC2/TC3 en [docs/twincat-tc2-tc3.md](docs/twincat-tc2-tc3.md)).

## Requisitos

- **Python 3.11+**
- En **Windows**: biblioteca **TcAdsDll** (instalación TwinCAT / ADS). Sin ella, `import pyads` fallará en el arranque de operaciones ADS.
- En **Linux**: pyads incluye **adslib** en el wheel; adecuado para Ubuntu/Docker.

## Instalación

```bash
pip install -e ".[dev]"
```

Variables de entorno:

| Variable | Descripción |
|----------|-------------|
| `MCP_ADS_CONFIG_DIR` | Carpeta con `plc.json` y `variables.json` (si no se define, se usa el directorio actual). |
| `MCP_ADS_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, etc. |

## Configuración

Ejemplos en [examples/plc.json](examples/plc.json) y [examples/variables.json](examples/variables.json).

Esquemas JSON Schema en [schemas/](schemas/) (y copia embebida en `mcp_ads/schemas/` para validación en tiempo de ejecución).

## Uso local

```bash
set MCP_ADS_CONFIG_DIR=C:\ruta\a\config   # Windows PowerShell: $env:MCP_ADS_CONFIG_DIR="..."
python -m mcp_ads
```

O el script de consola:

```bash
mcp-ads
```

### Verificación rápida (ADS sin MCP)

Con el PLC accesible y `plc.json` / `variables.json` listos:

```bash
# PowerShell (ejemplo: carpeta examples/wsl-tc3; ajusta IPs/AMS a tu red)
$env:MCP_ADS_CONFIG_DIR = "$PWD\examples\wsl-tc3"
python verificar_ads.py
```

Esto comprueba `ads_status` y una lectura por variable declarada. Hay un ejemplo para **WSL + PLC remoto** en [examples/wsl-tc3/](examples/wsl-tc3/) (`ip_address` y `local_ams_net_id` en `plc.json`).

En **Windows** hace falta el runtime ADS (**TcAdsDll**); para probar contra un PLC en otra máquina suele ser más simple ejecutar `python verificar_ads.py` **dentro de WSL** (mismo entorno que ya te funcionó con pyads).

## Cursor (stdio)

Ejemplo de fragmento para la configuración del servidor MCP (ajuste rutas):

```json
{
  "mcpServers": {
    "beckhoff-ads": {
      "command": "python",
      "args": ["-m", "mcp_ads"],
      "cwd": "C:\\Users\\srued\\Documents\\MCP_ADS",
      "env": {
        "MCP_ADS_CONFIG_DIR": "C:\\ruta\\a\\carpeta\\config",
        "MCP_ADS_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Con Docker (Ubuntu en imagen; requiere `-i` y la imagen `mcp-ads:local` construida antes con `docker build -t mcp-ads:local .` o `docker compose build`). Detalle y ejemplos para Cursor: [docs/docker-ubuntu.md](docs/docker-ubuntu.md).

```json
{
  "mcpServers": {
    "beckhoff-ads": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-v", "/ruta/config:/config:ro", "-e", "MCP_ADS_CONFIG_DIR=/config", "mcp-ads:local"]
    }
  }
}
```

## Herramientas MCP

| Herramienta | Descripción |
|-------------|-------------|
| `ads_read` | `{ "ids": ["id1", "id2"] }` — lee hasta 32 variables por llamada. |
| `ads_write` | `{ "id": "...", "value": ... }` — solo si `access` es `read_write`. |
| `ads_status` | `{}` — estado ADS/dispositivo. |
| `ads_browse_symbols` | `{ "prefix": "", "limit": 500 }` — descubrimiento de símbolos. |

## Documentación

- [Arquitectura](docs/architecture.md)
- [Docker y Ubuntu](docs/docker-ubuntu.md)
- [TwinCAT 2 vs 3 y browse](docs/twincat-tc2-tc3.md)

## Tests

```bash
python -m pytest tests -q
```

## Solución de problemas

1. **`FileNotFoundError: TcAdsDll.dll`** (Windows): instale TwinCAT o el componente ADS y/o defina `TWINCAT3DIR` según la documentación de pyads.
2. **Timeout / sin conexión**: verifique **AMS Net ID**, **puerto** (851 TC3, 801 TC2 típico), rutas AMS y firewall (**48898** TCP/UDP).
3. **Variable no encontrada**: confirme la **ruta simbólica** exacta en TwinCAT y que el **PLC esté en RUN**.

## Licencia

MIT (según `pyproject.toml`).
