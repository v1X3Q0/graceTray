
import argparse
import os
import time
import re
import gdb

from gdb_stools import clear_ws
from gdb_stools import populate_libs
from gdb_stools import parseArg
from gdb_stools import getlibranges_map

def invoke_find_all_sections(arg, from_tty):
    parser = argparse.ArgumentParser(description='trace some stuff.')
    parser.add_argument('search_string',
                        help='string to compare the argument of')

    parseArg(arg)
    args = parser.parse_args()
    libranges_map = populate_libs()
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
