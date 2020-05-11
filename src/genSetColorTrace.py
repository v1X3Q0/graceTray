import argparse

parser = argparse.ArgumentParser(description='create set color script for ida')
parser.add_argument('-fs', dest='funcStart', help='start of target routine',
                        required=True)
parser.add_argument('-fe', dest='funcEnd', help='End of target routine',
                        required=True)
parser.add_argument('-if', dest='inputFile', help='input file with trace',
                        required=True)

whiteColor = 0xffffffff
startColor = 0xffffff
endColor = 0x00000000

def curColorInc(k):
    k += 4
    return k

# MmFwGetMemoryMap
# funcStart = 0x405D0984
# funcEnd = 0x405D0FC8

def main():
    args = parser.parse_args()    
    if args.inputFile[-4:] != '.txt':
        print('need a valid .txt file')
        return
    f = open(args.inputFile, 'r')
    g = f.readlines()
    f.close()
    f = open(args.inputFile[:-4] + '.trace.py', 'w')
    funcStart = int(args.funcStart, 16)
    funcEnd = int(args.funcEnd, 16)

    traceList = []
    curColor = startColor
    for i in g:
        i = i.replace('\n', '')
        i = int(i, 16)
        if i >= funcStart and i <= funcEnd:
            if i not in traceList:
                # curColor = curColorInc(curColor)
    # SetColor(currentEA, CIC_ITEM, 0xc7c7ff);
                traceList.append(i)
    colorIncr = (endColor - 0xff) * 1.0 / len(traceList) / 3
    colorIncrCount = colorIncr
    print (colorIncr)
    count = 0
    for i in traceList:
        curColor = startColor + (int(colorIncrCount) << ((count % 3) * 8))
        if count == len(traceList) - 1:
            curColor = 0
        f.write('SetColor(' + hex(i) +  ', CIC_ITEM, ' + hex(curColor) + ')\n')
        colorIncrCount += colorIncr
        count += 1

    f.close()

if __name__ == "__main__":
    main()