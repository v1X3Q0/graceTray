
import argparse
import os
import time
import gdb
import sys

dirname, filename = os.path.split(os.path.abspath(__file__))
if dirname not in sys.path:
    sys.path.append(dirname)

from gdb_stools import architecture_init
from gdb_stools import eval_branch_taken
from gdb_stools import getARCH
from gdb_stools import getARCH_SIZE
from gdb_stools import getsize_t
from gdb_stools import getsize_n
from gdb_stools import get_ret_address
from gdb_stools import software_finish

def invoke_software_finish(arg, from_tty):
    architecture_init()
    if eval_branch_taken() == True:
        software_finish()

class sso (gdb.Command):
    """software step over"""
    def __init__(self):
        super(sso, self).__init__("sso", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        invoke_software_finish(arg, from_tty)
