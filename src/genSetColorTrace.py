import argparse

def hex_int(x):
    return int(x, 16)

parser = argparse.ArgumentParser(description='create set color script for ida')
parser.add_argument('-fb', '--funcBegin', required=False, type=hex_int,
    help='start of target routine')
parser.add_argument('-fe', '--funcEnd', required=False, type=hex_int,
    help='End of target routine')
parser.add_argument('-df', '--disassemblerFormat', default="ida",
    help='disassembler format, ida or binja')
parser.add_argument('inputFile',
    help='input file with trace')
parser.add_argument('-sc', '--startColor', required=False, type=hex_int,
    help='start color to use')

whiteColor = 0xffffffff
startColor = 0x00ffffff
endColor = 0x00000000

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


def main():
    global startColor

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

    f = open(args.inputFile[:-4] + '.trace.py', 'w')

    traceList = []
    for i in g:
        i = i.replace('\n', '')
        i = int(i, 16)
        if ((args.funcBegin != None) and (i >= args.funcBegin and i <= args.funcEnd)) or (args.funcBegin == None):
            if i not in traceList:
                traceList.append(i)

    if args.startColor != None:
        startColor = args.startColor

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

    if args.disassemblerFormat == "binja":
        # f.write("{} = bv.get_function_at({})\n".format(hfName, hex(traceList[0])))
        f.write("{} = bv.get_functions_containing({})[0]\n".format(hfName, hex(traceList[0])))
    count = 0
    for i in traceList:
        # if count == len(traceList) - 1:
        #     curColor = 0
        
        if args.disassemblerFormat == "ida":
            f.write('set_color({}, CIC_ITEM, {})\n'.format(hex(i),
                hex(rumask(int(rcur)) + gumask(int(gstart)) + bumask(int(bstart)))))
        elif args.disassemblerFormat == "binja":
            f.write("{}.set_auto_instr_highlight({}, HighlightColor(red={}, green={}, blue={}))\n".format(
                hfName, hex(i), hex(int(rcur)), hex(int(gcur)), hex(int(bcur))))
        
        # colorIncrCount += colorIncr
        rcur -= rstep
        gcur -= gstep
        bcur -= bstep

        count += 1

    f.close()

if __name__ == "__main__":
    main()
