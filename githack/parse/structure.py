# -*- coding: utf-8 -*-
import struct


class StructureMeta(type):
    def __init__(self, clsname, bases, clsdict):
        fields = getattr(self, '_fields_', [])
        byte_order = ''
        offset = 0
        for fieldfmt, fieldname, *func in fields:
            if isinstance(fieldfmt, StructureMeta):
                field = NestedStruct(fieldname, fieldfmt, offset)
                size = fieldfmt.struct_size
            else:
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


class NestedStruct:
    def __init__(self, name, struct_type, offset):
        self.name = name
        self.struct_type = struct_type
        self.offset = offset

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            data = instance._buffer[self.offset:self.offset+self.struct_type.struct_size]
            result = self.struct_type(data)
            setattr(instance, self.name, result)
            return result


class SizedRecord:
    def __init__(self, bytedata):
        self._buffer = memoryview(bytedata)

    @classmethod
    def from_file(cls, fd, size_fmt, includes_size=True):
        sz_nbytes = struct.calcsize(size_fmt)
        sz_bytes = fd.read(sz_nbytes)
        sz, *_ = struct.unpack(size_fmt, sz_bytes)
        buf = fd.read(sz - includes_size * sz_nbytes)
        return cls(buf)

    def iter_as(self, code):
        if isinstance(code, str):
            s = struct.Struct(code)
            for off in range(0, len(self._buffer), s.size):
                yield s.unpack_from(self._buffer, off)
        elif isinstance(code, StructureMeta):
            size = code.struct_size
            for off in range(0, len(self._buffer), size):
                data = self._buffer[off:off+size]
                yield code(data)


class Structure(metaclass=StructureMeta):
    def __init__(self, bytedata):
        self._buffer = memoryview(bytedata)

    @classmethod
    def from_file(cls, fd):
        return cls(fd.read(cls.struct_size))
