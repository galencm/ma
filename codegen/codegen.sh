#!/bin/bash
usage="Usage:  $0 [xml] [name]
        xml     path to xml file
        name    (default: 'machine') used to create output directory

Use an xml file to    1) generate yaml file for machine and 
                      2) generate isonomic permutations(cli,gui,iot,etc...)

Generated files are stored in created directory structure.
For example:
    ./codegen.sh foo.xml
produces the output:
                      ./machine/
                      ./machine/machine.yaml
                      ./machine/generated/<files>
"
# show usage if run without arguments
: ${1?"$usage"}
#if run without second argument use 'machine'
#as default
name=${2:-machine}
primitive_source=${3:-./PRIMITIVES}

while getopts ':hs:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    esac
done
shift $((OPTIND - 1))

#$1 xml file
#$2  output name
gsl -a -script:machine_yaml.gsl $1 $name 
#$1 xml file
#$2 output directory in form of ./foo/ with trailing /
#$3 location of gsl files to use as templates
gsl -a -script:permutate.gsl $1 ./$name/generated/ $primitive_source
#check generated yaml
python3 check_yaml.py ./$name/$name.yaml
