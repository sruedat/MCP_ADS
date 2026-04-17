import pyads

AMS_PLC = "192.168.1.21.1.1"   # AMS Net ID del runtime en la VM (ajústalo si el tuyo es otro)
IP_PLC = "192.168.1.21"

# Debe ser EL MISMO AMS que en la ruta remota de TwinCAT (cliente)
pyads.set_local_address("192.168.1.11.1.1")

plc = pyads.Connection(AMS_PLC, pyads.PORT_TC3PLC1)
plc.ip_address = IP_PLC
plc.default_timeout = 5.0  # segundos (opcional)

plc.open()
try:
    local = plc.get_local_address()
    print("AMS local usada por adslib:", local)
    print("Estado:", plc.read_state())
finally:
    plc.close()
