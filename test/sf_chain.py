
import argparse
import os
import time
from datetime import datetime
import os

ARCH=None
ARCH_SIZE=None
# print(hex(int(gdb.parse_and_eval("*(unsigned long long*)" + sp_temp).cast(gdb.lookup_type('unsigned long long')))))
uint64_n = "unsigned long long"
uint32_n = "unsigned int"
uint16_n = "unsigned short"
uint8_n = "unsigned char"
uint64_t = gdb.lookup_type(uint64_n)
uint32_t = gdb.lookup_type(uint32_n)
uint16_t = gdb.lookup_type(uint16_n)
uint8_t = gdb.lookup_type(uint8_n)
size_n = None
size_t = None
haltex = False
nodump = False
rsi_chain = None
rdx_chain = None
optionstring = None
IS_TRACING=False
b_list = []

# convert args in args.txt to sys.argv, expect 1 line in
def parseArg(args_line):
    args_each = []
    if args_line != '':
        args_each = args_line.split(' ')
    # clear the existing sys.argv
    while len(sys.argv) != 0:
        sys.argv.pop()
    sys.argv.append("info_shared_library.py")
    # append the args that were parsed
    for i in args_each:
        sys.argv.append(i)
    return args_each

def get_next_instruction():
    if ARCH == "i386:x86-64":
        pc_output = gdb.execute("x/2i $pc", to_string=True)
        next_inst = pc_output.split('\n')[1]
        next_inst = next_inst.replace("\t", " ")
        next_inst = next_inst.replace(":", "")
        next_inst = next_inst[3:]
        next_inst = next_inst.split(" ")[0]
        next_inst_addr = int(next_inst, 16)
    elif ARCH == "arm32":
        cur_inst = int(gdb.parse_and_eval("$pc").cast(size_t))
        next_inst_addr = cur_inst + 4
    return next_inst_addr

def get_ret_address():
    if ARCH == "i386:x86-64":
        # print(hex(int(gdb.parse_and_eval("*(unsigned long long*)" + sp_temp).cast(gdb.lookup_type('unsigned long long')))))
        sp_temp = int(gdb.parse_and_eval("$sp").cast(size_t))
        ret_addr = int(gdb.parse_and_eval("*({}*){}".format(size_n, hex(sp_temp))).cast(size_t))
    elif ARCH == "arm32":
        ret_addr = int(gdb.parse_and_eval("$lr").cast(size_t))
    return ret_addr

def init_dump_filename():
    fname = ""
    fileres = gdb.execute("info files", to_string=True)
    symbolline = fileres.split('\n')[0]
    if symbolline.split(' ')[0] == "Symbols":
        fileabs_beg = symbolline.find("\"")
        fileabs_end = symbolline.find("\"", fileabs_beg + 1)
        fileabs = symbolline[fileabs_beg + 1:fileabs_end]
        fname = "{}_".format(os.path.basename(fileabs))

    tracename = "{}{}_{}.dump.txt".format(fname,
        hex(int(gdb.parse_and_eval("$pc").cast(size_t))),
        datetime.utcnow().strftime('%Y%m%d_%H%M%S%f')[:-3])
        
    return tracename
    # return "gdbTrace.txt"

class software_finishpoint_control (gdb.Breakpoint):
    def __init__(self, spec):
        self.stack_save = gdb.parse_and_eval("$sp").cast(size_t)
        if ARCH == "i386:x86-64":
            self.stack_save = self.stack_save + ARCH_SIZE
        gdb.Breakpoint.__init__(self, spec)
    def stop (self):
        inf_val = gdb.parse_and_eval("$sp").cast(size_t)
        if inf_val == self.stack_save:
            # throw commands here to be executed after sfc occurs
            tmp_fname = init_dump_filename()
            rax_chain = int(gdb.parse_and_eval("$rax").cast(size_t))
            if rax_chain != rdx_chain:
                print("MISMATCH: rax: {} rdx: {} to dump: {}".format(hex(rax_chain), hex(rdx_chain), tmp_fname))
            else:
                print("MATCH   : rax: {} rdx: {} to dump: {}".format(hex(rax_chain), hex(rdx_chain), tmp_fname))
            # this is technically incorrect, we should be reading rax bytes
            # since rax was what was sent back. however, the buffer should be
            # of size rdx anyways, so whatever, we'll take it all.
            if nodump == False:
                gdb.execute("dump binary memory {} {} {}".format(tmp_fname, hex(rsi_chain), hex(rsi_chain + rdx_chain)))
            target_find_str = "find {}, +{}, {{char[{}]}}\"{}\"".format(hex(rsi_chain), hex(rdx_chain), len(optionstring), optionstring)
            if len(optionstring) > rdx_chain:
                return False
            find_output = gdb.execute(target_find_str, to_string=True)
            if "Pattern not found." in find_output:
                # print(find_output)
                return False
            # no stop == true means no stop
            print(target_find_str)
            if haltex == True:
                return True
        return False

class software_bp_control (gdb.Breakpoint):
    def __init__(self, spec):
        gdb.Breakpoint.__init__(self, spec)
    def stop (self):
        # throw commands here to be executed after sfcc occurs
        tmp_fname = init_dump_filename()
        loc_rsi = int(gdb.parse_and_eval("$rsi").cast(size_t))
        loc_rdx = int(gdb.parse_and_eval("$rdx").cast(size_t))
        print("NOT CHECKING RET: rdx: {} to dump: {}".format(hex(loc_rdx), tmp_fname))
        gdb.execute("dump binary memory {} {} {}".format(tmp_fname, hex(loc_rsi), hex(loc_rsi + loc_rdx)))
        if haltex == True:
            return True
        return False

def software_finish_control():
    global b_list
    pc_save = get_ret_address()
    if pc_save not in b_list:
        b_list.append(pc_save)
        temp_finish = software_finishpoint_control("*{}".format(hex(pc_save)))
        temp_finish.silent = True

class delim_entrypoint (gdb.Breakpoint):
    def __init__(self, spec):
        gdb.Breakpoint.__init__(self, spec)
    def stop (self):
        # throw commands here to be executed before sfc occurs
        global rsi_chain
        global rdx_chain
        rsi_chain = int(gdb.parse_and_eval("$rsi").cast(size_t))
        rdx_chain = int(gdb.parse_and_eval("$rdx").cast(size_t))
        # set successor
        software_finish_control()
        # return false to allow execution to reach the sfc
        return False

def invoke_software_finish_control(arg, from_tty):
    global ARCH
    global ARCH_SIZE
    global size_n
    global size_t
    global haltex
    global nodump
    global optionstring
    global IS_TRACING

    parser = argparse.ArgumentParser(description='create set color script for ida')
    parser.add_argument("ENTRY",
        help="where chain should start")
    parser.add_argument('-ee', '--execEntry', required=False,
        help='execute this gdb stuff on entry')
    parser.add_argument('-ef', '--execFinish', required=False,
        help='execute this gdb stuff on exit')
    parser.add_argument('-je', '--justexec', required=False, action='store_true',
        help='not a finishpoint, just a standard pybreak')    
    parser.add_argument('-nd', '--nodump', required=False, action='store_true',
        help="don't dump")
    parser.add_argument('-he', '--haltex', required=False, action='store_true',
        help="halt execution")
    parser.add_argument('-os', '--optionstring', required=False,
        help="string to search for")

    parseArg(arg)
    args = parser.parse_args()
    if args.haltex == True:
        print("WARNING: args.nostop set to {}, will be halting".format(args.haltex))
    haltex = args.haltex
    nodump = args.nodump
    if args.justexec == True:
        print("WARNING: standard breakpoint executing, not fancy finish")
    optionstring = args.optionstring[1:len(args.optionstring) - 1]

    arch_res = gdb.execute("show architecture", to_string=True)
    if "i386:x86-64" in arch_res:
        ARCH="i386:x86-64"
        ARCH_SIZE=8
        size_n = uint64_n
        size_t = uint64_t
    elif ("armv5t" in arch_res) or ("arm)" in arch_res):
        ARCH="arm32"
        ARCH_SIZE=4
        size_n = uint32_n
        size_t = uint32_t
    else:
        print("unknown architecture res: {}".format(arch_res))
        return False

    targ_addr = "{}".format(args.ENTRY)
    if args.justexec == True:
        software_bp_control(targ_addr)
    else:
        delim_entrypoint(targ_addr)

class sfcc (gdb.Command):
    """software finish control command"""
    def __init__(self):
        super(sfcc, self).__init__("sfcc", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        invoke_software_finish_control(arg, from_tty)

sfcc()