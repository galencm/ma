#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

usage="Usage:  [name] [destination path/directory]

Example: 
    ./mchgen.sh foo ~/machine_foo

produces the output:
                      ~/machine_foo
                      ~/machine_foo/<files>
                      ~/machine_foo/tests/<files>

Currently a newly created outline consists of:
    machine.xml                xml specification for machine(pass to codegen.sh or ma)
    environment.xml            xml for machine environment(pass to envgen)
    environment.sh             entry to environment scripts usually in ./env
    LICENSE                    MPL 2.0, default
    AUTHORS                    authors file, empty
    README.md                  simple readme
    .gitignore                 ignores generated scripts and python cache files
    conftest.py                basic self-testing configuration
    local_tools.py             used by tests to discover machine services
    ./tests/test_machine.py    basic self-tests using pytest
"
# show usage if run without arguments
: ${1?"$usage"}

name=${1:-machine}
: ${2?$(echo missing output destination path)$(exit 1)}
machine_dir=$2
mkdir $machine_dir
mkdir $machine_dir/tests

while getopts ':hs:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    esac
done
shift $((OPTIND - 1))

cp environment.xml $machine_dir
cp environment.sh  $machine_dir
cp machine.xml     $machine_dir
cp .gitignore      $machine_dir
cp ur_README.md $machine_dir/README.md 
cp LICENSE         $machine_dir
# basic tests
cp local_tools.py $machine_dir
cp conftest.py $machine_dir
cp test_machine.py $machine_dir/tests

#create empty AUTHORS file
touch $machine_dir/AUTHORS 
echo
echo machine skeleton created in $machine_dir
echo run included tests using \'pytest -v\'
#replace paths from generic to machine name
#sed -i -e "s/machine_foo/$machine_dir/g" $machine_dir/README.md