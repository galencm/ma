# Mchgen

Generate a machine outline with files and directory structure. Defaults with a simple hello world accessible via rpc.

A newly created outline consists of:

| file              |                   |
|-------------------|-------------------|
|`machine.xml`      |    xml specification for machine |            
|`environment.xml`  |    xml for machine environment   | 
|`environment.sh`   |    entry to environment scripts usually in ./env |
|`helloworlds.py`   |    simple example to test or remove |
|`LICENSE`          |    MPL 2.0, default |
|`AUTHORS`          |    authors file, empty |
|`README.md`        |    simple readme |
|`gitignore`        |    ignores common generated files |


### Usage:  

`./mchgen.sh [machine name]`

### Example:

`./mchgen.sh foo`

produces:

    `../machine_foo`

    `../machine_foo/<files>`

### Running the Example

`./ma.sh machine_foo machine_foo ./machine_foo/machine.xml`

##  <a name="contribute"></a> Contributing
This project uses the C4 process 

https://rfc.zeromq.org/spec:42/C4/

##  <a name="license"></a> License
Mozilla Public License, v. 2.0

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)
