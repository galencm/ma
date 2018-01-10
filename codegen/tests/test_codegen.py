import pytest
import subprocess
import os
import shutil
import textwrap
import ruamel.yaml
import pathlib

@pytest.fixture(scope='session')
def machine_yaml():
    #partial xml from machine_core
    machine_xml = textwrap.dedent("""
    <?xml version = "1.0"?>
    <machine description = "pytest machine">
        <alias name = "scanning_interface" alias = "scan_iface" value = "wlan2"/>
        <alias name = "accesspoint_interface" alias = "ap_iface" value = "wlan1"/>
        <alias name = "accesspoint_password" alias = "ap_pass" value = "f00_bar_baz"/>
        <alias name = "accesspoint_ssid" alias = "ap_ssid" value = "foo"/>
        <include file = "bridge.py" name = "bridge-watch" wireup="true">
            <argument value = "reactor" />
        </include>
        <include file = "tools.py" name = "tools" rpc = "true" wireup = "true" />
        <include file = "redis.hcl" wireup = "true" />
        <include file = "mqtt.hcl" wireup = "true" />
        <include file = "associative.py" wireup = "false"
          rpc = "false">
            <argument alias = "scan_iface" />
            <argument value = "--config" />
            <argument value = "default.yaml" />
            <argument value = "--ap-ssid" />
            <argument alias = "ap_ssid" />
            <argument value = "--ap-pass" />
            <argument alias = "ap_pass" />
        </include>
    </machine>
    """)

    name = "test"
    destination = "/tmp/{}".format(name)
    xml_file = os.path.join(destination,"machine.xml")
    yaml_file = os.path.join(destination,"{}.yaml".format(name))

    try:
        shutil.rmtree(destination)
    except FileNotFoundError:
        pass

    os.mkdir(destination)

    with open(xml_file,"w+") as f:
        f.write(machine_xml)
    # use try/except to allow pytest to be
    # called from inside codegen dir or from
    # ma dir
    try:
        subprocess.call(["./codegen.sh",xml_file,name,destination])
    except:
        subprocess.call(["./codegen.sh",xml_file,name,destination],cwd="./codegen/")

    yield yaml_file

    try:
        shutil.rmtree(destination)
    except FileNotFoundError:
        pass

def test_created_machine_yaml(machine_yaml):
    yaml=ruamel.yaml.YAML(typ='safe')
    contents = yaml.load(pathlib.Path(machine_yaml))
    assert 'includes' in contents.keys()
    assert isinstance(contents['includes'][0]['bridge.py'],dict)
    assert contents['includes'][0]['bridge.py']['auto-wireup'] is True
    assert contents['includes'][0]['bridge.py']['name'] == "bridge-watch"
    assert contents['includes'][0]['bridge.py']['args'] == ['reactor']
    assert isinstance(contents['includes'][1]['tools.py'],dict)
    assert contents['includes'][1]['tools.py']['auto-wireup'] is True
    assert contents['includes'][1]['tools.py']['as-rpc'] is True
    assert contents['routes'] == None
    # pipes are currently a block of text
    # that is parsed by pipeling
    assert contents['pipes'] == ['']
    assert contents['rules'] == None