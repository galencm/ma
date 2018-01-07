# Machinic
Tools for preparing, running and interacting with *machines

1. [Overview](#overview)
2. [Contributing](#contribute)
3. [License](#license)

## <a name="overview"></a> Overview

Machinic consists of a collection of tools to prepare and run machines:

`connector.py` : Wrap a python file with zerorpc. Provide cli to running connector-wrapped processes.

`machine.py` : generate scripts from YAML to start/stop machines, add routes using `jobs.py` and *ling scripts

`jobs.py` : generate and submit hcl/json files for running process via nomad


## Examples:

Wrapping python file to access via zerorpc:

`connector.py server --service-file ../machine_core/tools.py`

console into wrapped file using zerorpc and cmd2:

`python3 connector.py cli -s zerorpc-tools`

generate machine files and state from YAML:

`python3 machine.py run --name core --path ../machine_core/machine.yaml `

submit jobs to scheduler(taken from a machine_core `start.sh`)

`python3 ${JOB_PATH}jobs.py run --name redis --tags machine core --existing-file redis.hcl`

`python3 ${JOB_PATH}jobs.py run --name zerorpc-tools --tags machine core --command $CORE_PATH"connector.py" --args "server --service-file ${MACHINE_PATH}tools.py"` 


scripts for:

* installed scheduler and service discovery as system services
* lings: routeling, pipeling, add/remove etc...

## Security Considerations

Currently the way zerorpc is used to wrap python files exposes many python functions via zerorpc(in a manner explicitly not recommended by zerorpc devs). 

Python file is imported as module, wrapped in an object and then passed to zerorpc, this allows the use of any python file, but imports all additional modules so python `os` functions may be easily available via zerorpc or cmd2 console for example. 

** Currently it is recommended to use firewalld rules to drop all(or by port) incoming connections outside of local network.** 

See more details in machine README

##  <a name="contribute"></a> Contributing
This project uses the C4 process 
https://rfc.zeromq.org/spec:42/C4/

##  <a name="license"></a> License
Mozilla Public License, v. 2.0 

http://mozilla.org/MPL/2.0/


