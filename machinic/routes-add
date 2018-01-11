#!/usr/bin/python3
### This is a generated file ###
import argparse
import routeling
import sys
import os
def main(argv):
    """
    Add route
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    #parser.add_argument("route", help="",required=False )
    parser.add_argument("--route", required=False,help="string of route enclosed in double quotes")
    parser.add_argument("-f","--file", required=False,help="file of routes 1 per line")

    args = parser.parse_args()

    if args.file:
        if os.path.isfile(args.file):
            with open(args.file,'r') as f:
                for line in f.readlines():
                    try:
                        routeling.add_route(line)
                    except Exception as ex:
                        print(ex)
    elif args.route:
        try:
            routeling.add_route(args.route)
        except Exception as ex:
            print(ex)

if __name__ == "__main__":
    main(sys.argv)
