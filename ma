#!/bin/bash
#$1 machine name
#$2 machine directory
#$3 machine xml
#./ma [machine name] [machine directory] [machine xml]

#example:
#./ma image_machine image_machine ./image_machine/scanner.xml 

./$2/stop.sh
cp $3 ./codegen/
filename=$(basename "$3")
echo $filename
#run in codegen dir
cd codegen
./codegen.sh $filename $1
echo "copying ./$1/$1.yaml to ../$2/machine.yaml"
echo $(pwd)
cp ./$1/$1.yaml ../$2/machine.yaml
cd ..
cd ./machinic
#machine logger output is not being displayed?
python3 machine.py run --name $1 --path ../$2/machine.yaml
cd ..
#generate env 
cd ./envgen
./envgen ../$2/environment.xml ../$2
cd ..

cd $2
#copy to other machines here to
#mimic directory structure...    
./start.sh
