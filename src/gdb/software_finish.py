
import argparse
import os
import time
import gdb

dirname, filename = os.path.split(os.path.abspath(__file__))
if dirname not in sys.path:
    sys.path.append(dirname)

from gdb_stools import architecture_init
from gdb_stools import get_ret_address
from gdb_stools import getARCH
from gdb_stools import getARCH_SIZE
from gdb_stools import getsize_t
from gdb_stools import getsize_n
from gdb_stools import software_finish

def invoke_software_finish(arg, from_tty):
    architecture_init()
    software_finish()

class sfc (gdb.Command):
    """software finish command"""
    def __init__(self):
        super(sfc, self).__init__("sfc", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        invoke_software_finish(arg, from_tty)

sfc()