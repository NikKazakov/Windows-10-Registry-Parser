import logging

from .common import *
from .cell import *

log = logging.getLogger()


class Regf(Block):
    def __init__(self, buf, offset):
        super().__init__(buf, offset, dict(
            signature=(0, STR, 4),
            sequence1=(4, DWORD),
            sequence2=(8, DWORD),
            last_written=(12, FILETIME),
            major_version=(20, DWORD),
            minor_version=(24, DWORD),
            file_type=(28, DWORD),
            file_format=(32, DWORD),
            root_cell_offset=(36, DWORD),
            hive_bins_data_size=(40, DWORD),
            clustering_factor=(44, DWORD),
            file_name=(48, STR, 64, 'utf-16-le'),
            rmid=(112, GUID),
            logid=(128, GUID),
            flags=(144, DWORD),
            tmid=(148, GUID),
            guid_signature=(164, STR, 4),
            last_reorganized=(168, FILETIME),
            checksum=(508, DWORD),
            thawtmid=(4040, GUID),
            thawrmid=(4056, GUID),
            thawlogid=(4056, DWORD),
            boot_type=(4088, DWORD),
            boot_recover=(4092, DWORD)
        ))


class Hbin(Block):
    def __init__(self, buf, offset):
        super().__init__(buf, offset, dict(
            signature=(0, STR, 4),
            offset=(4, DWORD),
            size=(8, DWORD),
            timestamp=(20, FILETIME),
            spare=(28, DWORD)
        ))
        self._cells = None

    @property
    def cells(self):
        if self._cells is None:
            self._cells = Cells(self._buf, self._offset + 32, self.size)
        return self._cells


class Hbins(LazyList):
    def __init__(self, buf, offset, max_size):
        super().__init__(buf, offset, Hbin, max_size=max_size)


class RegistryValue:
    def __init__(self, keyvalue):
        if not isinstance(keyvalue, KeyValue):
            raise ValueError(f'Expected KeyValue, got {type(keyvalue)}')
        
        self._keyvalue = keyvalue
    
    @property
    def name(self):
        return self._keyvalue.name
    
    @property
    def value(self):
        return self._keyvalue.data
    
    @property
    def type(self):
        return self._keyvalue.type_str
    
    def __str__(self):
        return f'{self.type} {self.name}={self.value}'
    
    def __repr__(self):
        return f'RegistryValue(name="{self.name}", value="{self.value}", type="{self.type}")'


class RegistryKey:
    def __init__(self, keynode, path):
        if not isinstance(keynode, KeyNode):
            raise ValueError(f'Expected KeyNode, got {type(keynode)}')
        
        self._keynode = keynode
        self._path = path
        self._subkeys = None
        self._values = None

    @property
    def name(self):
        return self._keynode.name
        
    @property
    def subkeys(self):
        if self._subkeys is None:
            name = '' if self.name == 'ROOT' else self.name
            self._subkeys = KeyedList({i.name: RegistryKey(i, self._path + name + '\\') for i in self._unpack_subkeys(self._keynode.subkeys)})
        return self._subkeys
    
    def _unpack_subkeys(self, cell):
        if isinstance(cell, PointersList) or isinstance(cell, list):
            r = []
            for i in cell:
                r.extend(self._unpack_subkeys(i))
            return r
        elif isinstance(cell, KeyNode):
            return [cell,]
        else:
            print(type(cell))
            raise SystemError
    
    def __getitem__(self, key):
        if not isinstance(key, str) and not isinstance(key, int):
            raise TypeError(f'Expected str, got {type(key)}')
        
        return self.subkeys[key]

    @property
    def values(self):
        if self._values is None:
            self._values = KeyedList({i.name: RegistryValue(i) for i in self._keynode.values})
        return self._values
    
    def __str__(self):
        return f'{self._path}{self.name}, {len(self.values)} values, {len(self.subkeys)} subkeys'
    
    def __repr__(self):
        return f'RegistryKey(name="{self.name}", path="{self._path}")'


class Registry:
    def __init__(self, buf):
        self._buf = buf
        self._regf = None
        self._hbins = None
    
    @classmethod
    def from_file(cls, fd):
        return cls(fd.read())
    
    @classmethod
    def from_path(cls, path):
        with open(path, 'rb') as f:
            return cls.from_file(f)

    @property
    def regf(self):
        if self._regf is None:
            self._regf = Regf(self._buf, 0)
        return self._regf

    @property
    def hbins(self):
        if self._hbins is None:
            self._hbins = Hbins(self._buf, 4096, self.regf.hive_bins_data_size)
        return self._hbins

    def __str__(self) -> str:
        return f'Registry {self.regf.file_name}'

    @property
    def root(self):
        return RegistryKey(self.hbins[0].cells[0], '')
    
    def get(self, path):
        keynode = self.root
        path = path.strip('\\').split('\\')
        for name in path:
            keynode = keynode[name]
        return keynode
