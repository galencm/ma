import pytest
import subprocess
import os
import shutil
import glob

# Consul and nomad need to be running 
# for start and stop tests
# config file and sudo are needed for eval with nomad
#
# cp ./machinic/env/nomad_config.hcl /tmp
# $ consul agent -dev
# $ sudo /usr/local/bin/nomad agent -server -dev -config=nomad_config.hcl 

@pytest.fixture(scope='session')
def machine_directory():
    name = "test"
    destination = "/tmp/{}".format(name)

    try:
        shutil.rmtree(destination)
    except FileNotFoundError:
        pass

    yaml = os.path.join(destination,"{}.yaml".format(name))
    try:
        subprocess.call(["./../mchgen/mchgen.sh",name,destination],cwd="../mchgen/")
        subprocess.call(["./../codegen/codegen.sh",
                            os.path.join(destination,"machine.xml"),
                            name,
                            destination
                            ],cwd="../codegen/")
        subprocess.call(["python3",
                            "machine.py",
                            "generate",
                            "--name",
                            name, 
                            "--file",
                            yaml
                          ])
    except:
        subprocess.call(["./mchgen.sh",name,destination],cwd="./mchgen/")
        subprocess.call(["./codegen.sh",
                            os.path.join(destination,"machine.xml"),
                            name,
                            destination
                            ],cwd="./codegen/")
        subprocess.call(["python3",
                            "machine.py",
                            "generate",
                            "--name",
                            name, 
                            "--file",
                            yaml
                          ],cwd="./machinic/")
    yield destination
    try:
        shutil.rmtree(destination)
    except FileNotFoundError:
        pass

def test_machine_script_generation(machine_directory):
    assert os.path.isdir(machine_directory)
    created_scripts = glob.glob(os.path.join(machine_directory,"*.sh"))
    assert os.path.join(machine_directory,"start.sh") in created_scripts
    assert os.path.join(machine_directory,"stop.sh") in created_scripts

def test_machine_start(machine_directory):
    start_script = os.path.join(machine_directory,"start.sh")

    #with pytest.raises(Exception):
    subprocess.check_output([start_script],shell=True)

    assert os.path.isfile(os.path.expanduser("~/.local/jobs/{}.hcl".format("helloworlds")))
    assert os.path.isfile(os.path.expanduser("~/.local/jobs/{}.json".format("helloworlds")))
    
    scheduled_jobs = subprocess.check_output(["python3","jobs.py","status"]).decode()
    for line in scheduled_jobs.split("\n"):
        if "helloworlds" in line:
            assert "running" in line
            assert "dead" not in line

def test_machine_stop(machine_directory):
    stop_script = os.path.join(machine_directory,"stop.sh")
    
    #with pytest.raises(Exception):
    subprocess.call([stop_script],shell=True)

    scheduled_jobs = subprocess.check_output(["python3","jobs.py","status"]).decode()
    for line in scheduled_jobs.split("\n"):
        if "helloworlds" in line:
            assert "dead (stopped)" in line
            assert "running" not in line
