#!/bin/bash
usage="Usage:\n ./ma [machine name] [machine directory] [machine xml]"

# usage example:
# ./ma image_machine image_machine ./image_machine/scanner.xml 
while getopts ':hs:' option; do
  case "$option" in
    h)  
        echo "ma generates files using:"
        echo "    codegen:     generate machine yaml and code for input devices"
        echo "    machine.py:  generate scheduler jobs from yaml and start/stop scripts"
        echo "    envgen:      generate environment directory and scripts"
        echo "and starts machine..."
        echo ""
        echo -e "$usage"
        exit
        ;;    
    esac

done
shift $((OPTIND - 1))

#require all arguments
if [ "$#" -ne 3 ]; then
    echo -e $usage 
    exit 0
fi

machine_name=$1
machine_path=$2
machine_xml=$3

# try to stop machine
./$machine_path/stop.sh

# generate yaml from machine xml
cd codegen
./codegen.sh $machine_xml $machine_name $machine_path
cd ..

# generate nomad files and start stop scripts from yaml
cd machinic
echo $machine_name $machine_path/machine.yaml
python3 machine.py run --name $machine_name --file $machine_path/$machine_name.yaml
cd ..

# generate environment files from environment xml 
cd envgen
./envgen $machine_path/environment.xml $machine_path
cd ..

# start machine
cd $machine_path
./start.sh