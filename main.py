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


print(r)
print(r.regf)
print(r.hbins)
print(len(r.hbins))
print(r.hbins[0])
print(r.hbins[0].cells[0])
print(r.hbins[0].cells[0].subkeys[0])
print(r.hbins[0].cells[0].subkeys[0].subkeys[0])
print(r.hbins[0].cells[0].subkeys[0].subkeys[0].subkeys[0].values[0])
print(r.hbins[0].cells[0].subkeys[0].subkeys[0].subkeys[0].values[1])
print()
