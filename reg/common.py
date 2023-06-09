import datetime
import enum
import logging
import struct
import uuid


log = logging.getLogger()


WORD = enum.auto()
DWORD = enum.auto()
DWORD_BIG = enum.auto()
QWORD = enum.auto()
INT = enum.auto()
FILETIME = enum.auto()
GUID = enum.auto()
STR = enum.auto()
BYTES = enum.auto()

# Constants to convert from filetime
FILETIME_EPOCH = datetime.datetime(1601, 1, 1)


class Block:
    '''
    Represents consecutive byte fields
    Lazy-loads fields provided in constructor via __getattribute__ magic
    Provider generalized __str__ for all heirs
    '''
    def __init__(self, buf, offset, fields):
        self._buf = buf
        self._offset = offset
        self._fields = fields
        self._fields_loaded = {}
    
    def unpack(self, offset, ftype, *opts):
        if ftype in [STR, BYTES]:
            if len(opts) < 1:
                raise ValueError(f'Invalid size specified for {ftype} at {offset}')
            size = opts[0]
            format = f'{size}s'
        elif ftype == WORD:
            format = 'H'
            size = 2
        elif ftype == DWORD:
            format = 'I'
            size = 4
        elif ftype == DWORD_BIG:
            format = '>I'
            size = 4
        elif ftype == QWORD:
            format = 'Q'
            size = 8
        elif ftype == INT:
            format = 'i'
            size = 4
        elif ftype == FILETIME:
            format = 'Q'
            size = 8
        elif ftype == GUID:
            format = '16s'
            size = 16

        try:
            value = struct.unpack(format, self._buf[self._offset+offset : self._offset+offset+size])[0]
        except struct.error as e:
            log.critical(f'{self._offset}+{offset}/{len(self._buf)} {ftype}:{size}')
            log.critical(f'{self._buf[self._offset+offset-20:self._offset+offset+80]}')
            raise e

        if ftype == STR:
            encoding = opts[1] if len(opts) == 2 else 'ascii'
            try:
                r = value.decode(encoding).strip('\x00')
            except UnicodeDecodeError:
                # In regedit invalid values are just silent
                r = '...'  
            return r
        elif ftype == FILETIME:
            return str(FILETIME_EPOCH + datetime.timedelta(microseconds=(value // 10)))
        elif ftype == GUID:
            return str(uuid.UUID(bytes=value))
        elif ftype == QWORD:
            return hex(value)
        # Maybe we want to print bytes prettier
        # elif ftype == BYTES:
        #     return ''.join([ '%0.2x'%i for i in value ])
        return value

    def __getattribute__(self, name: str):
        if name[0] != '_':
            if name in self._fields and name not in self._fields_loaded:
                self._fields_loaded[name] = self.unpack(*self._fields[name])

            if name in self._fields_loaded:
                return self._fields_loaded[name]
        
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if name[0] != '_':
            self._fields_loaded[name] = value

        super().__setattr__(name, value)
    
    def items(self):
        for key in self._fields:
            yield key, self.__getattribute__(key)

    def __str__(self):
        return f'{self.__class__.__module__}.{self.__class__.__qualname__} at {hex(self._offset)}, contains {len(self._fields)} fields'


class LazyList:
    '''
    Iterable structure with lazy-loading
    Override _load_next to change what should go into this
    '''
    def __init__(self, buf, offset, children, max_size=-1, max_items=-1):
        self._buf = buf
        self._offset = offset
        self._children = children
        self._max_size = max_size
        self._current_size = 0
        self._max_items = max_items
        self._current = -1
        self._loaded = []
    
    def __getitem__(self, key):
        if not isinstance(key, int):
            raise TypeError(f'Expected int, got {type(key)}')
        if key < 0:
            raise IndexError(f'Negative index is not supported')
        
        while key >= len(self._loaded):
            if self._has_next:
                item = self._load_next()
                self._loaded.append(item)
            else:
                raise IndexError(f'Index out of range. Total {len(self._loaded)} loaded')
        
        return self._loaded[key]
    
    @property
    def _has_next(self):
        if self._max_size > 0:
            return self._max_size > self._current_size
        else:
            return self._max_items > len(self._loaded)

    def _load_next(self):
        item = self._children(self._buf, self._offset + self._current_size)
        self._current_size += item.size
        return item
    
    def __iter__(self):
        self._current = -1
        return self
    
    def __next__(self):
        self._current += 1
        try:
            return self[self._current]
        except IndexError:
            raise StopIteration

    def __len__(self):
        for item in self:
            pass
        return len(self._loaded)

    def __str__(self):
        r = f'{self.__class__.__module__}.{self.__class__.__qualname__} at {hex(self._offset)}, loaded {len(self._loaded)}'
        if self._max_items > 0:
            r += f'/{self._max_items} items.'
        else:
            r += f' items, {self._current_size}/{self._max_size} bytes'
        return r


class KeyedList:
    def __init__(self, items):
        if not isinstance(items, dict):
            raise ValueError(f'Expected dict, got {type(items)}')
        
        self.items = items
        self.values = list(items.values())
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return self.items[key]
        elif isinstance(key, int):
            return self.values[key]
        else:
            raise TypeError(f'Expected str or int, got {type(key)}')
    
    def __iter__(self):
        return self.values.__iter__()
    
    def __repr__(self):
        return str(self.values)

    def __len__(self):
        return self.values.__len__()