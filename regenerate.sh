
        #!/bin/bash
        #set machine dir ie .
        machine_dir=$(pwd)

        echo "running envgen..."
        cd ~/ma/envgen
        ./envgen.sh $machine_dir/environment.xml $machine_dir
    