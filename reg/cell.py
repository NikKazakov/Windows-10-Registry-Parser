import enum
import logging

from .common import *


log = logging.getLogger()


FLAG_KEY_VOLATILE = 0x0001
FLAG_KEY_HIVE_EXIT = 0x0002
FLAG_KEY_HIVE_ENTRY = 0x0004
FLAG_KEY_NO_DELETE = 0x0008
FLAG_KEY_SYM_LINK = 0x0010
FLAG_KEY_COMP_NAME = 0x0020
FLAG_KEY_PREDEF_HANDLE = 0x0040

FLAG_VALUE_COMP_NAME = 0x0001

class RegType(enum.IntEnum):
    REG_NONE = 0x00000000 	
    REG_SZ = 0x00000001
    REG_EXPAND_SZ = 0x00000002 	
    REG_BINARY = 0x00000003 	
    REG_DWORD = 0x00000004 	
    REG_DWORD_BIG_ENDIAN = 0x00000005 	
    REG_LINK = 0x00000006 	
    REG_MULTI_SZ = 0x00000007 	
    REG_RESOURCE_LIST = 0x00000008 	
    REG_FULL_RESOURCE_DESCRIPTOR = 0x00000009 	
    REG_RESOURCE_REQUIREMENTS_LIST = 0x0000000a 	
    REG_QWORD = 0x0000000b

    def values():
        return [i.value for i in RegType]


class Cell(Block):
    def __init__(self, buf, offset):
        super().__init__(buf, offset, dict(
            size=(0, DWORD),
            signature=(4, STR, 2)
        ))
        self.allocated = self.size < 0
        self.size = abs(self.size)


class PointersList(LazyList):
    def __init__(self, buf, offset, children, max_size=-1, max_items=-1, step=4):
        self.pointers = Block(buf, offset, {})
        self._step = step
        super().__init__(buf, offset, children, max_size, max_items)
   
    def _load_next(self):
        item_offset = self.pointers.unpack(self._current_size, DWORD)
        self._current_size += self._step
        item = self._children(self._buf, 4096 + item_offset)
        return item
CELL_TYPES = dict()


class IndexLeaf(PointersList):
    def __init__(self, buf, offset):
        header = Cell(buf, offset)
        header._fields['number_of_items'] = (6, WORD)
        super().__init__(buf, 8+offset, KeyNode, max_items=header.number_of_items)
CELL_TYPES['li'] = IndexLeaf


class FastLeaf(PointersList):
    def __init__(self, buf, offset):
        header = Cell(buf, offset)
        header._fields['number_of_items'] = (6, WORD)
        super().__init__(buf, 8+offset, KeyNode, max_items=header.number_of_items, step=8)
CELL_TYPES['lf'] = FastLeaf


class HashLeaf(PointersList):
    def __init__(self, buf, offset):
        header = Cell(buf, offset)
        header._fields['number_of_items'] = (6, WORD)
        super().__init__(buf, 8+offset, KeyNode, max_items=header.number_of_items, step=8)
CELL_TYPES['lh'] = HashLeaf


class IndexRoot(PointersList):
    def __init__(self, buf, offset):
        header = Cell(buf, offset)
        header._fields['number_of_items'] = (6, WORD)
        super().__init__(buf, 8+offset, None, max_items=header.number_of_items)
    
    def _load_next(self):
        item_offset = self.pointers.unpack(self._current_size, DWORD)
        self._current_size += self._step
        cell = Cell(self._buf, 4096 + item_offset)
        item = CELL_TYPES[cell.signature](self._buf, 4096 + item_offset)
        return item
CELL_TYPES['ri'] = IndexRoot


class KeyNode(Cell):
    def __init__(self, buf, offset):
        super().__init__(buf, offset)
        self._fields.update(dict(
            flags=(6, WORD),
            last_written=(8, FILETIME),
            access_bits=(16, DWORD),
            parent=(20, DWORD),
            number_of_subkeys=(24, DWORD),
            number_of_volatile_subkeys=(28, DWORD),
            subkeys_list_offset=(32, DWORD),
            volatile_subkeys_list_offset=(36, DWORD),
            number_of_key_values=(40, DWORD),
            key_values_list_offset=(44, DWORD),
            key_security_offset=(48, DWORD),
            class_name_offset=(52, DWORD),
            largest_subkey_name_length=(56, DWORD),
            largest_subkey_class_name_length=(60, DWORD),
            largest_value_name_length=(64, DWORD),
            largest_value_data_size=(68, DWORD),
            workvar=(72, DWORD),
            key_name_length=(76, WORD),
            class_name_length=(78, WORD),
        ))

        if FLAG_KEY_COMP_NAME&self.flags > 0:
            encoding = 'ascii'
        else:
            encoding = 'utf-16-le'
        self._fields['name'] = (80, STR, self.key_name_length, encoding)
        self._subkeys = None
        self._values = None

    @property
    def subkeys(self):
        if self._subkeys is None:
            if self.number_of_subkeys > 0 and self.number_of_subkeys != 0xffffffff:
                cell = Cell(self._buf, 4096 + self.subkeys_list_offset)
                self._subkeys = CELL_TYPES[cell.signature](self._buf, 4096 + self.subkeys_list_offset)
            else:
                self._subkeys = []
        return self._subkeys
  
    @property
    def values(self):
        if self._values is None:
            if self.number_of_key_values > 0 and self.number_of_key_values != 0xffffffff:
                self._values = PointersList(self._buf, 4096 + 4 + self.key_values_list_offset, KeyValue, max_items=self.number_of_key_values)
            else:
                self._values = []
        return self._values

    def __str__(self):
        return f'{self.__class__.__module__}.KeyNode at {hex(self._offset)}, {self.name}'
    
    def _repr(self, path):
        new_path = f'{path}/{self.name}'
        print(new_path)
        for i in self.items():
            print(i)
        for i in self.subkeys:
            i._repr(new_path)
            break
            
        # # for i in self.items():
        # #     print(i)
        # r = self.key_name + '\n'
        # for i in self.subkeys:
        #     for line in i._repr().split('\n')
        #     print(i._repr())
        #     r += f'\t{i._repr()}'
        #     break
        # return r
CELL_TYPES['nk'] = KeyNode


class KeyValue(Cell):
    def __init__(self, buf, offset):
        super().__init__(buf, offset)
        self._fields.update(dict(
            name_length=(6, WORD),
            data_size=(8, DWORD),
            data_offset=(12, DWORD),
            data_type=(16, DWORD),
            flags=(20, WORD),
            spare=(22, WORD)
        ))

        if self.name_length > 0:
            if FLAG_VALUE_COMP_NAME&self.flags > 0:
                encoding = 'ascii'
            else:
                encoding = 'utf-16-le'
            self._fields['name'] = (24, STR, self.name_length, encoding)
        else:
            self._fields_loaded['name'] = '(Default)'
        
        self._data = None
    
    @property
    def data(self):
        if self._data is None:
            if self.data_size >= 0x80000000:
                self._data = self.data_offset
            elif self._buf[4096 + self.data_offset + 4: 4096 + self.data_offset + 6] == b'db':
                self._data = BigData(self._buf, 4096 + self.data_offset).data
            else:
                if self.data_type in [RegType.REG_SZ, RegType.REG_EXPAND_SZ, RegType.REG_MULTI_SZ]:
                    format = [STR, self.data_size, 'utf-16-le']
                elif self.data_type == RegType.REG_DWORD:
                    format = [DWORD]
                elif self.data_type == RegType.REG_DWORD_BIG_ENDIAN:
                    format = [DWORD_BIG]
                elif self.data_type == RegType.REG_QWORD:
                    format = [QWORD]
                elif self.data_type in [RegType.REG_NONE, RegType.REG_BINARY, RegType.REG_LINK, RegType.REG_RESOURCE_LIST, RegType.REG_FULL_RESOURCE_DESCRIPTOR, RegType.REG_RESOURCE_REQUIREMENTS_LIST]:
                    format = [BYTES, self.data_size]
                elif self.data_type in RegType.values():
                    print(RegType(self.data_type).name)
                    raise SystemError
                else:  # UNKNOWN
                    format = [BYTES, self.data_size]

                self._data = Cell(self._buf, 4096 + self.data_offset).unpack(4, *format)                
                
                if self.data_type == RegType.REG_MULTI_SZ:
                    self._data = self._data.split('\x00')
        return self._data

    @property
    def type_str(self):
        if self.data_type in RegType.values():
            return RegType(self.data_type).name
        else:
            return f'UNKNOWN ({hex(self.data_type)})'

    def __str__(self):
        return f'{self.__class__.__module__}.KeyValue at {hex(self._offset)}, name="{self.name}" type="{self.type_str}" value="{self.data}"'
CELL_TYPES['vk'] = KeyValue


class KeySecurity(Cell):
    def __init__(self, buf, offset):
        raise NotImplementedError
        super().__init__(buf, offset)
CELL_TYPES['sk'] = KeySecurity


class BigData(Cell):
    def __init__(self, buf, offset):
        super().__init__(buf, offset)
        self._fields['number_of_segments'] = (6, WORD)
        self._fields['segments_list_offset'] = (8, DWORD)
        self._data = None
    
    @property
    def data(self):
        if self._data is None:
            self._data = b''
            current_size = 0
            segments_list = Cell(self._buf, 4096 + self.segments_list_offset)
            for i in range(self.number_of_segments):
                data_segment_offset = segments_list.unpack(4+current_size, DWORD)
                data_segment = Cell(self._buf, 4096 + data_segment_offset).unpack(4, BYTES, 16344)
                self._data += data_segment
        return self._data
CELL_TYPES['db'] = BigData


class Cells(LazyList):
    def __init__(self, buf, offset, max_size):
        super().__init__(buf, offset, None, max_size=max_size)

    def _load_next(self):
        cell = Cell(self._buf, self._offset + self._current_size)
        item = CELL_TYPES[cell.signature](self._buf, self._offset + self._current_size)
        self._current_size += item.size
        return item

