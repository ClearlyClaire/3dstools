#!/usr/bin/env python2

from common.constants import *

import sys
import struct

def findjumps(file, count):
    pos = file.tell()
    for i in range(count):
        word = file.read(4)
        if len(word) != 4 or word[3] != '\xeb':
            file.seek(pos)
            return False
    file.seek(pos)
    return True

def is_valid_va(address):
    return 0 <= (address - 0x00100000) < APPMEMALLOC

def is_xref(cmd, pc, target):
    offset = target - (pc + 8)
    txt = struct.pack('<i', offset // 4)[:3]
    x = ord(cmd[3])
    return txt == cmd[:3] and (x & 14 == 10)

def find_getservicehandle(file):
    pos = file.tell()

    # push {r4, r5, r6, r7, r8, lr}
    if file.read(4) != b'\xf0\x41\x2d\xe9':
        file.seek(pos)
        return False

    ok = False
    for i in range(15):
        if file.read(4) == b'\x32\x00\x00\xef':
            ok = True
            break
    if not ok:
        file.seek(pos)
        return False

    for i in range(10):
        if file.read(4) == b'\x00\x01\x05\x00':
            file.seek(pos)
            return True
    file.seek(pos)
    return False


def find_wrapper(file, target):
    pos = file.tell()
    if file.read(4)[1:] != b'\x20\xc0\x9f\xe5'[1:]: # ldr ip, [pc, 32]
        file.seek(pos)
        return False

    ok = False
    for i in range(30):
        data = file.read(4)
        if data == b'\x1e\xff\x2f\xe1':
            file.seek(pos)
            return False
        if is_xref(data, pos + 4 * (i + 1), target):
            ok = True
            break

    if ok:
        file.seek(pos)
        return True
    else:
        file.seek(pos)
        return False


def decode_move(data):
    cmd, = struct.unpack('<I', data)
    op = cmd & 4095
    cmd >>= 12
    dest = cmd & 15
    cmd >>= 4
    if cmd & 15 != 0:
        return None
    cmd >>= 4
    S = cmd & 1
    cmd >>= 1
    if cmd & 15 != 13:
        return None
    cmd >>= 4
    immediate = cmd & 1
    cmd >>= 1
    if cmd & 3 != 0:
        return None
    cmd >>= 2
    if S or (op > 10 and not immediate):
        return None
    return (op, dest, immediate)


def decode_ldr(data):
    cmd, = struct.unpack('<I', data)
    offset = cmd & 4095
    cmd >>= 12
    reg = cmd & 15
    cmd >>= 4
    if cmd == 0xe59f:
        return (reg, offset)
    else:
        return None


def decode_service_init(file, target):
    pos = file.tell()
    values = {}

    for i in range(10):
        pc = file.tell()
        data = file.read(4)

        if len(data) < 4:
            file.seek(pos)
            return None

        if is_xref(data, pc, target):
            values['address'] = pc
            return values

        if ord(data[3]) & 10 == 10:
            file.seek(pos)
            return None

        decoded_data = decode_ldr(data)
        if decoded_data:
            reg, offset = decoded_data
            file.seek(pc + offset + 8)
            v, = struct.unpack('<I', file.read(4))
            values[reg] = v
            file.seek(pc + 4)
            continue
        decoded_data = decode_move(data)
        if decoded_data:
            op, reg, immediate = decoded_data
            if immediate:
                values[reg] = op
            elif op in values:
                values[reg] = values[op]
            continue

#        file.seek(pos)
#        return None

    return None


def main(path):
    with open(path, 'rb') as file:
        file.seek(0, 2)
        file_size = file.tell()

        file.seek(0)
        while True:
            if findjumps(file, 4):
                candidate = file.tell()
                print('Offset of .text in file: %#08x' % candidate)
                print('Address of .text in RAM: %#08x' % (DUMPEND - file_size + candidate))
            if len(file.read(4096)) < 4096:
                break
        text_offset = candidate
        bss_offset = file_size - text_offset

        bss_candidates = []
        file.seek(0)
        ok = True
        while file.tell() < text_offset:
            ptr = file.tell()
            data = file.read(4096)
            if len(data) < 4096:
                break
            if data[:32] != (b'\x00' * 32) and ok:
                bss_candidates.append(ptr)
            ok = (data[-256:] == (b'\x00' * 256))
        print(bss_candidates)

        file.seek(0)
        while True:
            if find_getservicehandle(file):
                candidate = file.tell()
                print('getservicehandle offset in file: %#08x' % candidate)
            if len(file.read(4)) < 4:
                break
        getservicehandle_address = candidate

        file.seek(0)
        while True:
            pc = file.tell()
            data = file.read(4)
            if len(data) < 4:
                break
            if is_xref(data, pc, getservicehandle_address):
                print('XREF to getservicehandle: %#08x' % pc)

        file.seek(0)
        while True:
            if find_wrapper(file, getservicehandle_address):
                wrapper_address = file.tell()
                print('Wrapper offset in file: %#08x' % wrapper_address)
            if len(file.read(4)) < 4:
                break

        file.seek(0)
        while True:
            values = decode_service_init(file, wrapper_address)
            if values:
                pos = file.tell()
                if 1 in values:
                    if values[1] - 0x00100000 < bss_offset:
                        service_name_pos = values[1] - 0x00100000 + text_offset
                        file.seek(service_name_pos)
                        name = file.read(20)
                        if not name:
                            name = '(VA: %#08x)' % values[1]
                        else:
                            name = name[:name.find('\x00')]
                    else:
                        #service_name_pos = values[1] - 0x00100000 - bss_offset + 0x3a0000
                        #file.seek(service_name_pos)
                        #name = file.read(20)
                        #if not name:
                        name = '(in BSS/VA: %#08x)' % values[1]
                        #else:
                        #    name = name[:name.find('\x00')]
                else:
                    name = '(unknown)'

                print('Handle %s: %#08x [xref: %#08x]' % (name, values.get(0, 0), values['address']))
                file.seek(pos)
            if len(file.read(4)) < 4:
                break

main(*sys.argv[1:])
