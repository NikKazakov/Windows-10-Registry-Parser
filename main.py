import argparse


parser = argparse.ArgumentParser( prog='parse windows 10 registry' )
parser.add_argument('filename')

args = parser.parse_args()


# Main usable class is reg.Registry
from reg import Registry

# It provides two constructors besides main one
# Via filepath
r = Registry.from_path(args.filename)
# Via file descriptor
with open(args.filename, 'rb') as f:
    r = Registry.from_file(f)
# And via raw buffer
with open(args.filename, 'rb') as f:
    buf = f.read()
r = Registry(buf)

# # It exposes main (ROOT) KeyNode as .root property
# print(r.root)  # ROOT, 0 values, 17 subkeys

# # KeyNodes are exposed via RegistryKey class
# # It provides .name, .subkeys, .values properties and key/index access to subkeys
# print(r.root.name)   # ROOT
# print(r.root.subkeys)  # [RegistryKey(name="ActivationBroker", path="\"), RegistryKey(name="ControlSet001", path="\"),]
# print(r.root.values)  # []
# print(r.root['ActivationBroker'])  # \ActivationBroker, 0 values, 1 subkeys
# print(r.root[0])  # \ActivationBroker, 0 values, 1 subkeys
# print(r.root[0][0][0])  # \ActivationBroker\Plugins\{REDACTED}, 2 values, 0 subkeys
# # Registry class also provides .get method to access a KeyNode by its full path
# key = r.get('\ActivationBroker\Plugins\{REDACTED}')
# print(key)  # \ActivationBroker\Plugins\{REDACTED}, 2 values, 0 subkeys
# print(repr(key))  # RegistryKey(name="{REDACTED}", path="\ActivationBroker\Plugins\")

# # Values of each KeyNode can be accessed via .values property. It also provides key/index access
# print(key.values)  # [RegistryValue(name="(Default)", value="DevicePairingActivationBrokerPlugin", type="REG_SZ"), RegistryValue(name="TypeID", value="{REDACTED}", type="REG_SZ")]
# print(key.values[0])  # REG_SZ (Default)=DevicePairingActivationBrokerPlugin
# print(r.root[0][0][0].values[1])  # REG_SZ TypeID={REDACTED}
# print(key.values['(Default)'])  # REG_SZ (Default)=DevicePairingActivationBrokerPlugin
# print(repr(r.root[0][0][0].values[1]))  # RegistryValue(name="TypeID", value="{REDACTED}", type="REG_SZ")


# Simple loop that prints all registry keys with their path and values
def recursive_print(key):
    print(key)
    for i in key.values:
        print('\t' + str(i))
    for i in key.subkeys:
        recursive_print(i)

# Uncomment next line to launch it. WARNING - a lot of output
recursive_print(r.root)
