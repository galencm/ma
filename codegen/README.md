# Codegen

Generate a variety of files from a machine XML file(using [GSL](https://github.com/zeromq/gsl)) to provide similar functionality across different categories, frameworks and languages. It could be described as **projecting** the machine structure into different forms(code,structure,materials,etc) or generating various **permutations** from primitives (from button xml: gui button(s) and hardware button(s)). 

So the xml stanza in a generic `machine.xml`: 

    <peripheral type="button" alternative_press="a">
        <output type="integer" value="1" destination="/foo"/>
    </peripheral>`

generates:

* `button-term-curt-1.py`   a terminal cli using [curtsies](https://github.com/thomasballinger/curtsies)
* `button-gui-kv-1.py`      a gui using [kivy](https://github.com/kivy/kivy)
* `button-iot-hmi-1.cpp`    iot code using [homie](https://github.com/marvinroger/homie)

### Usage:
`./codegen.sh [xml] [name]`

        `xml     path to xml file`

        `name    (default: 'machine') used to create output directory`

### Example:

    ./codegen.sh foo.xml

produces:

                      ./machine/

                      ./machine/machine.yaml

                      ./machine/generated/<generated files>

### Semantics

#### XML

_Evolving_. See documentation in xml.

#### Generation sources

`./codegen.sh` looks in `./PRIMITIVES/`

##### Naming structure

button-virt-gui-kv.py.gsl

    button      -    virt   -  gui    -    kv     -     py     -     gsl
    <peripheral><substrate><rough type><framework><output language><gsl format>

###### peripheral:

_All sorts of things, TODO: find better term since one can easily design more autonomous iterations_

* button(s)
* sensor(s)
* ...

###### substrate: 

_Substate/framework may involve hooks for toolchains, for example scripts to easily/immediately load generated code onto a chip or 3d print an object_

* virt: virtual(gui,cli)
* wifi: wireless stack(esp8266 chips, software such as homie or zyre)
* ...

potential:

* ble: bluetooth low energy(arduino, zyre) ?
* bscwifi: backscatter wireless (3d printed components) ?
* ...

###### rough (conceptual) type:

_organizational, and potentially for composing primitives in future_

* gui
* terminal
* iot
* ...

###### framework:

_frameworks may need to generate environments to fulfill dependencies_

* kv: kivy
* curt: curtsies
* hmi: homie
* ...

##  <a name="contribute"></a> Contributing
This project uses the C4 process 

[https://rfc.zeromq.org/spec:42/C4/](https://rfc.zeromq.org/spec:42/C4/)

##  <a name="license"></a> License
Mozilla Public License, v. 2.0

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)
