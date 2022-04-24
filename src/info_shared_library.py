
import argparse
import os
import time
import re

def hex_int(x):
    return int(x, 16)

libranges_map = {}

# convert args in args.txt to sys.argv, expect 1 line in
def parseArg(args_line):
    args_each = []
    if args_line != '':
        args_each = args_line.split(' ')
    # clear the existing sys.argv
    while len(sys.argv) != 0:
        sys.argv.pop()
    sys.argv.append("info_shared_library.py")
    # append the args that were parsed
    for i in args_each:
        sys.argv.append(i)
    return args_each

def clear_ws(line):
    ws_rem = re.sub(' +', ' ', line)
    if ws_rem[0] == ' ':
        ws_rem = ws_rem[1:]
    ret_bar = ws_rem.split(' ')
    return ret_bar

def populate_libs():
    global libranges_map

    ipm_info = gdb.execute("i proc mappings", to_string=True)
    ipm_info = ipm_info.split('\n')[4:]
    for i in ipm_info:
        if len(i) == 0:
            continue
        keys_ipm = clear_ws(i)
        if len(keys_ipm) == 4:
            continue
        libname = keys_ipm[len(keys_ipm) - 1]
        start_addr = int(keys_ipm[0], 0x10)
        end_addr = int(keys_ipm[1], 0x10)
        if libname in libranges_map.keys():
            libranges_map[libname].append({"start_addr": start_addr, "end_addr": end_addr})
        else:
            libranges_map[libname] = [{"start_addr": start_addr, "end_addr": end_addr}]

def invoke_info_shared_library(arg, from_tty):

    parser = argparse.ArgumentParser(description='trace some stuff.')
    parser.add_argument('so_name',
                        help='shared library to find')
    parser.add_argument('-ol', '--offset_lib', type=hex_int, required=False,
                        help='slide off and print')
    parseArg(arg)
    args = parser.parse_args()
    populate_libs()
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

isl()
