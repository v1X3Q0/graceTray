#!/usr/bin/env python

from lldb import SBTarget
# import commands
import optparse
import shlex

def getsectioncontaining(target, module, inaddr):
    resaddr = 0
    for j in module.sections:
        if (inaddr >= j.GetLoadAddress(target)) and (inaddr < (j.GetLoadAddress(target) + j.size)):
            resaddr = inaddr - j.GetLoadAddress(target) + j.GetFileAddress()
            return j, resaddr
    return None


def sbt(debugger, command, result, internal_dict):
    # print >>result, (commands.getoutput('/bin/ls %s' % command))
    target = debugger.GetSelectedTarget()
    thread = target.GetProcess().selected_thread
    for i in thread.frame:
        if i == None:
            break
        cursec, fileaddr = getsectioncontaining(target, i.module, i.pc)
        out_str = "{} {}.{} {}::{}".format(hex(i.pc), i.module.platform_file.basename, cursec.GetName(), hex(fileaddr), i.symbol.name)
        print(out_str)
    # line_out = "{} {} {}".format(hex(so_beg), hex(so_end), so_lib_cur)

# And the initialization code to add your commands
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f sbt.sbt sbt')
    print('The "sbt" python command has been installed and is ready for use.')
