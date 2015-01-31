#!/usr/bin/env python2

from common.constants import *

import sys

def findjumps(file, count):
    pos = file.tell()
    for i in range(count):
        word = file.read(4)
        if len(word) != 4 or word[3] != '\xeb':
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
            if findjumps(file, 4):
                candidate = file.tell()
                print('Offset of .text in file: %#08x' % candidate)
                print('Address of .text in RAM: %#08x' % (DUMPEND - file_size + candidate))
            if len(file.read(4096)) < 4096:
                break

main(*sys.argv[1:])
