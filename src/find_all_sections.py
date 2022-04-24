
import argparse
import os
import time
import re

libranges_map = {}

# convert args in args.txt to sys.argv, expect 1 line in
def parseArg(args_line):
    args_each = []
    if args_line != '':
        args_each = args_line.split(' ')
    # clear the existing sys.argv
    while len(sys.argv) != 0:
        sys.argv.pop()
    sys.argv.append("find_all_sections.py")
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

def invoke_find_all_sections(arg, from_tty):
    parser = argparse.ArgumentParser(description='trace some stuff.')
    parser.add_argument('search_string',
                        help='string to compare the argument of')

    parseArg(arg)
    args = parser.parse_args()
    populate_libs()
    for i in libranges_map.keys():
        for j in libranges_map[i]:
            target_find_str = "find {}, {}, {}".format(hex(j["start_addr"]), hex(j["end_addr"]), args.search_string)
            findres = gdb.execute(target_find_str, to_string=True)
            if ("Pattern not found." in findres) == False:
                print(i)
                print(target_find_str)
                print(findres)

class fas (gdb.Command):
    """find all sections"""
    def __init__(self):
        super(fas, self).__init__("fas", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        invoke_find_all_sections(arg, from_tty)

fas()
