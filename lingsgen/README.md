# Lingsgen

## Overview

Generate ling(s):

* Use an xml model to define a ling(domain specific language with some standardizations for machinic ecosystem). Uses `gsl` and scripts to generate:
    * a python package structure
        * a textx .tx file
        * basic stub functions for:
            * commandline crud, 
            * parsing using textx
            * dsl to xml serialisation
        * basic cli tools: `*-add, *-get, *-run, *-remove, *-xml, ...` using package entry_points
        * generated tests
    * a python file that can be easily run as an rpc service to be included with machines

Basic ling structure is being developed in [`machinic-lings`](https://github.com/galencm/machinic-lings), see routeling and pipeling as prototyping models that will guide `lingsgen` structure.

The goal is to develop a robust and useful set of tools to serve as a reference, prototype new lings and modify / regenerate existing ones. 

## Contributing
This project uses the C4 process 

[https://rfc.zeromq.org/spec:42/C4/](https://rfc.zeromq.org/spec:42/C4/
)

## License
Mozilla Public License, v. 2.0

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)

