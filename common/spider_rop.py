# ROP Gadgets
G = {
    'POP {R0-R4,PC}': lambda version:
        0x0010b5b4 if version >= (9, 0)
        else 0x0012A3D4 if version >= (5, 0)
        else 0x0029C170,
    'POP {R0,PC}': lambda version:
        0x0010c2fc if version >= (9, 0)
        else 0x0010C320 if version >= (5, 0)
        else 0x002AD574,
    'POP {R1,PC}': lambda version:
        0x00228af4 if version >= (9, 0)
        else 0x00228B10 if version >= (5, 0)
        else 0x00269758, # pop {r1, pc}
#    'POP {R3,PC}': lambda version:
#        0x00242d60 if version >= (9, 0)
#        else 'ERROR'
#    'POP {R4,PC}': lambda version:
#        0x00242d28 if version >= (9, 0)
#        else 'ERROR'
    'POP {LR,PC}': lambda version:
        0x0013035C if version >= (9, 0)
        else 0x001303A4 if version >= (5, 0)
        else 0x002D6A34,
    'POP {PC}': lambda version:
        0x001057c4 if version >= (9, 0)
        else 0x001057E0 if version >= (5, 0)
        else 0x0010DB6C,
}
