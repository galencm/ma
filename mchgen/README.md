# Mchgen

Generate a machine outline. 

A newly created outline consists of:

| file              |                   |
|-------------------|-------------------|
|`machine.xml`      |    xml specification for machine |            
|`environment.xml`  |    xml for machine environment   | 
|`environment.sh`   |    entry to environment scripts usually in ./env |
|`LICENSE`          |    MPL 2.0, default |
|`AUTHORS`          |    authors file, empty |
|`README.md`        |    simple readme |
|`.gitignore`       |    ignores common generated files |
|`conftest.py`      |    basic self-testing configuration |
|`local_tools.py`   |    used by tests to discover machine services |
|`./tests/test_machine.py` |   basic self-tests using pytest |


## Usage:  

`./mchgen.sh [machine name] [output directory]`

## Example:

Get `ma`:
```
git clone https://github.com/galencm/ma
```

Create a new machine and initialize git:
```
cd ~/ma/mchgen
./mchgen.sh ~/machine_foo
cd ~/machine_foo
git init .
git add .
git commit -m "Problem: machine has no source control

Solution: use git"
```

(Re)generate environment:
```
cd ~/ma/envgen
./envgen.sh ~/machine_foo/environment.xml ~/machine_foo/
```

(Re)generate with codegen and machine.py:
```
cd ~/machine_foo
./regenerate.sh
```

Start machine:
```
cd ~/machine_foo
./start.sh
```

Run self-tests:
```
pytest -v
```

## Contributing
This project uses the C4 process 

[https://rfc.zeromq.org/spec:42/C4/](https://rfc.zeromq.org/spec:42/C4/
)

## License
Mozilla Public License, v. 2.0

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)
