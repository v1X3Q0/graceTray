
import argparse
import os
import time
import re

# example usage
# cf recv "license" "$rsi" "rdi"

def hex_int(x):
    return int(x, 16)

ARCH=None
ARCH_SIZE=None
uint64_t = gdb.lookup_type('unsigned long long')
uint32_t = gdb.lookup_type('unsigned int')
uint16_t = gdb.lookup_type('unsigned short')
uint8_t = gdb.lookup_type('unsigned char')
size_t = None
libranges_map = {}

def get_lib_from_ranges(targ_addr):
    global libranges_map

    # dictionary of lists, get the keys
    for i in libranges_map.keys():
        # the get the lists
        for j in libranges_map[i]:
            # then get the sub dicts
            if (targ_addr >= j["start_addr"]) and (targ_addr < j["end_addr"]):
                return i
    return None

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

def invoke_smart_backtrace(arg, from_tty):
    global ARCH
    global ARCH_SIZE
    global size_t
    global libranges_map

    arch_res = gdb.execute("show architecture", to_string=True)
    if "i386:x86-64" in arch_res:
        ARCH="i386:x86-64"
        ARCH_SIZE=8
        size_t = uint64_t
    elif ("armv5t" in arch_res) or ("arm)" in arch_res):
        ARCH="arm32"
        ARCH_SIZE=4
        size_t = uint32_t
    else:
        print("unknown architecture res: {}".format(arch_res))
        return False
    bt_info = gdb.execute("bt", to_string=True)
    bt_info = bt_info.split("\n")
    bt_out = []

    populate_libs()
    
    ljustprologue = len(str(len(bt_info) - 2)) + 2
    if ljustprologue < 4:
        ljustprologue = 4
    for i in bt_info:
        if len(i) == 0:
            continue
        if "from" in i:
            new_bt_line = i
        else:
            keys_bt = clear_ws(i)
            targ_addr = int(keys_bt[1], 0x10)
            pot_libname = get_lib_from_ranges(targ_addr)
            if pot_libname != None:
                new_bt_line = "{}{} from {} offset {}".format(keys_bt[0].ljust(ljustprologue), keys_bt[1], pot_libname, hex(targ_addr - libranges_map[pot_libname][0]["start_addr"]))
            else:
                new_bt_line = i
        bt_out.append(new_bt_line)

    for i in bt_out:
        print(i)

class sbt (gdb.Command):
    """smart backtrace"""
    def __init__(self):
        super(sbt, self).__init__("sbt", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        invoke_smart_backtrace(arg, from_tty)

class lta (gdb.Command):
    """locate target address"""
    def __init__(self):
        super(lta, self).__init__("lta", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        populate_libs()
        targ_addr = int(arg, 0x10)
        pot_libname = get_lib_from_ranges(targ_addr)
        if pot_libname != None:
            print("from {} offset {}".format(pot_libname, hex(targ_addr - libranges_map[pot_libname][0]["start_addr"])))

sbt()
lta()
