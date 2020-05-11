import sys

modBegin = 0
modEnd = 0
destination = 0
#winload
#   modBegin = 0x4057B000
#   modEnd = 0x4068C8C8

def parseArgFile():
    f = open("args.txt", "r")
    g = f.readlines()
    f.close()
    h = g[0].replace('\n', '')
    i = h.split(' ')
    while len(sys.argv) != 1:
        sys.argv.pop()
    for j in i:
        sys.argv.append(j)
    return i

def main():
    # gdb.execute("set logging redirect on")
    # gdb.execute("set logging overwrite on")
    # gdb.execute("set logging file gdbTrace.txt")
    # gdb.execute("set logging on")
    f = open("gdbTrace.txt", "w")
    while True:
        currentInst = gdb.parse_and_eval("$pc")
        f.write(hex(currentInst) + '\n')
        if currentInst == destination:
            break
        elif (currentInst < modBegin) or (currentInst > modEnd):
            gdb.execute("finish")
            continue
        gdb.execute("si")
    # gdb.execute("set logging off")
    f.close()
    
if __name__ == "__main__":
    args = parseArgFile()
    if (len(sys.argv) != 4):
        print("usage modBegin modEnd destination")
    else:
        print("performing script with args:")
        print(sys.argv)
        modBegin = int(sys.argv[1], 16)
        modEnd = int(sys.argv[2], 16)
        destination = int(sys.argv[3], 16)        
        main()
