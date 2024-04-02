
import argparse
import os
import time
import re
import gdb

dirname, filename = os.path.split(os.path.abspath(__file__))
if dirname not in sys.path:
    sys.path.append(dirname)

from gdb_stools import populate_libs
from gdb_stools import clear_ws
from gdb_stools import architecture_init
from gdb_stools import get_lib_from_ranges
from gdb_stools import getlibranges_map
# example usage
# cf recv "license" "$rsi" "rdi"

def hex_int(x):
    return int(x, 16)

def invoke_smart_backtrace(arg, from_tty):
    architecture_init()
    bt_info = gdb.execute("bt", to_string=True)
    bt_info = bt_info.split("\n")
    bt_out = []

    populate_libs()
    libranges_map = getlibranges_map()
    
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
        libranges_map = getlibranges_map()
        targ_addr = int(arg, 0x10)
        pot_libname = get_lib_from_ranges(targ_addr)
        if pot_libname != None:
            print("from {} offset {}".format(pot_libname, hex(targ_addr - libranges_map[pot_libname][0]["start_addr"])))

sbt()
lta()
