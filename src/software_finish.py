ARCH=None
ARCH_SIZE=None
uint64_t = gdb.lookup_type('unsigned long long')
uint32_t = gdb.lookup_type('unsigned int')
uint16_t = gdb.lookup_type('unsigned short')
uint8_t = gdb.lookup_type('unsigned char')
size_t = None

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

