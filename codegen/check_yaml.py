#from ruamel.yaml import YAML
import ruamel.yaml
import pathlib
import sys
import argparse

def main(argv):
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="yaml file")
    parser.add_argument("-v","--verbose", action='store_true', help="show parsed contents")

    args = parser.parse_args()
    f = pathlib.Path(args.file)
    yaml=ruamel.yaml.YAML(typ='safe')
    try:
        contents = yaml.load(f)
        if args.verbose:
            print(ruamel.yaml.dump(contents, Dumper= ruamel.yaml.RoundTripDumper), end='')
            print()
            print(contents)
        else:
            print("yaml valid!")
        sys.exit(0)
    except Exception as ex:
        print("yaml invalid!")
        print(ex)
        contents = None
        #with open(f.resolve(),'r') as file:
        contents = f.read_text()
        contents = contents.split("\n")
        for line_num,line in enumerate(contents):
            print("{:<4} {}".format(line_num,line))
        sys.exit(1)

if __name__ == '__main__':
    main(sys.argv)
