# COPY VARIANT
def brute_gracetray(bv: BinaryView, endAddr: int, startColor: int, endColor: int, fdeb=None, fname=None):
    RSHIFT_CONST = 0x10
    GSHIFT_CONST = 0x08
    BSHIFT_CONST = 0x00
    def init_trace_filename(bv, startAddr):
        fname = ""
        # detect if you have a symbol file, if so name will use its name
        fileabs = bv.file.original_filename
        fname = "{}_".format(os.path.dirname(fileabs))
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
    TARGFUNC_PREFIX = "targfunc.set_auto_instr_highlight("
    if fname != None:
        if os.path.exists(fname) and os.path.isfile(fname):
            f = open(fname, "r")
            g = f.readlines()
            f.close()
            for lineindex in range(1, len(g)):
                line = g[lineindex]
                line = line[len(TARGFUNC_PREFIX):]
                addrstr = line.split(',')[0]
                instaddr = int(addrstr, 0x10)
                if instaddr not in insthighlight_list:
                    insthighlight_list.append(fdeb.ip)
            f = open(fname, "a")
        else:
            f = open(fname, 'w')
            f.write("targfunc = bv.get_functions_containing({})[0]\n".format(hex(fdeb.ip)))
    inst_total = get_instructions_count(bv, targfunc)
    inst_counter=0
    funcend = targfunc.get_instruction_containing_address(targfunc.highest_address)
    while True:
        # small except condtion, if pc actually was 0
        if fdeb.ip != 0:
            oldip = fdeb.ip
        if (inst_counter % 100) == 0:
            print(f"step over number: {inst_counter}")
        try:
            if fdeb.ip not in insthighlight_list:
                insthighlight_list.append(fdeb.ip)
            # condition 1 for exiting, we are in a different function
            if bv.get_functions_containing(fdeb.ip)[0] != targfunc:
                print("stepping exited our target frame")
                break
            # condition 2 for exiting, we have reached the end
            if fdeb.ip == endAddr:
                print("reached target end address")
                break
            # condition 3 for exiting, we have reached the last instruction
            if fdeb.ip == funcend:
                print("reached interpretted funend")
                break
            # if we passed those, we can continue
            # print("performing step", fdeb.ip)
            fdeb.step_over_and_wait()
            inst_counter += 1
        except:
            excptstr = "excption has occured, oldip: {}".format(hex(oldip))
            print(excptstr)
            break
            # raise Exception(excptstr)
    rstep, rcur = mask_step_cur(startColor, endColor, len(insthighlight_list), RSHIFT_CONST)
    gstep, gcur = mask_step_cur(startColor, endColor, len(insthighlight_list), GSHIFT_CONST)
    bstep, bcur = mask_step_cur(startColor, endColor, len(insthighlight_list), BSHIFT_CONST)
    print("inst_count {} r {} {} g {} {} b {} {}".format(len(insthighlight_list), rstep, rcur, gstep, gcur, bstep, bcur))
    for inst in insthighlight_list:
        targfunc.set_auto_instr_highlight(inst, HighlightColor(red=int(rcur), green=int(gcur), blue=int(bcur)))
        if fname != None:
            f.write("{}{}, HighlightColor(red=int({}), green=int({}), blue=int({})))\n".format(TARGFUNC_PREFIX, hex(inst), rcur, gcur, bcur))
        # colorIncrCount += colorIncr
        rcur -= rstep
        gcur -= gstep
        bcur -= bstep
    if fname != None:
        print("wrote colors to file {}".format(fname))
        f.close()
    return
# brute_gracetray(bv, 0x40000, 0x0000ff00, 0x00000000)
