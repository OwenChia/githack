# -*- coding: utf-8 -*-
import struct


class StructureMeta(type):
    def __init__(self, clsname, bases, clsdict):
        fields = getattr(self, '_fields_', [])
        byte_order = ''
        offset = 0
        for fieldfmt, fieldname, *func in fields:
            if fieldfmt.startswith(('<', '>', '!', '@')):
                byte_order = fieldfmt[0]
                fieldfmt = fieldfmt[1:]
            fieldfmt = byte_order + fieldfmt

            field = StructField(fieldfmt, offset)
            size = struct.calcsize(fieldfmt)

            if len(func) == 1 and callable(func[0]):
                field = StructField(fieldfmt, offset, func=func[0])

            setattr(self, fieldname, field)
            offset += size
        setattr(self, 'struct_size', offset)


class StructField:
    def __init__(self, fmt, offset, *, func=None):
        self.format = fmt
        self.offset = offset
        self.func = func

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            r = struct.unpack_from(self.format, instance._buffer, self.offset)
            if callable(self.func):
                r = [self.func(it) for it in r]
            return r[0] if len(r) == 1 else r


class Structure(metaclass=StructureMeta):
    def __init__(self, bytedata):
        self._buffer = memoryview(bytedata)

    @classmethod
    def from_file(cls, fd):
        return cls(fd.read(cls.struct_size))
