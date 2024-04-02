import argparse
import os
import time
import sys
import re
try:
    import gdb
except:
    print("int the wrong interpretter, import gdb failed")

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
libranges_map = {}
IS_TRACING=False

def getlibranges_map():
    global libranges_map
    return libranges_map

def getARCH():
    global ARCH
    return ARCH

def getARCH_SIZE():
    global ARCH_SIZE
    return ARCH_SIZE

def getsize_t():
    global size_t
    return size_t

def getsize_n():
    global size_n
    return size_n

# convert args in args.txt to sys.argv, expect 1 line in
def parseArg(args_line):
    args_each = []
    if args_line == '' or args_line == None:
        args_line = ''
    if args_line != '':
        args_each = args_line.split(' ')
    # clear the existing sys.argv
    while len(sys.argv) != 0:
        sys.argv.pop()
    sys.argv.append("gdb-stools.py")
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
    elif (ARCH == "arm32") or (ARCH == "aarch64"):
        cur_inst = int(gdb.parse_and_eval("$pc").cast(size_t))
        next_inst_addr = cur_inst + 4
    return next_inst_addr

def get_ret_address():
    if ARCH == "i386:x86-64":
        # print(hex(int(gdb.parse_and_eval("*(unsigned long long*)" + sp_temp).cast(gdb.lookup_type('unsigned long long')))))
        sp_temp = int(gdb.parse_and_eval("$sp").cast(size_t))
        ret_addr = int(gdb.parse_and_eval("*({}*){}".format(size_n, hex(sp_temp))).cast(size_t))
    elif (ARCH == "arm32") or (ARCH == "aarch64"):
        ret_addr = int(gdb.parse_and_eval("$lr").cast(size_t))
    return ret_addr

def eval_branch_taken():
    result = False
    sp_pre_step = int(gdb.parse_and_eval("$sp").cast(size_t))
    pc_pre_step = int(gdb.parse_and_eval("$pc").cast(size_t))
    lr_pre_step = get_ret_address()
    pc_post_step_pred = get_next_instruction()
    gdb.execute("si")
    sp_post_step = int(gdb.parse_and_eval("$sp").cast(size_t))
    pc_post_step = int(gdb.parse_and_eval("$pc").cast(size_t))
    lr_post_step = get_ret_address()
    # condition is that our stack has decremented and we have

    if (ARCH == "arm32") or (ARCH == "aarch64"):
        # condition one, by arm32 convention bl ADDR_IMM
        if (lr_pre_step != lr_post_step) and (pc_post_step != pc_post_step_pred) and (pc_post_step_pred == lr_post_step):
            result = True
        # condition 2, mov lr, pc; bx ADDR_IMM
        elif (pc_post_step != pc_post_step_pred) and (pc_post_step_pred == lr_post_step):
            result = True
    elif ARCH == "i386:x86-64":
        if (sp_pre_step > sp_post_step) and (pc_post_step != pc_post_step_pred) and (pc_post_step_pred == lr_post_step):
            result = True
    return result

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

def software_finish():
    pc_save = get_ret_address()
    temp_finish = software_finishpoint("*{}".format(hex(pc_save)))
    temp_finish.silent = True
    gdb.execute("c")
    temp_finish.delete()

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
    return libranges_map

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

def architecture_init():
    global ARCH
    global ARCH_SIZE
    global size_t
    global size_n
    global IS_TRACING

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
        size_n = "unsigned long long"
    elif ("armv5t" in arch_res) or ("arm)" in arch_res):
        ARCH="arm32"
        ARCH_SIZE=4
        size_t = uint32_t
        size_n = "unsigned int"
    elif 'aarch64' in arch_res:
        ARCH="aarch64"
        ARCH_SIZE=8
        size_t = uint64_t
        size_n = "unsigned long long"
    else:
        print("unknown architecture res: {}".format(arch_res))
        return False

