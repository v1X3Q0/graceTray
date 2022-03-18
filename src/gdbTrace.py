from inspect import stack
import sys
import argparse

from numpy import size
# from software_finish import software_finish, software_finishpoint

def hex_int(x):
    return int(x, 16)

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

ARCH=None
ARCH_SIZE=None
uint64_t = gdb.lookup_type('unsigned long long')
uint32_t = gdb.lookup_type('unsigned int')
uint16_t = gdb.lookup_type('unsigned short')
uint8_t = gdb.lookup_type('unsigned char')
size_t = None
argfilename = "args.txt"
# winload
#   modBegin = 0x4057B000
#   modEnd = 0x4068C8C8

# convert args in args.txt to sys.argv, expect 1 line in
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
    args_each = args_line.split(' ')
    # clear the existing sys.argv
    while len(sys.argv) != 1:
        sys.argv.pop()
    # if the first argv is nothing, make it this script path
    if sys.argv[0] == '':
        sys.argv.pop()
        sys.argv.append(__file__)
    # append the args that were parsed
    for i in args_each:
        sys.argv.append(i)
    return args_each

class software_finishpoint (gdb.Breakpoint):
    def __init__(self, spec):
        # print("size_t software {}".format(size_t))
        self.stack_save = gdb.parse_and_eval("$sp").cast(size_t)
        if ARCH == "i386:x86-64":
            self.stack_save = self.stack_save + ARCH_SIZE
        gdb.Breakpoint.__init__(self, spec)
    def stop (self):
        inf_val = gdb.parse_and_eval("$sp").cast(size_t)
        # print("yahallo {} vs {}".format(hex(inf_val), hex(self.stack_save)))
        if inf_val == self.stack_save:
            return True
        return False

def software_finish():
    pc_save = None
    print("sf {}".format(size_t))
    if ARCH == "arm32":
        pc_save = int(gdb.parse_and_eval("$lr").cast(size_t))
    elif ARCH == "arm64":
        pc_save = int(gdb.parse_and_eval("$x30").cast(size_t))
    elif ARCH == "i386:x86-64":
        stack_temp = int(gdb.parse_and_eval("$sp").cast(size_t))
        pc_save = int(gdb.parse_and_eval(hex(stack_temp)))
    # print("pc_save {}".format(pc_save))
    software_finishpoint("*{}".format(hex(pc_save)))
    gdb.execute("c")

def main(args):
    global ARCH
    global ARCH_SIZE
    global size_t
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
    elif "armv5t" in arch_res:
        ARCH="arm32"
        ARCH_SIZE=4
        size_t = uint32_t
    else:
        print("unknown architecture res: {}".format(arch_res))
        return False
    if args.noTrace != True:
        f = open("gdbTrace.txt", "w")
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
    
if __name__ == "__main__":
# def sysmain():
    gdb.write("in sys")
    parseArgFile()
    # print(sys.argv)
    args = parser.parse_args()

    print("performing script")
    main(args)

# sysmain()