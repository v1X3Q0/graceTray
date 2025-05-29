#!/usr/bin/env python

from lldb import SBTarget
# import commands
import optparse
import shlex

def isl(debugger, command, result, internal_dict):
    # print >>result, (commands.getoutput('/bin/ls %s' % command))
    comargs = command.split(' ')
    nametarg = comargs[0]
    inaddr = int(comargs[1], 0x10)
    # print(debugger.GetSelectedTarget().modules)
    target = debugger.GetSelectedTarget()
    resaddr = 0
    # module gets us to a file, such as vmware-vmx
    for i in target.modules:
        if i.platform_file.basename == nametarg:
            # resaddr = i.ResolveFileAddress(inaddr).__int__()
            # section gets us to a section, such as __TEXT
            for j in i.sections:
                if (inaddr >= j.GetFileAddress()) and (inaddr < (j.GetFileAddress() + j.size)):
                    resaddr = inaddr - j.GetFileAddress() + j.GetLoadAddress(target)
                    break
            break
    else:
        return False
    # line_out = "{} {} {}".format(hex(so_beg), hex(so_end), so_lib_cur)
    print(hex(resaddr))

# And the initialization code to add your commands
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f isl.isl isl')
    print('The "isl" python command has been installed and is ready for use.')
