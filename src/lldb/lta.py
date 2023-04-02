#!/usr/bin/env python

from lldb import SBTarget
# import commands
import optparse
import shlex

def lta(debugger, command, result, internal_dict):
    # print >>result, (commands.getoutput('/bin/ls %s' % command))
    comargs = command.split(' ')
    inaddr = int(comargs[0], 0x10)
    target = debugger.GetSelectedTarget()
    resaddr = 0
    resname = ""
    # module gets us to a file, such as vmware-vmx
    for i in target.modules:
        # resaddr = i.ResolveFileAddress(inaddr).__int__()
        # section gets us to a section, such as __TEXT
        for j in i.sections:
            if (inaddr >= j.GetLoadAddress(target)) and (inaddr < (j.GetLoadAddress(target) + j.size)):
                resaddr = inaddr - j.GetLoadAddress(target) + j.GetFileAddress()
                resname = "{}.{}".format(i.platform_file.basename, j.GetName())
                break
        if resaddr != 0:
            break
    else:
        return False
    # line_out = "{} {} {}".format(hex(so_beg), hex(so_end), so_lib_cur)
    print("from {} offset {}".format(resname, hex(resaddr)))

# And the initialization code to add your commands
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f lta.lta lta')
    print('The "lta" python command has been installed and is ready for use.')
