#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

usage="Usage:  $0 [name]
        name    (default: 'machine')  machine name

Use a name to    1) generate machine outline

A prefix of machine_ will be added to machine name to create output directory.
Output directory will be created ../ 
    ./mchgen.sh foo
produces the output:
                      ../machine_foo
                      ../machine_foo/<files>

Currently a newly created outline consists of:
    machine.xml        xml specification for machine(pass to codegen.sh or ma)
    environment.xml    xml for machine environment(pass to envgen)
    environment.sh     entry to environment scripts usually in ./env
    helloworlds.py     simple example to test or remove
    LICENSE            MPL 2.0, default
    AUTHORS            authors file, empty
    README.md          simple readme
    .gitignore         ignores:
                           start.sh
                           stop.sh
                           restart.sh
                           .jobs/
                           __pycache__
"
# show usage if run without arguments
: ${1?"$usage"}
#if run without name argument use 'machine'
#as default
name=${1:-machine}

while getopts ':hs:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    esac
done
shift $((OPTIND - 1))

machine_dir="machine_${name}"
mkdir ../$machine_dir
cp environment.xml ../$machine_dir
cp environment.sh ../$machine_dir
cp helloworlds.py  ../$machine_dir
cp machine.xml     ../$machine_dir
cp .gitignore      ../$machine_dir
cp boiler_README.md       ../$machine_dir/README.md 
cp LICENSE         ../$machine_dir
#create empty AUTHORS file
touch ../$machine_dir/AUTHORS   ../$machine_dir
#replace paths from generic to machine name
sed -i -e "s/machine_foo/$machine_dir/g" ../$machine_dir/README.md