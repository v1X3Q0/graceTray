from binaryninja import BinaryView, Function, PluginCommand, HighlightColor
from binaryninja.debugger import DebuggerController
from binaryninja.interaction import IntegerField, TextLineField, ChoiceField, get_form_input, SeparatorField, OpenFileNameField, show_plain_text_report, show_message_box
import time
import os
# from .src.binja import brute_gracetray
from datetime import datetime

DEFAULT_STARTCOLOR=0x0000ff00
DEFAULT_ENDCOLOR=0x00000000
DEFAULT_ENDADDR=-1
DEFAULT_TOTALCOUNT=0

def gracetray_binja(bv: BinaryView):
    BETA=True
    input_list=[]
    startColor = IntegerField(f'start color, default: {hex(DEFAULT_STARTCOLOR)[2:].zfill(8)}', default=DEFAULT_STARTCOLOR)
    input_list.append(startColor)
    endColor = IntegerField(f'end color, default: {hex(DEFAULT_ENDCOLOR)[2:].zfill(8)}', default=DEFAULT_ENDCOLOR)
    input_list.append(endColor)
    endAddr = IntegerField(f'end address, default: {DEFAULT_ENDADDR} which means til routine exit', default=DEFAULT_ENDADDR)
    input_list.append(endAddr)
    totalCount = IntegerField(f'BETA: total count to exec, default: {DEFAULT_TOTALCOUNT} which means infinite', default=DEFAULT_TOTALCOUNT)
    input_list.append(totalCount)
    temp_filename="yes"
    addrlist = OpenFileNameField('output address list, yes to auto-create, no not to, or your file', default=temp_filename)
    input_list.append(addrlist)
    get_form_input(input_list, "addrlist")
    if startColor == None:
        return False
    addrlistres = None
    if addrlist.result == "yes":
        addrlistres = "\"\""
    elif addrlist.result == "no":
        addrlistres = "None"
    else:
        addrlistres = f"\"{addrlist.result}\""

    if BETA == True:
        print("copy this to your console")
        bjpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src/binja.py")
        com1 = "exec(open(\"{}\").read())".format(bjpath)
        # print(com1)
        com2 = "brute_gracetray(bv, endAddr={}, startColor={}, endColor={}, fdeb={}, fname={})" \
        "".format(endAddr.result, hex(startColor.result), hex(endColor.result), "None", addrlistres)
        # print(com2)
        show_message_box("exec the following", "{}\n{}".format(com1, com2))
    # else:
    #     fdeb = DebuggerController(bv)
    #     brute_gracetray(bv, endAddr.result, startColor.result, endColor.result,
    #                     # totalCount.result, # BETA feature, not implemented yet
    #                     fdeb, addrlist.result)
    return

PluginCommand.register("graceTray", "execute til and highlight", gracetray_binja)
