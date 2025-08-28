import os
import argparse

gracetray_mainpy = "gracetray_gdb.py"

def add_gracetray(homegdb: str, gracetraypath: str):
    if os.path.exists(homegdb):
        homegdb_raw = ""
        with open(homegdb, "r") as homegdb_file:
            homegdb_raw = homegdb_file.read()
        if gracetray_mainpy not in homegdb_raw:
            with open(homegdb, "a") as homegdb_file:
                homegdb_file.write("\nsource {}\n".format(os.path.join(gracetraypath, gracetray_mainpy)))
    return

def main(args):
    currentdir = os.path.abspath(os.path.curdir)
    gracetraypath = os.path.abspath(os.path.dirname(__file__))
    homedir = os.path.abspath(os.path.expanduser("~"))

    if args.local:
        homegdb = os.path.join(currentdir, ".gdbinit")
    else:
        homegdb = os.path.join(homedir, ".gdbinit")
    add_gracetray(homegdb, gracetraypath)
    return

if __name__ == "__main__":
    argparser = argparse.ArgumentParser("install_gracetray")
    argparser.add_argument("-f", "--force", action="store_true", help="force install, create gdbinit if none found")
    argparser.add_argument("-l", "--local", action="store_true", help="run on local gdbinit")
    args = argparser.parse_args()
    main(args)