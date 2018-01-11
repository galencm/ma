#!/usr/bin/python3
### This is a generated file ###
import argparse
import pipeling
import sys
import os
def main(argv):
    """
    Add pipe
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    #parser.add_argument("pipe", help="",required=False )
    parser.add_argument("--pipe", required=False,help="string of pipe enclosed in double quotes")
    parser.add_argument("-f","--file", required=False,help="file of pipes 1 per line")

    args = parser.parse_args()

    if args.file:
        if os.path.isfile(args.file):
            with open(args.file,'r') as f:
                for line in f.readlines():
                    try:
                        pipeling.remove_pipe(line)
                    except Exception as ex:
                        print(ex)
    elif args.pipe:
        try:
            pipeling.remove_pipe(args.pipe)
        except Exception as ex:
            print(ex)

if __name__ == "__main__":
    main(sys.argv)
