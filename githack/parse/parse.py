# -*- coding: utf-8 -*-
from operator import methodcaller
import re
import sys
import zlib

from .structure import Structure

SIGNATURE = b'DIRC'
SUPPORTED_VERSION = (2, 3)
RE_OBJECTS_TREE = re.compile(rb'(\d+) ([^\x00]+)\x00(.{20})', re.DOTALL)


class Header(Structure):
    _fields_ = [
        ('!4s', 'signature'),
        ('I', 'version'),
        ('I', 'entries'),
    ]


class Entries(Structure):
    _fields_ = [
        ('!I', 'ctime_seconds'),
        ('I', 'ctime_nanoseconds'),
        ('I', 'mtime_seconds'),
        ('I', 'mtime_nanoseconds'),
        ('I', 'dev'),
        ('I', 'ino'),
        ('I', 'mode'),
        ('I', 'uid'),
        ('I', 'gid'),
        ('I', 'size'),
        ('20s', 'sha1', methodcaller('hex')),
        ('H', 'flags'),
    ]


class ExtenedEntries(Structure):
    _fields_ = [
        ('!H', 'extra_flags'),
    ]


def parse_index(fd):
    ''' https://git-scm.com/docs/index-format '''
    header = Header.from_file(fd)
    if header.signature != SIGNATURE:
        raise TypeError("Not a Git index file")

    if header.version not in SUPPORTED_VERSION:
        raise NotImplementedError("Unsupported version")
    yield header.entries

    for idx in range(header.entries):
        entries = Entries.from_file(fd)

        setattr(entries, 'entry', idx + 1)
        setattr(entries, 'assume_valid', bool(entries.flags & (0b10000000 << 8)))
        setattr(entries, 'extended', bool(entries.flags & (0b01000000 << 8)))
        _stage1 = bool(entries.flags & (0b00100000 << 8))
        _stage2 = bool(entries.flags & (0b00010000 << 8))
        setattr(entries, 'stage', (_stage1, _stage2))
        setattr(entries, 'namelen', entries.flags & 0xFFF)

        if header.version == 3 and entries.extended:
            extended = ExtenedEntries.from_file(fd)
            _extra_flags = extended.extra_flags
            setattr(entries, 'reserved', _extra_flags & (0b10000000 << 8))
            setattr(entries, 'skip-worktree', _extra_flags & (0b01000000 << 8))
            setattr(entries, 'intent-to-add', _extra_flags & (0b00100000 << 8))
            entries.struct_size += 2

        if entries.namelen < 0xFFF:
            _name = fd.read(entries.namelen).decode()
            setattr(entries, 'name', _name)
            entries.struct_size += entries.namelen
        else:
            # TODO: read name when namelen >= 0xfff
            raise NotImplementedError("not support when name length >= 4095 (0xFFF)")

        _padlength = 8 - (entries.struct_size % 8)
        nuls = fd.read(_padlength)
        if set(nuls) == set('\x00'):
            raise Exception('padding contained non-NUL')

        yield entries


def parse_object(bytedata, *, strict_mode=False):
    ''' https://git-scm.com/book/en/v2/Git-Internals-Git-Objects'''
    try:
        bytedata = zlib.decompress(bytedata)
    except Exception as ex:
        print(repr(ex), file=sys.stderr)
        sys.exit(1)

    bytedata = bytedata.replace(b' ', b'\x00', 1)
    filetype, length, content = bytedata.split(b'\x00', 2)

    '''
    if filetype == b'tree':
        seen = []
        for mode, filename, hashvalue in RE_OBJECTS_TREE.finditer(content):
            seen.append((mode, filename, hashvalue.hex()))
        content = seen
    '''

    if strict_mode and str(len(content)) != length.decode():
        raise Exception('Parse Error: content length not fit')

    return filetype, content
