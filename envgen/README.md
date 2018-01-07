# Envgen

Generate collections of scripts(an environment) from XML to check for files(using `which`), system packages(using `bork`), python packages(using `bork`), etc. Items that are not found will be installed as specified in xml(for example: (0) not found (1) download (2) extract (3) 'make install') or using bork. 

* Uses [GSL](https://github.com/zeromq/gsl) to generate files from XML.

* Generated files use [Bork](https://github.com/mattly/bork) and bash.

### Usage:  

`./envgen.sh [xml] [dir]`

### Example:

`./envgen.sh ../machine_foo/environment.xml ../machine_foo/`

generates:

`../machine_foo/env/`

`../machine_foo/env/<files>`

(`env` directory is automatically appended to `[dir]` argument)

### Running environment scripts

`cd ../machine_foo`

`./environment.sh`

* `./machine_foo/environment.sh` always calls `./env/env_meta.sh` which handles OS-specific scripts and runs scripts using bork's `include`.  

* A script to be included based on os must have '`_os_`' in the filename, for example: `env_os_debian.bork`.


##  <a name="contribute"></a> Contributing
This project uses the C4 process 

https://rfc.zeromq.org/spec:42/C4/

##  <a name="license"></a> License
Mozilla Public License, v. 2.0

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)
