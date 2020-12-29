import sys
import argparse

parser = argparse.ArgumentParser(description='trace some stuff.')
parser.add_argument('-mb', '--modBegin', default=0, type=int,
                    help='module beginning')
parser.add_argument('-me', '--modEnd', default=0, type=int,
                    help='module ending')
parser.add_argument('-dst', '--destination', type=int, required=True,
                    help='destination instruction')
parser.add_argument('-nt', '--noTrace', action='store_true',
                    help='whether or not to record instructions')
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
    if sys.argv[0] == '':
        sys.argv.pop()
        sys.argv.append(__file__)
    for j in i:
        sys.argv.append(j)
    return i

def main(args):
    # gdb.execute("set logging redirect on")
    # gdb.execute("set logging overwrite on")
    # gdb.execute("set logging file gdbTrace.txt")
    # gdb.execute("set logging on")
    if args.noTrace != True:
        f = open("gdbTrace.txt", "w")
    while True:
        currentInst = gdb.parse_and_eval("$pc")
        if args.noTrace != True:
            f.write(hex(currentInst) + '\n')

        if currentInst == args.destination:
            break
        # elif (currentInst < args.modBegin) or (currentInst > args.modEnd):
        #     gdb.execute("finish")
        #     continue
        gdb.execute("si")
    # gdb.execute("set logging off")
    if args.noTrace != True:
        f.close()
    
if __name__ == "__main__":
    parseArgFile()
    print(sys.argv)
    args = parser.parse_args()

    print("performing script")
    main(args)
