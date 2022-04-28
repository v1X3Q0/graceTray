
import argparse
import os
import time

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
IS_TRACING=False

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
    pc_save = get_ret_address()
    temp_finish = software_finishpoint("*{}".format(hex(pc_save)))
    temp_finish.silent = True
    gdb.execute("c")
    temp_finish.delete()

def invoke_software_finish(arg, from_tty):
    global ARCH
    global ARCH_SIZE
    global size_n
    global size_t
    global IS_TRACING

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

    software_finish()

class sfc (gdb.Command):
    """software finish command"""
    def __init__(self):
        super(sfc, self).__init__("sfc", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        invoke_software_finish(arg, from_tty)

sfc()