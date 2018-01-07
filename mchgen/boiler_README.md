# README

This is a generated file. Replace this with machine info 
or run `mchgen.sh` to regenerate.   

## Appendix 1: Machine Basics
1. [Before starting](#before)
    1. [Security Considerations]()
    2. [Installing]()
2. [Quickstart](#quickstart)
    1. [Single step with `ma`](#with_ma)
3. [Step-by-Step](#step_by_step)
    1. [Generate yaml](#gen_code)
    2. [Generate controls and job files](#gen_con)
    3. [Generate environment](#genev)
    4. [Start/Stop](#start_stop)
4. [Testing](#test)
5. [License](#license)

## <a name="before"></a> Before starting

### Security Considerations
Currently the way zerorpc is used to wrap python files exposes many python functions via zerorpc. It is recommended to use firewalld rules to drop all incoming connections outside of local network. 

see `./ma/README.md` and `./machinic/setup_firewall.sh`

Redis runs without authentication. There are some aliases in the config used by redis.hcl.

Mosquitto runs without authentication.

### Installing

* dl ma from github
* core machine must be running

## <a name="quickstart"></a> Quickstart
### <a name="with_ma"></a> Running `ma`
`./ma ./machine_foo/ ./machine_foo/machine.xml`

##  <a name="step_by_step"></a> Step by Step
### <a name="gen_code"></a> Generate machine YAML
`cd codegen/`
`./codegen.sh ../machine_foo/machine.xml`
`cp ./machine/machine.yaml ../machine_foo`

### <a name="gen_con"></a> Generate controls and job files:
`cd machinic/`
`python3 machine.py run --name foo --path ../machine_foo/machine.yaml`

### <a name="gen_env"></a>  Generate environment:
`cd envgen/`
`./envgen.sh ../machine_foo/machine.xml ../machine_foo/`

### <a name="start_stop"></a>  Start/stop machine:
`cd machine_foo/`
    `./start.sh`
    `./stop.sh`

## <a name="test"></a> Testing
`cd machinic/`
`python3 connector.py cli -s zerorpc-helloworlds `

at prompt (cmd) type 'hello' and press enter

##  <a name="license"></a> License
Mozilla Public License, v. 2.0 

http://mozilla.org/MPL/2.0/
