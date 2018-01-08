#!/bin/bash
usage="Usage:  $0 [xml] [name] [output path] [primitive directory]
        xml               path to xml file
        name              (default: 'machine') used to create output directory
        output path       directory to store generated files
        primitive source  (default: ./PRIMITIVES) directory containing gsl files

Use an xml file to    1) generate yaml file for machine and 
                      2) generate isonomic permutations(cli,gui,iot,etc...)

Generated files are stored in created directory structure.
For example:
    ./codegen.sh ~/foo.xml machine_foo ~/machine_foo
produces the output:
                      ~/machine_foo/
                      ~/machine_foo/machine.yaml
                      ~/machine_foo/generated/<files>
"
# show usage if run without arguments
: ${1?"$usage"}
#if run without second argument use 'machine'
#as default
machine_xml=$1
name=${2:-machine}
machine_path=${3:-./machine}
primitive_source=${4:-./PRIMITIVES}

while getopts ':hs:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    esac
done
shift $((OPTIND - 1))


gsl -a -script:machine_yaml.gsl $machine_xml $name $machine_path

# machine_path trailing slash is important!
gsl -a -script:permutate.gsl $machine_xml $machine_path/generated/ $primitive_source
# check generated yaml
#python3 check_yaml.py $machine_path/$name.yaml
