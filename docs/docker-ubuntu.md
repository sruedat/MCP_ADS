# Despliegue en Ubuntu y Docker

El servidor está pensado para ejecutarse en Linux (Ubuntu) con **pyads** y la biblioteca **adslib** incluida en el wheel de pyads para Linux.

## Requisitos de red

- El contenedor o la VM Ubuntu debe alcanzar el **AMS Net ID** del PLC por la red configurada (enrutamiento AMS / firewall).
- Los puertos típicos de comunicación ADS incluyen **TCP/UDP 48898** y el **puerto ADS del runtime** (p. ej. **851** para PLC1 en TwinCAT 3, **801** habitual en TwinCAT 2).

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `MCP_ADS_CONFIG_DIR` | Directorio absoluto que contiene `plc.json` y `variables.json`. |
| `MCP_ADS_LOG_LEVEL` | Nivel de log de Python (`DEBUG`, `INFO`, `WARNING`, …). Por defecto `WARNING`. |

## Construcción de la imagen

En la raíz del repositorio:

```bash
docker build -t mcp-ads:local .
```

## Ejecución con stdio

MCP por stdio requiere **stdin abierto** (`-i`). Ejemplo de prueba manual:

```bash
docker run --rm -i \
  -v /ruta/local/config:/config:ro \
  -e MCP_ADS_CONFIG_DIR=/config \
  mcp-ads:local
```

### Docker Compose (recomendado en el repo)

Desde la raíz del proyecto (donde está `docker-compose.yml`):

```bash
docker compose build
docker compose run --rm -i mcp-ads
```

Equivale a `docker run` con el volumen `./examples/wsl-tc3:/config:ro` y las variables definidas en el archivo.

### Cursor (Windows / Docker Desktop)

1. Construya la imagen al menos una vez: `docker compose build` o `docker build -t mcp-ads:local .`
2. En `.cursor/mcp.json`, use `docker run` o `docker compose run` con `-i`, `cwd` apuntando a la raíz del repo y volumen hacia su carpeta de config (p. ej. `examples/wsl-tc3`).

Fragmento de ejemplo (`cwd` debe ser la carpeta del clon; ajuste la ruta del volumen si no usa `wsl-tc3`):

```json
{
  "mcpServers": {
    "beckhoff-ads": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "examples/wsl-tc3:/config:ro",
        "-e",
        "MCP_ADS_CONFIG_DIR=/config",
        "-e",
        "MCP_ADS_LOG_LEVEL=INFO",
        "mcp-ads:local"
      ],
      "cwd": "C:\\Users\\SU_USUARIO\\Documents\\MCP_ADS"
    }
  }
}
```

Con **Compose** (misma `cwd` en la raíz del repo):

```json
{
  "mcpServers": {
    "beckhoff-ads": {
      "command": "docker",
      "args": ["compose", "run", "--rm", "-i", "mcp-ads"],
      "cwd": "C:\\Users\\SU_USUARIO\\Documents\\MCP_ADS"
    }
  }
}
```

**Red:** el contenedor debe alcanzar el PLC; en `plc.json` use `ip_address` / rutas AMS acordes (el `local_ams_net_id` del cliente debe existir en la tabla de rutas del PLC hacia el host donde corre Docker).

Para **Cursor** u otro cliente, el proceso debe ejecutarse con stdio: `docker run -i ...` o `docker compose run -i ...` y el `ENTRYPOINT` arranca `python3 -m mcp_ads`.

## Instalación nativa en Ubuntu (sin Docker)

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export MCP_ADS_CONFIG_DIR=/ruta/a/tu/config
python -m mcp_ads
```

## Montaje de configuración

Coloque en `MCP_ADS_CONFIG_DIR`:

- `plc.json` — véase [../examples/plc.json](../examples/plc.json)
- `variables.json` — véase [../examples/variables.json](../examples/variables.json)

Los esquemas de validación están en [../schemas/](../schemas/) y copiados en el paquete `mcp_ads/schemas/` para distribución.
