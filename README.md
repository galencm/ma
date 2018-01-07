# Ma

_projectional systems fabricated_

1. [Overview](#overview)
    1. [Security Considerations](#security)
2. [Quickstart](#quickstart)
    1. [Start Consul and Nomad](#start_substrate)
    2. [Start core machine](#start_core_machine)
    3. [Generate and start machine](#generate_machine)
    4. [Check machine status](#check_machine)
    5. [Notes](#notes)
3. [Contributing](#contribute)
4. [License](#license)

##<a name="overview"></a> Overview

* Encounter a process or problem that involves a mixture of concerns, digital and otherwise.

* Sketch a diagram of a potential solution. Generate a working prototype of the diagram. Add or remove elements, iterate, regenerate. Generate components as software or hardware, glom, rearrange, adjust, regenerate. 

* Imagine a system as higher dimensional form(s) to be projected into code, logic, interconnections and materials. 

* Currently: code generation, ad-hoc semantics, message brokers, permutating primitives, esp8266, wifi, glomming things. Much to improve and discover... 

* The future? computational fabrication, self-assembly, streetwise dsls, meshes, zyre, 3d printed circuits, stranger toolchains, more routes, less friction. That's the vision at least... 


###<a name="security"></a> Security Considerations 
**Current assumption is that firewall rules are running to block all incoming connections outside of local network** 

(To setup firewall rules, see [notes](#notes))

####Potential Issues

#####Machinic:
* `Connector.py` uses zerorpc to wrap a module in a broad way that exposes many more python functions than necessary or safe(warned against by zerorpc devs)
* Cmd2 console into zerorpc-wrapped modules

#####Core Machine:
* Redis runs without authentication
    * Some redis commands have been aliased in default  config (see redis.hcl)
* Mosquitto runs without authentication
* `associative.py` sends json to any ap matched by pattern

#####All machines:
* `environment.sh` requires sudo to download and install missing files (scripts are generated from environment.xml)

* others?



##<a name="quickstart"></a> Quickstart

**Firewall rules:**

See [notes](#notes) or run `./machinic/setup_firewall.sh` to add rules

###<a name="start_substrate"></a> Start Consul and Nomad 

Consul(service discovery) and nomad(scheduler) must be running before any machines.  

Two approaches: 

persistent: Install as services to start immediately and automatically start with os.

non-persistent: run in terminals using Ctrl-C to quit. Will have to be manually started as needed. 

* **Persistent**: Install consul/nomad as services(will prompt for sudo) 
    
    `./machinic/setup.services.sh`

* **Non-Persistent**: Start consul/nomad from terminals. Using two terminals:
    
    _( in terminal 1)_

    `consul agent -dev`

    _( in terminal 2: data_dir is used to increase disk space available to nomad in -dev mode)_

    `echo data_dir  = "\"/home/$USER/.config/nomad_data"\" > /home/$USER/.local/nomad_disk.conf`

    `sudo -E env "PATH=$PATH" nomad agent -server -dev -config=/home/$USER/.config/nomad_disk.conf`

    _(or single line for one terminal)_

    `consul agent -dev & ; echo data_dir  = "\"/home/$USER/.config/nomad_data"\" > /home/$USER/.local/nomad_disk.conf ; sudo -E env "PATH=$PATH" nomad agent -server -dev -config=/home/$USER/.config/nomad_disk.conf`

    **if running nomad without sudo:**
    see [notes](#notes)

###<a name="start_core_machine"></a> Start core machine:

`./ma machine_core machine_core ./machine_core/machine.xml`

###<a name="generate_machine"></a>  Generate and start a machine:
`cd mchgen`

`./mchgen.sh foo`

`cd ../`

`./ma machine_foo machine_foo ./machine_foo/machine.xml`

###<a name="check_machine"></a>  Check process/machine status:

`nomad status`

`python3 ./machinic/jobs.py status-raw`

`python3 connector.py cli -s zerorpc-helloworlds`

At `(Cmd)` prompt type `hello` and press return

###<a name="notes"></a> Notes

#### nomad without sudo,redis & machine_core

By default the machine_core nomad job for redis is configured to store db in /var/lib/redis, if running nomad without sudo or changing permissions to directory, redis will be unable to write to directory. The config file at ./machine_core/redis.hcl can be modified to store the redis db in the user directory(since config file remains in directory, have to avoid commiting changes):

* uncomment line and replace "<user\>" with username:

    `#dir /home/<user>/db\n` 
    becomes
    `dir /home/your-username/db\n`

* and comment line:

    `dir /var/lib/redis\n` 
    becomes
    `#dir /var/lib/redis\n`

#### firewall rules

_ Drop all incoming rule may need to change or be modified for consul gossip and zyre protocols..._

Install on debian-based systems(pi):

`sudo apt-get install firewalld`

Install on fedora:

`sudo dnf install firewalld`

`sudo firewall-cmd --permanent --set-default-zone=drop`

Set interface to network interface

`sudo firewall-cmd --permanent --zone=drop --change-interface=<interface>`

To add rule:

`sudo firewall-cmd --zone=drop  --add-rich-rule='rule family="ipv4" source address="192.168.0.0/24" accept'`

To remove rule:

`sudo firewall-cmd --zone=drop  --remove-rich-rule='rule family="ipv4" source address="192.168.0.0/24" accept'`


Pi-specific:

If using a raspberry pi it is useful to change the default password. Fail2ban may be useful as well:

`sudo apt-get fail2ban`

`sudo dnf install fail2ban`


#### Troubleshooting
* `redis-cli -p <port> -h <hostname>` (use jobs.py status-raw to quickly get port/ip)
* `nomad status <job_name>`
* `nomad logs <job_name id>`
* `nomad logs -stderr <job_name id>`
* `python3 connector.py cli -s zerorpc-<name>` (if process name begins with 'zerorpc-')
* `mosquitto_pub -p <port> -h <hostname> -t "foo" -m "bar"` ('mqtt' in machine_core)
* `mosquitto_sub -p <port> -h <hostname> -t '#'`


##  <a name="contribute"></a> Contributing
This project uses the C4 process 

https://rfc.zeromq.org/spec:42/C4/

##  <a name="license"></a> License
Mozilla Public License, v. 2.0

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)

