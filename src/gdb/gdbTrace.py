from inspect import stack, trace
import sys
import argparse
from datetime import datetime
import os
import gdb

dirname, filename = os.path.split(os.path.abspath(__file__))
if dirname not in sys.path:
    sys.path.append(dirname)

from gdb_stools import parseArg
from gdb_stools import architecture_init
from gdb_stools import get_ret_address
from gdb_stools import software_finish
from gdb_stools import getsize_t
from gdb_stools import software_tracepoint
from gdb_stools import eval_branch_taken

# from numpy import size
# from software_finish import software_finish, software_finishpoint

def hex_int(x):
    return int(x, 16)

def init_trace_filename():
    size_t = getsize_t()
    fname = ""
    # detect if you have a symbol file, if so name will use its name
    fileres = gdb.execute("info files", to_string=True)
    symbolline = fileres.split('\n')[0]
    if symbolline.split(' ')[0] == "Symbols":
        fileabs_beg = symbolline.find("\"")
        fileabs_end = symbolline.find("\"", fileabs_beg + 1)
        fileabs = symbolline[fileabs_beg + 1:fileabs_end]
        fname = "{}_".format(os.path.basename(fileabs))

    tracename = "{}{}_{}.trace.txt".format(fname,
        hex(int(gdb.parse_and_eval("$pc").cast(size_t))),
        datetime.utcnow().strftime('%Y%m%d_%H%M%S%f')[:-3])

    return tracename
    # return "gdbTrace.txt"

def software_tracepoint_init(arg, from_tty):
    parser = argparse.ArgumentParser(description='trace some stuff.')
    parser.add_argument('-mb', '--modBegin', type=hex_int,
                        help='module beginning')
    parser.add_argument('-me', '--modEnd', type=hex_int,
                        help='module ending')
    parser.add_argument('-fb', '--funcBegin', type=hex_int,
                        help='function beginning')
    parser.add_argument('-dst', '--destination', type=hex_int,
                        help='destination instruction')
    parser.add_argument('-nt', '--noTrace', action='store_true',
                        help='whether or not to record instructions')
    parser.add_argument('-mt', '--multTrace', action='store_true',
                        help='trace point infinite times, or auto cleanup')

    architecture_init()
    parseArg(arg)
    args = parser.parse_args()
    return args

def invoke_software_tracepoint(arg, from_tty):
    f = None
    filename = ""
    args = software_tracepoint_init(arg, from_tty)
    size_t = getsize_t()

    while True:
        if args.funcBegin != None:
            if args.funcBegin != gdb.parse_and_eval("$pc").cast(size_t):
                temp_stp = software_tracepoint("*{}".format(hex(args.funcBegin)), args)
                temp_stp.silent = True
                print("tracepoint set at {}".format(hex(args.funcBegin)))
                gdb.execute("c")
                temp_stp.delete()
                if args.funcBegin != gdb.parse_and_eval("$pc").cast(size_t):
                    return False
        if args.noTrace != True:
            try:
                filename = init_trace_filename()
                f = open(filename, "w")
            except:
                print("couldn't open {}".format(filename))
                return -1
        retAddr = get_ret_address()
        if args.destination == None:
            args.destination == retAddr
        print("expect to stop at {}".format(hex(retAddr)))
        while True:
            currentInst = int(gdb.parse_and_eval("$pc").cast(size_t))
            if (currentInst == args.destination) or (currentInst == retAddr):
                break
            # if (currentInst < args.funcBegin) or (currentInst > args.funcEnd):
                # gdb.execute("finish")
            if args.noTrace != True:
                f.write(hex(currentInst) + '\n')
            # perform step after everything
            if eval_branch_taken() == True:
                software_finish()
        if args.noTrace != True:
            f.close()
        # if nostop, then keep looping, another tracepoint continue and so on.
        # else, break
        IS_TRACING = False
        if args.multTrace != True:
            break

class stp (gdb.Command):
    """software tracepoint command"""
    def __init__(self):
        super(stp, self).__init__("stp", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        invoke_software_tracepoint(arg, from_tty)

# if __name__ == "__main__":
# # def sysmain():
#     parseArgFile()
#     # print(sys.argv)
#     args = parser.parse_args()

#     main(args)
stp()
# sysmain()