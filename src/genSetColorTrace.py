import argparse
import os
import time

def hex_int(x):
    return int(x, 16)

whiteColor = 0xffffffff
startColor = 0x00ffffff
endColor = 0x00000000

parser = argparse.ArgumentParser(description='create set color script for ida')
parser.add_argument('-fb', '--funcBegin', required=False, type=hex_int,
    help='start of target routine')
parser.add_argument('-fe', '--funcEnd', required=False, type=hex_int,
    help='End of target routine')
parser.add_argument('-df', '--disassemblerFormat', default="binja",
    help='disassembler format, ida or binja')
parser.add_argument('inputFile',
    help='input file with trace')
parser.add_argument('-sc', '--startColor', default=startColor, type=hex_int,
    help='start color to use, default 0x{}'.format(hex(startColor)[2:].zfill(8)))
parser.add_argument('-ec', '--endColor', default=endColor, type=hex_int,
    help='end color to use, default 0x{}'.format(hex(endColor)[2:].zfill(8)))
parser.add_argument('-rc', "--resetColor", required=False, action="store_true",
    help='reset color with input scheme')
parser.add_argument('-rb', '--rebase', type=hex_int, default=0,
    help='optionally rebase an input file, default=0, so no rebase')

hfName = "highlightFunc"

def curColorInc(k):
    k += 4
    return k

# MmFwGetMemoryMap
# funcStart = 0x405D0984
# funcEnd = 0x405D0FC8

def rmask(color):
    return (color & 0x00ff0000) >> 0x10

def gmask(color):
    return (color & 0x0000ff00) >> 0x08

def bmask(color):
    return (color & 0x000000ff) >> 0x00

def rumask(color):
    return (color & 0xff) << 0x10

def gumask(color):
    return (color & 0xff) << 0x08

def bumask(color):
    return (color & 0xff) << 0x00

resetCodeBlock = """
def reset_color(targAddr={}):
    highlightFunc = bv.get_functions_containing(targAddr)[0]
    for inst in highlightFunc.instructions:
        highlightFunc.set_auto_instr_highlight(inst[1], HighlightColor(alpha=0))
"""

def init_trace_py(inputFile):
    inputFileDir = os.path.dirname(inputFile)
    # remove directory path
    inputFile = os.path.basename(inputFile)
    # remove .txt
    inputFile = os.path.splitext(inputFile)[0]
    # remove .trace
    inputFile = os.path.splitext(inputFile)[0]

    # a date can be _20220318_221418515, length 19
    datesuffix = inputFile[-19:]
    fileprefix = inputFile[0:-19]

    # modTimesinceEpoc = os.path.getmtime(inputFile)
    # # Convert seconds since epoch to readable timestamp
    # modificationTime = time.strftime('%Y%m%d_%H%M%S', time.localtime(modTimesinceEpoc))

    fullNewPath = os.path.join(inputFileDir,
        "{}{}".format(inputFile, '.trace.py'))
    f = open(fullNewPath, 'w')
    print("outfile will be {}".format(fullNewPath))
    return f, inputFile


def main():
    global startColor
    global endColor

    args = parser.parse_args()    
    if args.inputFile[-4:] != '.txt':
        print('need a valid .txt file')
        return False
    if ((args.funcBegin == None) and (args.funcEnd != None)) or ((args.funcBegin != None) and (args.funcEnd == None)):
        print("need both boundaries of function defined")
        return False
    f = open(args.inputFile, 'r')
    g = f.readlines()
    f.close()
    rebase = args.rebase
    f, modunit = init_trace_py(args.inputFile)

    traceList = []
    for i in g:
        i = i.replace('\n', '')
        i = int(i, 16) - rebase
        if ((args.funcBegin != None) and (i >= args.funcBegin and i <= args.funcEnd)) or (args.funcBegin == None):
            if i not in traceList:
                traceList.append(i)

    if args.startColor != None:
        startColor = args.startColor
    if args.endColor != None:
        endColor = args.endColor

    # determine step for changing the color
    rstart = rmask(startColor)
    gstart = gmask(startColor)
    bstart = bmask(startColor)

    rend = rmask(endColor)
    gend = gmask(endColor)
    bend = bmask(endColor)

    rstep = (rstart - rend) * 1.0 / len(traceList)
    gstep = (gstart - gend) * 1.0 / len(traceList)
    bstep = (bstart - bend) * 1.0 / len(traceList)

    rcur = rstart * 1.0
    gcur = gstart * 1.0
    bcur = bstart * 1.0

    print("decrements are r:{}, g:{}, b:{}".format(rstep, gstep, bstep))

    target_identifier = "{}_{}".format(hex(traceList[0]), modunit)
    target_identifier = target_identifier.replace('-', '_')

    f.write("def set_{}():\n".format(target_identifier))
    if args.disassemblerFormat == "binja":
        f.write("\t{} = bv.get_functions_containing({})[0]\n".format(hfName, hex(traceList[0])))
    count = 0
    for i in traceList:
        # if count == len(traceList) - 1:
        #     curColor = 0
        
        if args.disassemblerFormat == "ida":
            f.write('\tset_color({}, CIC_ITEM, {})\n'.format(hex(i),
                hex(rumask(int(rcur)) + gumask(int(gcur)) + bumask(int(bcur)))))
        elif args.disassemblerFormat == "binja":
            f.write("\t{}.set_auto_instr_highlight({}, HighlightColor(red={}, green={}, blue={}))\n".format(
                hfName, hex(i), hex(int(rcur)), hex(int(gcur)), hex(int(bcur))))
        
        # colorIncrCount += colorIncr
        rcur -= rstep
        gcur -= gstep
        bcur -= bstep

        count += 1
    f.write("\n")
    
    if args.resetColor == True:
        f.write("def reset_{}():\n".format(target_identifier))
        if args.disassemblerFormat == "binja":
            f.write("\t{} = bv.get_functions_containing({})[0]\n".format(hfName, hex(traceList[0])))
        for i in traceList:
            if args.disassemblerFormat == "ida":
                f.write('\tset_color({}, CIC_ITEM, {})\n'.format(hex(i),
                    hex(rumask(int(rcur)) + gumask(int(gcur)) + bumask(int(bcur)))))
            elif args.disassemblerFormat == "binja":
                f.write("\t{}.set_auto_instr_highlight({}, HighlightColor(alpha=0))\n".format(
                    hfName, hex(i)))
        f.write("\n")
    else:
        f.write(resetCodeBlock.format(hex(traceList[0])))

    f.write("print(\"calling set_{}\")\n".format(target_identifier))
    f.write("set_{}()\n".format(target_identifier))
    f.close()

if __name__ == "__main__":
    main()
