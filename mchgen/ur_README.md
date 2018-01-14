# README

This is a generated file.

## Machinic basics

**get [`ma`](https://github.com/galencm/ma):**
```
git clone https://github.com/galencm/ma
```

**(Re)generate control scripts from yaml:**
```
cd ma/machinic
python3 machine.py generate --name machine --file ~/your_machine/machine.yaml
```

**Start/stop machine(core machine must be running):**
```
cd your_machine
./start.sh
./stop.sh
```

**Check machine status:**
```
cd ma/machinic
python3 machine.py status
python3 machine.py status-raw
```

**(Re)generate yaml and permutations from xml:**
```
cd ma/codegen
./codegen.sh ~/your_machine/machine.xml machine ~/your_machine/
```

**(Re)generate environment from xml:**
```
cd ma/envgen
./envgen.sh ~/your_machine/environment.xml ~/your_machine/
```

## Testing:

**Run tests:**
```
pytest -v
```

**Run tests with different yaml:**
```
pytest -v --yaml your_machine.yaml
```
## License
Mozilla Public License, v. 2.0 

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)
