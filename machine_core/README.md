# README

## Overview

The core machine provides necessary **routing**, **interconnectivity** and **state** functionality. 

* Routing:
    * Mosquitto pubsub (bridged to redis for routing)
    * Redis pubsub
    * Routling dsl for message parsing and flexible routing
    * Pipeling dsl for dataflows 
* Wireless Interconnectivity:
    * Access point created with host-ap
    * Identify and configure wireless devices based on framework(s)(using Homie)
* State:
    * Redis 

## <a name="quickstart"></a> Quickstart
**Consul & nomad must be running**

**Check firewall rules**

<a name="quickstart"></a> 
`./ma ./machine_core/ ./machine_core/machine.xml`

## <a name="test"></a> Testing

`cd ./machine_core/examples`

`python3 routing_example.py`

##  <a name="contribute"></a> Contributing

This project uses the C4 process 

[https://rfc.zeromq.org/spec:42/C4/](https://rfc.zeromq.org/spec:42/C4/)

##  <a name="license"></a> License
Mozilla Public License, v. 2.0 

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)


