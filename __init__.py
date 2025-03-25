from binaryninja import BinaryView, Function, PluginCommand, HighlightColor
from binaryninja.debugger import DebuggerController
from binaryninja.interaction import IntegerField, TextLineField, ChoiceField, get_form_input, SeparatorField, OpenFileNameField
import time
import os
from .src.gdb.gdbTrace import init_trace_filename
import datetime

DEFAULT_STARTCOLOR=0x0000ff00
DEFAULT_ENDCOLOR=0x00000000
DEFAULT_ENDADDR=-1
DEFAULT_TOTALCOUNT=0

# COPY VARIANT
def brute_gracetray(bv: BinaryView, endAddr: int, startColor: int, endColor: int, fdeb=None, fname=None):
    RSHIFT_CONST = 0x10
    GSHIFT_CONST = 0x08
    BSHIFT_CONST = 0x00
    def init_trace_filename(bv, startAddr):
        fname = ""
        # detect if you have a symbol file, if so name will use its name
        fileabs = bv.file.original_filename
        fname = "{}_".format(os.path.basename(fileabs))
        tracename = "{}{}_{}.trace.txt".format(fname,
            hex(startAddr),
            datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3])
        return tracename
    def mask_step_cur(startcolor: int, endcolor: int, tracecount: int, shift_const: int):
        targ_mask = (0xff << shift_const)
        cstart = (startcolor & targ_mask) >> shift_const
        cend = (endcolor & targ_mask) >> shift_const
        cstep = (cstart - cend) * 1.0 / tracecount
        ccur = cstart * 1.0
        return cstep, ccur
    def get_instructions_count(bv: BinaryView, targfunc: Function):
        inst_count = 0
        for inst in targfunc.instructions:
            inst_count+=1
        return inst_count
    if fdeb == None:
        fdeb = binaryninja.debugger.DebuggerController(bv)
    if fname == '':
        fname = init_trace_filename(bv, fdeb.ip)
    insthighlight_list = []
    if fdeb.connected == False:
        print("target not connected to a session, come back later")
        return False
    targfunc = bv.get_functions_containing(fdeb.ip)[0]
    inst_count = get_instructions_count(bv, targfunc)
    funcend = targfunc.get_instruction_containing_address(targfunc.highest_address)
    while True:
        if fdeb.ip not in insthighlight_list:
            insthighlight_list.append(fdeb.ip)
        # condition 1 for exiting, we are in a different function
        if bv.get_functions_containing(fdeb.ip)[0] != targfunc:
            print("stepping exited our target frame")
            break
        # condition 2 for exiting, we have reached the end
        if fdeb.ip == endAddr:
            print("raeched target end address")
            break
        # condition 3 for exiting, we have reached the last instruction
        if fdeb.ip == funcend:
            print("raeched interpretted funend")
            break
        # if we passed those, we can continue
        # print("performing step", fdeb.ip)
        fdeb.step_over()
    rstep, rcur = mask_step_cur(startColor, endColor, len(insthighlight_list), RSHIFT_CONST)
    gstep, gcur = mask_step_cur(startColor, endColor, len(insthighlight_list), GSHIFT_CONST)
    bstep, bcur = mask_step_cur(startColor, endColor, len(insthighlight_list), BSHIFT_CONST)
    print("inst_count {} r {} {} g {} {} b {} {}".format(len(insthighlight_list), rstep, rcur, gstep, gcur, bstep, bcur))
    if fname != None:
        f = open(fname, 'wb')
        for i in insthighlight_list:
            f.write(f"{i}\n")
        f.close()
    for inst in insthighlight_list:
        targfunc.set_auto_instr_highlight(inst, HighlightColor(red=int(rcur), green=int(gcur), blue=int(bcur)))
        # colorIncrCount += colorIncr
        rcur -= rstep
        gcur -= gstep
        bcur -= bstep
    return
# brute_gracetray(bv, 0x40000, 0x0000ff00, 0x00000000)

def gracetray_binja(bv: BinaryView):
    input_list=[]
    startColor = IntegerField(f'start color, default: {hex(DEFAULT_STARTCOLOR)[2:].zfill(8)}', default=DEFAULT_STARTCOLOR)
    input_list.append(startColor)
    endColor = IntegerField(f'end color, default: {hex(DEFAULT_ENDCOLOR)[2:].zfill(8)}', default=DEFAULT_ENDCOLOR)
    input_list.append(endColor)
    endAddr = IntegerField(f'end address, default: {DEFAULT_ENDADDR} which means til routine exit', default=DEFAULT_ENDADDR)
    input_list.append(endAddr)
    totalCount = IntegerField(f'total count to exec, default: {DEFAULT_TOTALCOUNT} which means infinite', default=DEFAULT_TOTALCOUNT)
    input_list.append(totalCount)
    temp_filename = init_trace_filename()
    temp_filename = os.path.join(os.path.dirname(bv.file.filename), temp_filename)
    addrlist = OpenFileNameField('output address list', default=temp_filename)
    input_list.append(addrlist)
    get_form_input(input_list, "addrlist")
    if startColor == None:
        return False
    
    fdeb = DebuggerController(bv)
    brute_gracetray(bv, endAddr.result, startColor.result, endColor.result, totalCount.result, fdeb, addrlist.result)
    return

PluginCommand.register("graceTray", "execute til and highlight", gracetray_binja)
