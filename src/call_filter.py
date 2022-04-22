
import argparse
import os
import time

# example usage
# cf recv "license" "$rsi" "rdi"

def hex_int(x):
    return int(x, 16)

parser = argparse.ArgumentParser(description='trace some stuff.')
parser.add_argument('sym_address',
                    help='symbol or address to break at')
parser.add_argument('search_string',
                    help='string to compare the argument of')
parser.add_argument('bytes_search',
                    help='bytes address to begin the search for')
parser.add_argument('bytes_length',
                    help='length to use for search of bytes')

ARCH=None
ARCH_SIZE=None
uint64_t = gdb.lookup_type('unsigned long long')
uint32_t = gdb.lookup_type('unsigned int')
uint16_t = gdb.lookup_type('unsigned short')
uint8_t = gdb.lookup_type('unsigned char')
size_t = None

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
        sys.argv.append("call_filter.py")
    # append the args that were parsed
    for i in args_each:
        sys.argv.append(i)
    return args_each


class call_filter (gdb.Breakpoint):
    def __init__(self, spec, search_string, bytes_search, bytes_length):
        self.search_string = search_string
        self.bytes_search = bytes_search
        self.bytes_length = bytes_length
        gdb.Breakpoint.__init__(self, spec)
    def stop (self):
        cur_bs = hex(int(gdb.parse_and_eval(self.bytes_search).cast(size_t)))
        cur_bl = hex(int(gdb.parse_and_eval(self.bytes_length).cast(size_t)))
        target_find_str = "find {}, +{}, {}".format(cur_bs, cur_bl, self.search_string)
        print(target_find_str)
        if int(cur_bl, 16) < len(self.search_string):
            # print("too small a size, continuing")
            return False
        find_output = gdb.execute(target_find_str, to_string=True)
        if "Pattern not found." in find_output:
            # print(find_output)
            return False
        return True
        
def invoke_call_filter(arg, from_tty):
    global ARCH
    global ARCH_SIZE
    global size_t
    global IS_TRACING
    f = None

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
    parseArg(arg)
    args = parser.parse_args()
    bytes_search = args.bytes_search.replace("\"", "")
    bytes_length = args.bytes_length.replace("\"", "")
    call_filter(args.sym_address, args.search_string, bytes_search, bytes_length)

class cfs (gdb.Command):
    """class filter search"""
    def __init__(self):
        super(cfs, self).__init__("cfs", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        invoke_call_filter(arg, from_tty)

cfs()