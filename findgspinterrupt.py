#!/usr/bin/env python2

from common.constants import *

import sys
import struct

def is_valid_va(address):
    return 0 <= (address - 0x00100000) < APPMEMALLOC

def findinterrupttable(file):
    pos = file.tell()
    data = file.read(0x90)
    if data[-16:] != b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
        file.seek(pos)
        return False

    # Now, that should be a table
    data = file.read(4 * 6)
    if len(data) != 4 * 6:
        file.seek(pos)
        return False

    addresses = struct.unpack('<6I', data)
    for address in addresses:
        if not is_valid_va(address):
            file.seek(pos)
            return False

    file.seek(pos)

    return True

def main(path):
    with open(path, 'rb') as file:
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        while True:
            if findinterrupttable(file):
                candidate = file.tell()
                print('Offset in file: %#08x' % candidate)
                print('Address in RAM: %#08x' % (DUMPEND - file_size + candidate))
            if len(file.read(4)) < 4:
                break

main(*sys.argv[1:])
