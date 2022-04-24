from inspect import stack, trace
import sys
import argparse
from datetime import datetime
import os

from numpy import size
# from software_finish import software_finish, software_finishpoint

def hex_int(x):
    return int(x, 16)

ARCH=None
ARCH_SIZE=None
uint64_t = gdb.lookup_type('unsigned long long')
uint32_t = gdb.lookup_type('unsigned int')
uint16_t = gdb.lookup_type('unsigned short')
uint8_t = gdb.lookup_type('unsigned char')
size_t = None
argfilename = "args.txt"
IS_TRACING=False
# winload
#   modBegin = 0x4057B000
#   modEnd = 0x4068C8C8

# convert args in args.txt to sys.argv, expect 1 line in
def parseArg(args_line):
    args_each = args_line.split(' ')
    # clear the existing sys.argv
    while len(sys.argv) != 1:
        sys.argv.pop()
    # if the first argv is nothing, make it this script path
    if sys.argv[0] == '':
        sys.argv.pop()
        # when main, can do __file__, if command have to insert thing
        # sys.argv.append(__file__)
        sys.argv.append("gdbTrace.py")
    # append the args that were parsed
    for i in args_each:
        sys.argv.append(i)
    return args_each

def parseArgFile():
    f = None
    try:
        f = open(argfilename, "r")
    except:
        print("no file {}".format(argfilename))
        return False
    args_line = f.readlines()
    f.close()
    args_line = args_line[0].replace('\n', '')
    return parseArg(args_line)


class software_finishpoint (gdb.Breakpoint):
    def __init__(self, spec):
        self.stack_save = gdb.parse_and_eval("$sp").cast(size_t)
        if ARCH == "i386:x86-64":
            self.stack_save = self.stack_save + ARCH_SIZE
        gdb.Breakpoint.__init__(self, spec)
    def stop (self):
        inf_val = gdb.parse_and_eval("$sp").cast(size_t)
        if inf_val == self.stack_save:
            return True
        return False

def software_finish():
    pc_save = None
    if ARCH == "arm32":
        pc_save = int(gdb.parse_and_eval("$lr").cast(size_t))
    elif ARCH == "arm64":
        pc_save = int(gdb.parse_and_eval("$x30").cast(size_t))
    elif ARCH == "i386:x86-64":
        stack_temp = int(gdb.parse_and_eval("$sp").cast(size_t))
        pc_save = int(gdb.parse_and_eval(hex(stack_temp)))
    temp_finish = software_finishpoint("*{}".format(hex(pc_save)))
    temp_finish.silent = True
    gdb.execute("c")
    temp_finish.delete()

def init_trace_filename():
    fname = ""
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

class software_tracepoint (gdb.Breakpoint):
    def __init__(self, spec, args):
        self.args = args
        gdb.Breakpoint.__init__(self, spec)

    def stop (self):
        global IS_TRACING
        # evaluate if i'm the correct tracepoint?
        # which would mean verify that I have the correct stack frame
        # or thread id
        if IS_TRACING == False:
            IS_TRACING = True
            print("tracepoint encountered {}, beginning trace".format(hex(gdb.parse_and_eval("$pc").cast(size_t))))
            return True
        else:
            print("WARNING: encountered tracepoint mid trace")
            return False

def main(args):
    global ARCH
    global ARCH_SIZE
    global size_t
    global IS_TRACING
    f = None
    # i386:x86-64
    # The target architecture is set automatically (currently i386:x86-64)
    # armv5t
    # The target architecture is set automatically (currently armv5t)

    arch_res = gdb.execute("show architecture", to_string=True)
    # print("arch_res {}".format(arch_res))
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
    if args.noTrace != True:
        f = open(init_trace_filename(), "w")
    while True:
        currentInst = gdb.parse_and_eval("$pc")
        if (currentInst < args.funcBegin) or (currentInst > args.funcEnd):
            # gdb.execute("finish")
            software_finish()
            continue
        if args.noTrace != True:
            f.write(hex(currentInst) + '\n')
        if currentInst == args.destination:
            break
        gdb.execute("si")
    if args.noTrace != True:
        f.close()
    IS_TRACING = False

def invoke_software_tracepoint(arg, from_tty):
    global ARCH
    global ARCH_SIZE
    global size_t
    global IS_TRACING
    f = None
    parser = argparse.ArgumentParser(description='trace some stuff.')
    parser.add_argument('-mb', '--modBegin', type=hex_int,
                        help='module beginning')
    parser.add_argument('-me', '--modEnd', type=hex_int,
                        help='module ending')
    parser.add_argument('-fb', '--funcBegin', type=hex_int,
                        help='function beginning')
    parser.add_argument('-fe', '--funcEnd', type=hex_int,
                        help='function ending')
    parser.add_argument('destination', type=hex_int,
                        help='destination instruction')
    parser.add_argument('-nt', '--noTrace', action='store_true',
                        help='whether or not to record instructions')
    parser.add_argument('-mt', '--multTrace', action='store_true',
                        help='trace point infinite times, or auto cleanup')

    # i386:x86-64
    # The target architecture is set automatically (currently i386:x86-64)
    # armv5t
    # The target architecture is set automatically (currently armv5t)

    arch_res = gdb.execute("show architecture", to_string=True)
    # print("arch_res {}".format(arch_res))
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
    parseArg(arg)
    args = parser.parse_args()

    while True:
        if args.funcBegin != gdb.parse_and_eval("$pc").cast(size_t):
            temp_stp = software_tracepoint("*{}".format(hex(args.funcBegin)), args)
            temp_stp.silent = True
            print("tracepoint set at {}".format(hex(args.funcBegin)))
            gdb.execute("c")
            temp_stp.delete()
            if args.funcBegin != gdb.parse_and_eval("$pc").cast(size_t):
                return False
        if args.noTrace != True:
            f = open(init_trace_filename(), "w")
        while True:
            currentInst = gdb.parse_and_eval("$pc")
            if (currentInst < args.funcBegin) or (currentInst > args.funcEnd):
                # gdb.execute("finish")
                software_finish()
                continue
            if args.noTrace != True:
                f.write(hex(currentInst) + '\n')
            if currentInst == args.destination:
                break
            gdb.execute("si")
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