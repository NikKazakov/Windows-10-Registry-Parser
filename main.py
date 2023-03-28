import argparse
import json
import logging

# from common import json_serialize
# from parts import *


from reg import Registry

logging.basicConfig(level=logging.INFO)


parser = argparse.ArgumentParser( prog='parse windows 10 registry' )
parser.add_argument('filename')

args = parser.parse_args()

with open(args.filename, 'rb') as f:
    r = Registry.from_file(f)


# Launch with "python .\main.py r\SYSTEM"

print(r)
# Registry SYSTEM
print(r.regf)
# reg.registry.Regf at 0x0, contains 24 fields
print(r.hbins)
# reg.registry.Hbins at 0x1000, loaded 0 items, 0/17375232 bytes
print(f'Total hbins: {len(r.hbins)}')
# Total hbins: 3674
print(r.hbins[0])
# reg.registry.Hbin at 0x1000, contains 5 fields
print(r.hbins[0].cells[0])
# reg.cell.KeyNode at 0x1020, ROOT
print(r.hbins[0].cells[0].subkeys[0])
# reg.cell.KeyNode at 0x1170, ActivationBroker
print(r.hbins[0].cells[0].subkeys[0].subkeys[0])
# reg.cell.KeyNode at 0x1358, Plugins
print(r.hbins[0].cells[0].subkeys[0].subkeys[0].subkeys[0].values[0])
# reg.cell.KeyValue at 0x1628, (Default)
print(r.hbins[0].cells[0].subkeys[0].subkeys[0].subkeys[0].values[1])
# reg.cell.KeyValue at 0x16a0, TypeID
