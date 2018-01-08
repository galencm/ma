#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

files=(./ENVS/*)
env_outputs=""
for item in ${files[@]}
do
  printf -v a "   %s\n" $item
  env_outputs+=$a
done


usage="Usage:  $0 [xml] [dir]
        xml     path to xml file
        dir     destination for generated /env
        
        -o      list output Sources
        -h      help

Use an xml file to    1) generate environment scripts for machine or project 

Generated files are stored in created directory structure.
For example:
    ./envgen.sh ~/machine_foo/environment.xml ~/machine_foo/
produces the output:
                       ~/machine_foo/env/
                       ~/machine_foo/env/<files>

                       ('/env/' directory is automatically appended)

Output Sources:
  ./ENVS/ contains GSL templates used to generate code.

  for example:
      env_debian.gsl creates env_os_debian.bork
      env_python.gsl creates env_python.bork

  environment.sh will pattern match and select os against 
  filenames containing _os_. All files without _os_ will be 
  included and run by environment.sh.
"
# show usage if run without arguments
: ${1?"$usage"}
#if run without second argument use './env/'
#as default

while getopts ':ohs:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    o) echo "$env_outputs"
       exit
       ;;       
    esac

done
shift $((OPTIND - 1))

: ${2?$(echo missing output directory)$(exit 1)}
outdir=$2

#append trailing / if needed...
case "$outdir" in
*/)
    ;;
*)
    outdir+="/"
    ;;
esac

#generated files will go into 'env' directory
outdir+="/env/"
echo $outdir

#$1 xml file
#$2 output directory
gsl -a -script:envgen.gsl $1 $outdir 

#make environment.sh executable so it
#can be called by user or other scripts
chmod +x $outdir/environment.sh 

#currently copying environment.sh into toplevel
#directory with mchgen.sh
