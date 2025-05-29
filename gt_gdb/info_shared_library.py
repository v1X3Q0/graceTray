
import argparse
import os
import time
import re
import gdb
import sys

dirname, filename = os.path.split(os.path.abspath(__file__))
if dirname not in sys.path:
    sys.path.append(dirname)

from gdb_stools import parseArg
from gdb_stools import populate_libs
from gdb_stools import getlibranges_map

def hex_int(x):
    return int(x, 16)

def invoke_info_shared_library(arg, from_tty):

    parser = argparse.ArgumentParser(description='trace some stuff.')
    parser.add_argument('so_name',
                        help='shared library to find')
    parser.add_argument('-ol', '--offset_lib', type=hex_int, required=False,
                        help='slide off and print')
    parseArg(arg)
    args = parser.parse_args()
    populate_libs()
    libranges_map = getlibranges_map()
    for i in libranges_map.keys():
        if os.path.isfile(i) == False:
            continue
        so_lib_cur = os.path.basename(i)
        so_lib_cur = so_lib_cur.split('.')[0]
        if so_lib_cur != args.so_name:
            continue
        so_beg = libranges_map[i][0]["start_addr"]
        so_end = libranges_map[i][len(libranges_map[i]) - 1]["end_addr"]
        line_out = "{} {} {}".format(hex(so_beg), hex(so_end), so_lib_cur)
        if args.offset_lib != None:
            line_out = "{} {}".format(line_out, hex(so_beg + args.offset_lib))
        print(line_out)

class isl (gdb.Command):
    """info shared library"""
    def __init__(self):
        super(isl, self).__init__("isl", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        invoke_info_shared_library(arg, from_tty)
