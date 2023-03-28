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


class Registry:
    def __init__(self, buf):
        self._buf = buf
        self._regf = None
        self._hbins = None
    
    @classmethod
    def from_file(cls, fd):
        return cls(fd.read())
    
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

    def repr(self, depth=0):
        for hbin in self.hbins:
            for cell in hbin.cells:
                print(cell)
                if isinstance(cell, KeyNode):
                    cell._repr(self.regf.file_name)
                break
            break