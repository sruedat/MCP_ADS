import pyads

pyads.set_local_address("192.168.1.11.1.1")

AMS_PLC = "192.168.1.21.1.1"  # ajústalo si tu Net ID es otro
IP_PLC = "192.168.1.21"

plc = pyads.Connection(AMS_PLC, pyads.PORT_TC3PLC1)
plc.ip_address = IP_PLC

plc.open()
try:
    valor = plc.read_by_name("MAIN.test", pyads.PLCTYPE_BOOL)
    print("MAIN.test =", valor)
finally:
    plc.close()
