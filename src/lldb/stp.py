from inspect import stack, trace
import sys
import argparse
from datetime import datetime
import os
import time

def hex_int(x):
    return int(x, 16)

debugger_g = None

def init_trace_filename():
    fname = ""
    # detect filename, if it exits then name the file after it
    target = debugger_g.GetSelectedTarget()
    if len(target.modules) > 0:
        fname = target.modules[0].platform_file.basename

    tracename = "{}{}_{}.trace.txt".format(fname,
        hex(target.GetProcess().selected_thread.frame[0].pc),
        datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3])

    return tracename
    # return "gdbTrace.txt"

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
    sys.argv.append("lldb-stools.py")
    # append the args that were parsed
    for i in args_each:
        sys.argv.append(i)
    return args_each

def software_tracepoint_init(arg):
    parser = argparse.ArgumentParser(description='trace some stuff.')
    parser.add_argument('-dst', '--destination', type=hex_int,
                        help='destination instruction')
    parser.add_argument('-fb', '--funcBegin', type=hex_int, required=True,
                        help='function beginning')
    parser.add_argument('-fe', '--funcEnd', type=hex_int, required=True,
                        help='function ending')
    # parser.add_argument('-nt', '--noTrace', action='store_true',
    #                     help='whether or not to record instructions')
    parseArg(arg)
    args = parser.parse_args()
    return args

def getsectioncontaining(target, module, inaddr):
    resaddr = 0
    for j in module.sections:
        if (inaddr >= j.GetLoadAddress(target)) and (inaddr < (j.GetLoadAddress(target) + j.size)):
            resaddr = inaddr - j.GetLoadAddress(target) + j.GetFileAddress()
            return j, resaddr
    return None

def getmsectioncontaining(target, inaddr):
    resaddr = 0
    for module in target.modules:
        for j in module.sections:
            if (inaddr >= j.GetLoadAddress(target)) and (inaddr < (j.GetLoadAddress(target) + j.size)):
                resaddr = inaddr - j.GetLoadAddress(target) + j.GetFileAddress()
                return j, resaddr
    return None

def stp(debugger, command, result, internal_dict):
    global debugger_g

    f = None
    filename = ""
    debugger_g = debugger
    args = software_tracepoint_init(command)
    target = debugger.GetSelectedTarget()
    thread = target.GetProcess().selected_thread
    rettrack = int(thread.frame[0].registers[0].GetChildMemberWithName('x30').value, 0x10)
    frame_index = thread.num_frames
    currentInst = thread.frame[0].pc
    nextInst = currentInst
    targsec, startaddr = getmsectioncontaining(target, currentInst)

    try:
        filename = init_trace_filename()
        f = open(filename, "w")
    except:
        print("couldn't open {}".format(filename))
        return -1

    while True:
        currentInst = thread.frame[0].pc
        # we have reached our return pointer, we can break
        if currentInst == rettrack:
            break

        # we have popped off the last frame, so we can break
        # if thread.num_frames < frame_index:
        #     break

        # eval branch taken
        # the old way to evaluate branch taken was to say that the link register has changed.
        # sometimes this works, and we can then just use it to determine we are in the same
        # frame. however arm64 that doesn't seem to work.
        # cur_rettrack = int(thread.frame[0].registers[0].GetChildMemberWithName('x30').value, 0x10)
        # if cur_rettrack != rettrack:
        if (currentInst < args.funcBegin) or (currentInst > args.funcEnd):
            # print("exited frame, returning {} != {}".format(hex(cur_rettrack), hex(rettrack)))
            thread.RunToAddress(nextInst)
            continue

        f.write(hex(currentInst - targsec.GetLoadAddress(target) + targsec.GetFileAddress()) + '\n')

        nextInst = currentInst + 4
        thread.StepInto()
    f.close()
    print("currentinst hit {}, completed".format(hex(currentInst)))

# And the initialization code to add your commands
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f stp.stp stp')
    print('The "stp" python command has been installed and is ready for use.')
